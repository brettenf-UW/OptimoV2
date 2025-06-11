#!/bin/bash

# Comprehensive OptimoV2 System Test
echo "=== OptimoV2 Comprehensive System Test ==="
echo "Started at: $(date)"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION="us-west-2"
ACCOUNT_ID="529088253685"
ISSUES=0

# Function to check status
check() {
    local description=$1
    local command=$2
    local expected=$3
    
    echo -n "Checking $description... "
    result=$(eval $command 2>&1)
    
    if [[ -n "$expected" ]] && [[ "$result" != *"$expected"* ]]; then
        echo -e "${RED}FAILED${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((ISSUES++))
    else
        echo -e "${GREEN}OK${NC}"
    fi
}

echo -e "${BLUE}1. AWS Infrastructure Check${NC}"
echo "================================"

# Check Lambda configuration
check "Lambda function exists" \
    "aws lambda get-function --function-name optimo-unified-handler --region $REGION --query 'Configuration.FunctionName' --output text" \
    "optimo-unified-handler"

check "Lambda uses job-def-v8" \
    "aws lambda get-function-configuration --function-name optimo-unified-handler --region $REGION --query 'Environment.Variables.JOB_DEFINITION' --output text" \
    "optimo-job-def-v8"

check "Lambda uses correct S3 bucket" \
    "aws lambda get-function-configuration --function-name optimo-unified-handler --region $REGION --query 'Environment.Variables.S3_INPUT_BUCKET' --output text" \
    "optimo-input-files-v2"

# Check S3 buckets
check "Input bucket exists" \
    "aws s3api head-bucket --bucket optimo-input-files-v2 2>&1 && echo 'EXISTS'" \
    "EXISTS"

check "Output bucket exists" \
    "aws s3api head-bucket --bucket optimo-output-files 2>&1 && echo 'EXISTS'" \
    "EXISTS"

# Check DynamoDB
check "DynamoDB table exists" \
    "aws dynamodb describe-table --table-name optimo-jobs --region $REGION --query 'Table.TableStatus' --output text" \
    "ACTIVE"

# Check Batch
check "Compute environment enabled" \
    "aws batch describe-compute-environments --compute-environments optimo-compute-env --region $REGION --query 'computeEnvironments[0].state' --output text" \
    "ENABLED"

check "Job queue enabled" \
    "aws batch describe-job-queues --job-queues optimo-job-queue --region $REGION --query 'jobQueues[0].state' --output text" \
    "ENABLED"

# Check job definition
check "Job definition v8 exists" \
    "aws batch describe-job-definitions --job-definition-name optimo-job-def-v8 --status ACTIVE --region $REGION --query 'jobDefinitions[0].status' --output text" \
    "ACTIVE"

check "Job def has AWS_DEFAULT_REGION" \
    "aws batch describe-job-definitions --job-definition-name optimo-job-def-v8 --status ACTIVE --region $REGION --query 'jobDefinitions[0].containerProperties.environment[?name==\`AWS_DEFAULT_REGION\`].value' --output text" \
    "us-west-2"

echo
echo -e "${BLUE}2. Container Image Check${NC}"
echo "================================"

# Check if v8 image exists
IMAGE_EXISTS=$(aws ecr describe-images --repository-name optimo-batch --image-ids imageTag=v8 --region $REGION 2>&1)
if [[ "$IMAGE_EXISTS" == *"ImageNotFoundException"* ]]; then
    echo -e "${RED}❌ Container v8 NOT found in ECR${NC}"
    echo -e "${YELLOW}Action Required: Run the PowerShell script to build and push the container:${NC}"
    echo "  ./rebuild_container_v8.ps1"
    ((ISSUES++))
else
    echo -e "${GREEN}✅ Container v8 exists in ECR${NC}"
fi

echo
echo -e "${BLUE}3. Lambda Permissions Check${NC}"
echo "================================"

# Check IAM policies
POLICIES=$(aws iam list-attached-role-policies --role-name optimo-lambda-role --query 'AttachedPolicies[*].PolicyName' --output text)
if [[ "$POLICIES" == *"optimo-lambda-s3-v2-policy"* ]]; then
    echo -e "${GREEN}✅ Lambda has S3 v2 bucket permissions${NC}"
else
    echo -e "${RED}❌ Lambda missing S3 v2 bucket permissions${NC}"
    ((ISSUES++))
fi

echo
echo -e "${BLUE}4. Recent Job Analysis${NC}"
echo "================================"

# Check recent failed jobs
RECENT_JOBS=$(aws dynamodb scan --table-name optimo-jobs --region $REGION --max-items 5 --query 'Items[?status.S==`FAILED`].{JobId:jobId.S,Status:status.S}' --output json)
if [[ "$RECENT_JOBS" != "[]" ]]; then
    echo -e "${YELLOW}⚠️  Recent failed jobs found:${NC}"
    echo "$RECENT_JOBS" | jq -r '.[] | "  - \(.JobId): \(.Status)"'
else
    echo -e "${GREEN}✅ No recent failed jobs${NC}"
fi

echo
echo -e "${BLUE}5. API Endpoint Test${NC}"
echo "================================"

# Test API endpoint
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs)
if [[ "$API_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✅ API endpoint responding (HTTP $API_RESPONSE)${NC}"
else
    echo -e "${RED}❌ API endpoint error (HTTP $API_RESPONSE)${NC}"
    ((ISSUES++))
fi

echo
echo -e "${BLUE}6. File Upload Test${NC}"
echo "================================"

# Create test file
echo "test" > /tmp/optimo-test-upload.txt

# Test S3 upload
if aws s3 cp /tmp/optimo-test-upload.txt s3://optimo-input-files-v2/test-upload.txt 2>/dev/null; then
    echo -e "${GREEN}✅ Can upload to S3 bucket${NC}"
    aws s3 rm s3://optimo-input-files-v2/test-upload.txt 2>/dev/null
else
    echo -e "${YELLOW}⚠️  Cannot upload to S3 (normal if running locally)${NC}"
fi
rm /tmp/optimo-test-upload.txt

echo
echo -e "${BLUE}7. System Readiness Summary${NC}"
echo "================================"

if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo
    echo "The system is ready for optimization jobs!"
    echo
    echo "Next steps:"
    echo "1. If container v8 is missing, run: ./rebuild_container_v8.ps1"
    echo "2. Go to: https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
    echo "3. Upload your CSV files and submit a job"
    echo "4. Monitor with: aws dynamodb get-item --table-name optimo-jobs --key '{\"jobId\": {\"S\": \"YOUR-JOB-ID\"}}' --region us-west-2"
else
    echo -e "${RED}❌ FOUND $ISSUES ISSUES${NC}"
    echo
    echo "Please address the issues above before submitting jobs."
    if [[ "$IMAGE_EXISTS" == *"ImageNotFoundException"* ]]; then
        echo
        echo -e "${YELLOW}Priority: Build and push container v8 using:${NC}"
        echo "  ./rebuild_container_v8.ps1"
    fi
fi

echo
echo "Test completed at: $(date)"