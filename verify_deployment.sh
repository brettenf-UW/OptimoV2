#!/bin/bash

# OptimoV2 Comprehensive Deployment Verification Script
# This script checks all components and ensures everything is properly deployed

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

echo -e "${BLUE}=== OptimoV2 Deployment Verification ===${NC}"
echo -e "${BLUE}Started at: $(date)${NC}"
echo

# Track issues
ISSUES_FOUND=0

# Function to check and report status
check_status() {
    local description=$1
    local command=$2
    local expected=$3
    
    echo -n "Checking $description... "
    result=$(eval $command 2>&1 || echo "ERROR")
    
    if [[ "$result" == *"ERROR"* ]] || [[ "$result" == *"error"* ]] || [[ "$result" == *"ResourceNotFoundException"* ]]; then
        echo -e "${RED}FAILED${NC}"
        echo -e "  ${RED}Error: $result${NC}"
        ((ISSUES_FOUND++))
        return 1
    elif [[ -n "$expected" ]] && [[ "$result" != *"$expected"* ]]; then
        echo -e "${YELLOW}WARNING${NC}"
        echo -e "  ${YELLOW}Expected: $expected${NC}"
        echo -e "  ${YELLOW}Found: $result${NC}"
        ((ISSUES_FOUND++))
        return 1
    else
        echo -e "${GREEN}OK${NC}"
        if [[ -n "$expected" ]]; then
            echo -e "  ${GREEN}Found: $result${NC}"
        fi
        return 0
    fi
}

echo -e "${BLUE}1. Checking Lambda Function Configuration${NC}"
echo "================================================"

# Check Lambda exists
check_status "Lambda function exists" \
    "aws lambda get-function --function-name $LAMBDA_FUNCTION --region $REGION --query 'Configuration.FunctionName' --output text" \
    "$LAMBDA_FUNCTION"

# Check Lambda environment variables
echo -e "\n${BLUE}Lambda Environment Variables:${NC}"
check_status "JOB_DEFINITION" \
    "aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.JOB_DEFINITION' --output text" \
    "$JOB_DEFINITION"

check_status "S3_INPUT_BUCKET" \
    "aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.S3_INPUT_BUCKET' --output text" \
    "$S3_INPUT_BUCKET"

check_status "S3_OUTPUT_BUCKET" \
    "aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.S3_OUTPUT_BUCKET' --output text" \
    "$S3_OUTPUT_BUCKET"

check_status "DYNAMODB_TABLE" \
    "aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.DYNAMODB_TABLE' --output text" \
    "$DYNAMODB_TABLE"

check_status "JOB_QUEUE" \
    "aws lambda get-function-configuration --function-name $LAMBDA_FUNCTION --region $REGION --query 'Environment.Variables.JOB_QUEUE' --output text" \
    "$JOB_QUEUE"

echo -e "\n${BLUE}2. Checking S3 Buckets${NC}"
echo "================================================"

# Check S3 buckets exist
check_status "Input bucket exists" \
    "aws s3api head-bucket --bucket $S3_INPUT_BUCKET 2>&1 && echo 'EXISTS'" \
    "EXISTS"

check_status "Output bucket exists" \
    "aws s3api head-bucket --bucket $S3_OUTPUT_BUCKET 2>&1 && echo 'EXISTS'" \
    "EXISTS"

# Check CORS configuration
echo -e "\n${BLUE}Checking CORS Configuration:${NC}"
check_status "Input bucket CORS" \
    "aws s3api get-bucket-cors --bucket $S3_INPUT_BUCKET --region $REGION 2>&1 | grep -q 'AllowedOrigins' && echo 'CONFIGURED' || echo 'NOT_CONFIGURED'" \
    "CONFIGURED"

check_status "Output bucket CORS" \
    "aws s3api get-bucket-cors --bucket $S3_OUTPUT_BUCKET --region $REGION 2>&1 | grep -q 'AllowedOrigins' && echo 'CONFIGURED' || echo 'NOT_CONFIGURED'" \
    "CONFIGURED"

