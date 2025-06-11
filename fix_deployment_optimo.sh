#!/bin/bash

# OptimoV2 Deployment Fix Script
# This script fixes common deployment issues found by verify_deployment.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
ACCOUNT_ID="529088253685"
LAMBDA_FUNCTION="optimo-unified-handler"
JOB_QUEUE="optimo-job-queue"
JOB_DEFINITION="optimo-job-def-v7"
S3_INPUT_BUCKET="optimo-input-files-v2"
S3_OUTPUT_BUCKET="optimo-output-files"
DYNAMODB_TABLE="optimo-jobs"
COMPUTE_ENV="optimo-compute-env"
ECR_REPO="optimo-batch"
CONTAINER_TAG="v7"

echo -e "${BLUE}=== OptimoV2 Deployment Fix Script ===${NC}"
echo -e "${BLUE}Started at: $(date)${NC}"
echo

# Function to execute fixes
fix_issue() {
    local description=$1
    local command=$2
    
    echo -e "${YELLOW}Fixing: $description${NC}"
    if eval $command; then
        echo -e "${GREEN}✅ Fixed successfully${NC}"
    else
        echo -e "${RED}❌ Fix failed${NC}"
        return 1
    fi
    echo
}

echo -e "${BLUE}1. Updating Lambda Configuration${NC}"
echo "================================================"

# Update Lambda environment variables
fix_issue "Lambda environment variables" \
    "aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION \
        --environment 'Variables={S3_INPUT_BUCKET=$S3_INPUT_BUCKET,S3_OUTPUT_BUCKET=$S3_OUTPUT_BUCKET,DYNAMODB_TABLE=$DYNAMODB_TABLE,JOB_QUEUE=$JOB_QUEUE,JOB_DEFINITION=$JOB_DEFINITION}' \
        --region $REGION"

# Wait for Lambda update to complete
echo "Waiting for Lambda update to complete..."
sleep 5

# Check Lambda update status
echo "Checking Lambda update status..."
while true; do
    STATUS=$(aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'LastUpdateStatus' --output text)
    if [[ "$STATUS" == "Successful" ]]; then
        echo -e "${GREEN}Lambda update completed successfully${NC}"
        break
    elif [[ "$STATUS" == "Failed" ]]; then
        echo -e "${RED}Lambda update failed${NC}"
        exit 1
    else
        echo "Update status: $STATUS - waiting..."
        sleep 2
    fi
done

echo -e "\n${BLUE}2. Ensuring S3 Buckets Exist${NC}"
echo "================================================"

# Create S3 buckets if they don't exist
echo "Checking input bucket..."
if ! aws s3api head-bucket --bucket $S3_INPUT_BUCKET 2>/dev/null; then
    fix_issue "Creating input bucket" \
        "aws s3api create-bucket --bucket $S3_INPUT_BUCKET --region $REGION --create-bucket-configuration LocationConstraint=$REGION"
else
    echo -e "${GREEN}Input bucket already exists${NC}"
fi

echo "Checking output bucket..."
if ! aws s3api head-bucket --bucket $S3_OUTPUT_BUCKET 2>/dev/null; then
    fix_issue "Creating output bucket" \
        "aws s3api create-bucket --bucket $S3_OUTPUT_BUCKET --region $REGION --create-bucket-configuration LocationConstraint=$REGION"
else
    echo -e "${GREEN}Output bucket already exists${NC}"
fi

# Configure CORS for buckets
echo -e "\n${BLUE}Configuring CORS for S3 buckets${NC}"

CORS_CONFIG='{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}'

fix_issue "Input bucket CORS" \
    "echo '$CORS_CONFIG' | aws s3api put-bucket-cors --bucket $S3_INPUT_BUCKET --cors-configuration file:///dev/stdin"

fix_issue "Output bucket CORS" \
    "echo '$CORS_CONFIG' | aws s3api put-bucket-cors --bucket $S3_OUTPUT_BUCKET --cors-configuration file:///dev/stdin"

