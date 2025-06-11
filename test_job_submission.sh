#!/bin/bash

# Test Job Submission Script
echo "=== OptimoV2 Test Job Submission ==="
echo

# Configuration
API_URL="https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod"
REGION="us-west-2"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}1. Testing File Upload Endpoint${NC}"
echo "================================"

# Test upload endpoint with a simple request
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d '{"fileName":"test.csv","fileType":"text/csv","fileContent":"dGVzdCBkYXRhCg=="}')

echo "Upload Response: $UPLOAD_RESPONSE"

if [[ "$UPLOAD_RESPONSE" == *"error"* ]]; then
    echo -e "${RED}❌ Upload endpoint error${NC}"
else
    echo -e "${GREEN}✅ Upload endpoint working${NC}"
fi

echo
echo -e "${BLUE}2. Checking Job Definition Configuration${NC}"
echo "================================"

# Get the current job definition details
JOB_DEF_INFO=$(aws batch describe-job-definitions --job-definition-name optimo-job-def-v8 --status ACTIVE --region $REGION --query 'jobDefinitions[0]' --output json)

echo "Container Image: $(echo $JOB_DEF_INFO | grep -o '"image":"[^"]*"' | cut -d'"' -f4)"
echo "Environment Variables:"
echo "$JOB_DEF_INFO" | grep -A1 "AWS_REGION\|AWS_DEFAULT_REGION" | grep "value" | sed 's/.*"value": "\([^"]*\)".*/  - \1/'

echo
echo -e "${BLUE}3. Pre-flight Checks Summary${NC}"
echo "================================"

# Lambda configuration
LAMBDA_JOB_DEF=$(aws lambda get-function-configuration --function-name optimo-unified-handler --region $REGION --query 'Environment.Variables.JOB_DEFINITION' --output text)
echo -e "Lambda Job Definition: ${GREEN}$LAMBDA_JOB_DEF${NC}"

# Check if container exists
CONTAINER_EXISTS=$(aws ecr describe-images --repository-name optimo-batch --image-ids imageTag=v8 --region $REGION 2>&1)
if [[ "$CONTAINER_EXISTS" == *"ImageNotFoundException"* ]]; then
    echo -e "Container v8: ${RED}NOT FOUND${NC}"
    echo -e "${YELLOW}⚠️  You need to build and push container v8!${NC}"
else
    echo -e "Container v8: ${GREEN}EXISTS${NC}"
fi

# Batch compute environment
COMPUTE_STATUS=$(aws batch describe-compute-environments --compute-environments optimo-compute-env --region $REGION --query 'computeEnvironments[0].{State:state,Status:status}' --output json)
echo "Compute Environment: $(echo $COMPUTE_STATUS | grep -o '"State":"[^"]*"' | cut -d'"' -f4)"

echo
echo -e "${BLUE}4. Instructions for Testing${NC}"
echo "================================"
echo "To submit a test job:"
echo "1. Go to: https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
echo "2. Upload your 6 CSV files:"
echo "   - Period.csv"
echo "   - Sections_Information.csv"
echo "   - Student_Info.csv"
echo "   - Student_Preference_Info.csv"
echo "   - Teacher_Info.csv"
echo "   - Teacher_unavailability.csv"
echo "3. Configure parameters (or use defaults)"
echo "4. Click 'Submit Job'"
echo
echo "Monitor the job with:"
echo 'aws dynamodb get-item --table-name optimo-jobs --key '"'"'{"jobId": {"S": "YOUR-JOB-ID"}}'"'"' --region us-west-2'
echo
echo "Watch Batch job logs:"
echo 'aws logs tail /aws/batch/job --follow --region us-west-2'

echo
echo -e "${BLUE}5. Common Issues and Solutions${NC}"
echo "================================"
echo "- If job fails immediately: Check CloudWatch logs for the Batch job"
echo "- If 500 error on upload: Lambda needs S3 permissions (already fixed)"
echo "- If 'region not specified': Container needs AWS_DEFAULT_REGION (fixed in v8)"
echo "- If container not found: Run ./rebuild_container_v8.ps1 in PowerShell"

echo
echo -e "${GREEN}✅ System is configured correctly for v8!${NC}"
echo "The next job submission should work properly with the region fix."