echo -e "\n${BLUE}3. Checking DynamoDB Table${NC}"
echo "================================================"

check_status "DynamoDB table exists" \
    "aws dynamodb describe-table --table-name $DYNAMODB_TABLE --region $REGION --query 'Table.TableStatus' --output text" \
    "ACTIVE"

echo -e "\n${BLUE}4. Checking AWS Batch Configuration${NC}"
echo "================================================"

# Check compute environment
check_status "Compute environment exists" \
    "aws batch describe-compute-environments --compute-environments $COMPUTE_ENV --region $REGION --query 'computeEnvironments[0].state' --output text" \
    "ENABLED"

# Check job queue
check_status "Job queue exists" \
    "aws batch describe-job-queues --job-queues $JOB_QUEUE --region $REGION --query 'jobQueues[0].state' --output text" \
    "ENABLED"

# Check job definition
check_status "Job definition exists" \
    "aws batch describe-job-definitions --job-definition-name ${JOB_DEFINITION%%-*} --status ACTIVE --region $REGION --query 'jobDefinitions[?revision==\`7\`].status' --output text" \
    "ACTIVE"

# Check container image
echo -e "\n${BLUE}Checking Container Image:${NC}"
check_status "ECR repository exists" \
    "aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION --query 'repositories[0].repositoryName' --output text" \
    "$ECR_REPO"

check_status "Container image v7 exists" \
    "aws ecr describe-images --repository-name $ECR_REPO --image-ids imageTag=$CONTAINER_TAG --region $REGION --query 'imageDetails[0].imageTags[0]' --output text" \
    "$CONTAINER_TAG"

echo -e "\n${BLUE}5. Checking API Gateway${NC}"
echo "================================================"

# Get API Gateway ID
API_ID=$(aws apigateway get-rest-apis --region $REGION --query "items[?name=='optimo-api'].id" --output text)
if [[ -z "$API_ID" ]]; then
    echo -e "${YELLOW}WARNING: Could not find API Gateway named 'optimo-api'${NC}"
    echo "Checking for any API with optimo endpoints..."
    API_ID="3dbrbfl8f3"  # Known API ID from documentation
fi

check_status "API Gateway exists" \
    "aws apigateway get-rest-api --rest-api-id $API_ID --region $REGION --query 'name' --output text 2>&1 || echo 'NOT_FOUND'" \
    ""

echo -e "\n${BLUE}6. Checking Recent Job Activity${NC}"
echo "================================================"

echo "Recent Batch jobs:"
aws batch list-jobs --job-queue $JOB_QUEUE --region $REGION --max-results 5 \
    --query 'jobSummaryList[*].{Name:jobName,Status:status,Created:createdAt}' --output table || echo "No recent jobs"

echo -e "\n${BLUE}7. Checking CloudWatch Logs${NC}"
echo "================================================"

# Check if log groups exist
check_status "Lambda log group exists" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$LAMBDA_FUNCTION --region $REGION --query 'logGroups[0].logGroupName' --output text" \
    "/aws/lambda/$LAMBDA_FUNCTION"

check_status "Batch log group exists" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/batch/job --region $REGION --query 'logGroups[0].logGroupName' --output text" \
    "/aws/batch/job"

echo -e "\n${BLUE}8. Summary${NC}"
echo "================================================"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}✅ All checks passed! OptimoV2 appears to be properly deployed.${NC}"
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issues that need attention.${NC}"
    echo -e "${YELLOW}Run the fix_deployment.sh script to attempt automatic fixes.${NC}"
fi

echo -e "\n${BLUE}Quick Test Command:${NC}"
echo "To test the system, upload your CSV files at:"
echo "https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
echo
echo "Or use the API directly:"
echo "curl -X GET https://$API_ID.execute-api.$REGION.amazonaws.com/prod/jobs"

echo -e "\n${BLUE}Completed at: $(date)${NC}"