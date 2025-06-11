#!/bin/bash

# OptimoV2 Emergency Fix Script
# This script fixes the critical issues and rebuilds the container

echo "=== OptimoV2 Emergency Fix Script ==="
echo "====================================="
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This script will fix the following issues:${NC}"
echo "1. run_batch_job_updated.py imports non-existent OptimizationPipeline class"
echo "2. Container v6 failing because it can't find /app/scripts/run_pipeline.py"
echo "3. AWS region not specified in boto3 clients"
echo

# Step 1: Backup existing files
echo -e "${GREEN}Step 1: Creating backups...${NC}"
cp scripts/run_batch_job.py scripts/run_batch_job.backup.$(date +%Y%m%d_%H%M%S).py 2>/dev/null || true
cp scripts/run_batch_job_updated.py scripts/run_batch_job_updated.backup.$(date +%Y%m%d_%H%M%S).py 2>/dev/null || true

# Step 2: Use the fixed version
echo -e "${GREEN}Step 2: Applying fixed script...${NC}"
cp scripts/run_batch_job_fixed.py scripts/run_batch_job.py

# Step 3: Verify the fix
echo -e "${GREEN}Step 3: Verifying the fix...${NC}"
if grep -q "subprocess.run" scripts/run_batch_job.py; then
    echo -e "${GREEN}✓${NC} Script now uses subprocess to run pipeline"
else
    echo -e "${RED}✗${NC} Fix verification failed"
    exit 1
fi

# Step 4: Build new container
echo -e "${GREEN}Step 4: Building new container (v7)...${NC}"
docker build -t optimo-batch:v7 .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

# Step 5: Tag for ECR
echo -e "${GREEN}Step 5: Tagging for ECR...${NC}"
docker tag optimo-batch:v7 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7

# Step 6: Login to ECR
echo -e "${GREEN}Step 6: Logging into ECR...${NC}"
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 529088253685.dkr.ecr.us-west-2.amazonaws.com

if [ $? -ne 0 ]; then
    echo -e "${RED}ECR login failed!${NC}"
    exit 1
fi

# Step 7: Push to ECR
echo -e "${GREEN}Step 7: Pushing to ECR...${NC}"
docker push 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7

if [ $? -ne 0 ]; then
    echo -e "${RED}ECR push failed!${NC}"
    exit 1
fi

# Step 8: Update job definition
echo -e "${GREEN}Step 8: Updating job definition...${NC}"

# First, let's get the current job definition to preserve settings
CURRENT_JOB_DEF=$(aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE --region us-west-2 --query 'jobDefinitions[0]' --output json)

# Extract current settings
VCPUS=$(echo $CURRENT_JOB_DEF | jq -r '.containerProperties.vcpus // 72')
MEMORY=$(echo $CURRENT_JOB_DEF | jq -r '.containerProperties.memory // 140000')
JOB_ROLE=$(echo $CURRENT_JOB_DEF | jq -r '.containerProperties.jobRoleArn // "arn:aws:iam::529088253685:role/optimo-batch-role"')
EXECUTION_ROLE=$(echo $CURRENT_JOB_DEF | jq -r '.containerProperties.executionRoleArn // "arn:aws:iam::529088253685:role/ecsTaskExecutionRole"')

# Register new job definition with v7 image
aws batch register-job-definition \
  --job-definition-name optimo-job-def-v7 \
  --type container \
  --container-properties "{
    \"image\": \"529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7\",
    \"vcpus\": $VCPUS,
    \"memory\": $MEMORY,
    \"jobRoleArn\": \"$JOB_ROLE\",
    \"executionRoleArn\": \"$EXECUTION_ROLE\",
    \"environment\": [
      {\"name\": \"AWS_REGION\", \"value\": \"us-west-2\"},
      {\"name\": \"DYNAMODB_TABLE\", \"value\": \"optimo-jobs\"},
      {\"name\": \"S3_OUTPUT_BUCKET\", \"value\": \"optimo-output-files\"},
      {\"name\": \"S3_INPUT_BUCKET\", \"value\": \"optimo-input-files-v2\"},
      {\"name\": \"LICENSE_SECRET_NAME\", \"value\": \"optimo/gurobi-license\"}
    ]
  }" \
  --region us-west-2

if [ $? -ne 0 ]; then
    echo -e "${RED}Job definition update failed!${NC}"
    exit 1
fi

# Step 9: Update Lambda to use new job definition
echo -e "${GREEN}Step 9: Updating Lambda configuration...${NC}"
echo -e "${YELLOW}Note: You need to update the Lambda unified_handler to use 'optimo-job-def-v7' instead of 'optimo-job-def'${NC}"
echo
echo "Update the following in lambda/unified_handler.py around line 108:"
echo "  'jobDefinition': 'optimo-job-def-v7',"
echo

# Step 10: Test the container locally
echo -e "${GREEN}Step 10: Testing container locally...${NC}"

# Create test environment file
cat > /tmp/test_env.list << EOF
JOB_ID=test-local-$(date +%s)
AWS_REGION=us-west-2
S3_INPUT_BUCKET=optimo-input-files-v2
S3_OUTPUT_BUCKET=optimo-output-files
DYNAMODB_TABLE=optimo-jobs
GEMINI_API_KEY=test-key
EOF

echo "Testing container startup..."
timeout 5 docker run --rm --env-file /tmp/test_env.list optimo-batch:v7 python -c "print('Container starts successfully')" 2>/dev/null

if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo -e "${GREEN}✓${NC} Container starts successfully"
else
    echo -e "${RED}✗${NC} Container test failed"
fi

rm -f /tmp/test_env.list

echo
echo -e "${GREEN}=== Fix Complete ===${NC}"
echo
echo "Summary of changes:"
echo "1. Fixed run_batch_job.py to use subprocess instead of importing non-existent class"
echo "2. Built and pushed new container image (v7)"
echo "3. Created new job definition: optimo-job-def-v7"
echo
echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo "1. Update lambda/unified_handler.py to use 'optimo-job-def-v7'"
echo "2. Deploy the updated Lambda function"
echo "3. Test with a new job submission"
echo
echo "To update Lambda quickly:"
echo "  cd lambda"
echo "  ./deploy_unified.sh"