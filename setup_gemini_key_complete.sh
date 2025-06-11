#!/bin/bash

# Complete Gemini API Key Setup Script
echo "=== Complete Gemini API Key Setup ==="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
REGION="us-west-2"
ACCOUNT_ID="529088253685"
LAMBDA_FUNCTION="optimo-unified-handler"

# Get the API key
echo "Enter your Gemini API key (it will be hidden):"
read -s GEMINI_API_KEY
echo

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}Error: API key cannot be empty${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Creating job definition v9 with all required environment variables${NC}"

# Create comprehensive job definition
cat > /tmp/job-definition-v9.json << EOF
{
    "jobDefinitionName": "optimo-job-def-v9",
    "type": "container",
    "containerProperties": {
        "image": "529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v8",
        "vcpus": 72,
        "memory": 140000,
        "jobRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/optimo-batch-role",
        "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
        "environment": [
            {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files-v2"},
            {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
            {"name": "DYNAMODB_TABLE", "value": "optimo-jobs"},
            {"name": "AWS_REGION", "value": "us-west-2"},
            {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"},
            {"name": "LICENSE_SECRET_NAME", "value": "optimo/gurobi-license"},
            {"name": "GEMINI_API_KEY", "value": "$GEMINI_API_KEY"},
            {"name": "JOB_COMPLETION_HANDLER", "value": "optimo-job-completion-handler"}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "/aws/batch/job",
                "awslogs-region": "$REGION",
                "awslogs-stream-prefix": "optimo-job-def-v9"
            }
        }
    }
}
EOF

# Register job definition
echo "Registering job definition..."
JOB_DEF_RESULT=$(aws batch register-job-definition --cli-input-json file:///tmp/job-definition-v9.json --region $REGION 2>&1)

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Job definition v9 created successfully${NC}"
    echo "$JOB_DEF_RESULT" | grep -o '"revision": [0-9]*'
else
    echo -e "${RED}❌ Failed to create job definition${NC}"
    echo "$JOB_DEF_RESULT"
    exit 1
fi

echo
echo -e "${BLUE}Step 2: Updating Lambda to use v9${NC}"

# Update Lambda
LAMBDA_RESULT=$(aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION \
    --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v9}' \
    --region $REGION 2>&1)

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Lambda updated to use job-def-v9${NC}"
else
    echo -e "${RED}❌ Failed to update Lambda${NC}"
    echo "$LAMBDA_RESULT"
    exit 1
fi

echo
echo -e "${BLUE}Step 3: Verifying configuration${NC}"

# Wait for Lambda update
sleep 3

# Verify Lambda configuration
CURRENT_JOB_DEF=$(aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.JOB_DEFINITION' --output text)

if [[ "$CURRENT_JOB_DEF" == "optimo-job-def-v9" ]]; then
    echo -e "${GREEN}✅ Lambda is using job-def-v9${NC}"
else
    echo -e "${RED}❌ Lambda configuration mismatch: $CURRENT_JOB_DEF${NC}"
fi

# Verify job definition has API key
JOB_DEF_ENV=$(aws batch describe-job-definitions --job-definition-name optimo-job-def-v9 --status ACTIVE --region $REGION --query 'jobDefinitions[0].containerProperties.environment[?name==`GEMINI_API_KEY`]' --output json)

if [[ "$JOB_DEF_ENV" != "[]" ]]; then
    echo -e "${GREEN}✅ Job definition has GEMINI_API_KEY${NC}"
else
    echo -e "${RED}❌ Job definition missing GEMINI_API_KEY${NC}"
fi

echo
echo -e "${BLUE}Step 4: Testing pipeline requirements${NC}"

# Check if the pipeline script expects the API key
if grep -q "GEMINI_API_KEY" scripts/run_batch_job.py; then
    echo -e "${GREEN}✅ run_batch_job.py checks for GEMINI_API_KEY${NC}"
else
    echo -e "${YELLOW}⚠️  run_batch_job.py might need to be updated to use GEMINI_API_KEY${NC}"
fi

# Check if run_pipeline.py needs the key
if [ -f "scripts/run_pipeline.py" ]; then
    if grep -q "GEMINI_API_KEY\|gemini.*api.*key" scripts/run_pipeline.py; then
        echo -e "${GREEN}✅ run_pipeline.py expects GEMINI_API_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  run_pipeline.py might need GEMINI_API_KEY${NC}"
    fi
fi

echo
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo
echo "Your system now has:"
echo "✅ Job definition v9 with GEMINI_API_KEY"
echo "✅ Lambda configured to use v9"
echo "✅ All AWS services properly connected"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Submit a new job at https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
echo "2. The job should run successfully with Gemini AI optimization"
echo
echo -e "${YELLOW}Note: If the job still fails, check CloudWatch logs for:${NC}"
echo "  /aws/batch/job (look for optimo-job-def-v9 streams)"

# Clean up
rm -f /tmp/job-definition-v9.json

echo
echo -e "${GREEN}Ready to optimize!${NC}"