echo -e "\n${BLUE}3. Verifying Batch Configuration${NC}"
echo "================================================"

# Check if compute environment is enabled
COMPUTE_STATE=$(aws batch describe-compute-environments --compute-environments $COMPUTE_ENV --region $REGION --query 'computeEnvironments[0].state' --output text)
if [[ "$COMPUTE_STATE" != "ENABLED" ]]; then
    fix_issue "Enabling compute environment" \
        "aws batch update-compute-environment --compute-environment $COMPUTE_ENV --state ENABLED --region $REGION"
fi

# Check if job queue is enabled
QUEUE_STATE=$(aws batch describe-job-queues --job-queues $JOB_QUEUE --region $REGION --query 'jobQueues[0].state' --output text)
if [[ "$QUEUE_STATE" != "ENABLED" ]]; then
    fix_issue "Enabling job queue" \
        "aws batch update-job-queue --job-queue $JOB_QUEUE --state ENABLED --region $REGION"
fi

echo -e "\n${BLUE}4. Checking Container Image${NC}"
echo "================================================"

# Check if container image exists
IMAGE_EXISTS=$(aws ecr describe-images --repository-name $ECR_REPO --image-ids imageTag=$CONTAINER_TAG --region $REGION --query 'imageDetails[0].imageTags[0]' --output text 2>/dev/null || echo "NOT_FOUND")

if [[ "$IMAGE_EXISTS" == "NOT_FOUND" ]]; then
    echo -e "${YELLOW}Container image v7 not found in ECR${NC}"
    echo "Please run the following commands to build and push the container:"
    echo
    echo "cd /mnt/c/dev/OptimoV2"
    echo "docker build -t optimo-batch:v7 ."
    echo "docker tag optimo-batch:v7 $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$CONTAINER_TAG"
    echo "aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    echo "docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$CONTAINER_TAG"
else
    echo -e "${GREEN}Container image v7 exists${NC}"
fi

echo -e "\n${BLUE}5. Deploying Latest Lambda Code${NC}"
echo "================================================"

# Check if unified handler exists
if [[ -f "lambda/unified_handler.py" ]]; then
    cd lambda
    fix_issue "Packaging Lambda function" \
        "zip unified_handler.zip unified_handler.py"
    
    fix_issue "Updating Lambda code" \
        "aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://unified_handler.zip --region $REGION"
    
    cd ..
else
    echo -e "${YELLOW}Lambda code not found at lambda/unified_handler.py${NC}"
fi

echo -e "\n${BLUE}6. Final Verification${NC}"
echo "================================================"

# Quick verification of key settings
echo "Verifying Lambda configuration..."
CURRENT_JOB_DEF=$(aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.JOB_DEFINITION' --output text)
CURRENT_S3_BUCKET=$(aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.S3_INPUT_BUCKET' --output text)

if [[ "$CURRENT_JOB_DEF" == "$JOB_DEFINITION" ]] && [[ "$CURRENT_S3_BUCKET" == "$S3_INPUT_BUCKET" ]]; then
    echo -e "${GREEN}✅ Lambda configuration verified${NC}"
else
    echo -e "${RED}❌ Lambda configuration mismatch${NC}"
    echo "Expected JOB_DEFINITION: $JOB_DEFINITION, Got: $CURRENT_JOB_DEF"
    echo "Expected S3_INPUT_BUCKET: $S3_INPUT_BUCKET, Got: $CURRENT_S3_BUCKET"
fi

echo -e "\n${BLUE}Summary${NC}"
echo "================================================"
echo -e "${GREEN}Deployment fixes completed!${NC}"
echo
echo "Next steps:"
echo "1. Run ./verify_deployment.sh to check all components"
echo "2. Submit a test job at https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
echo "3. Monitor the job using:"
echo "   aws dynamodb get-item --table-name $DYNAMODB_TABLE --key '{\"jobId\": {\"S\": \"YOUR-JOB-ID\"}}' --region $REGION"

echo -e "\n${BLUE}Completed at: $(date)${NC}"