#!/bin/bash

# OptimoV2 Comprehensive Status Check
# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== OptimoV2 Deployment Status Summary ===${NC}"
echo -e "${BLUE}Generated at: $(date)${NC}"
echo

echo -e "${BLUE}1. Lambda Configuration:${NC}"
aws lambda get-function-configuration \
  --function-name optimo-unified-handler \
  --region us-west-2 \
  --query 'Environment.Variables.{JOB_DEF:JOB_DEFINITION,S3_INPUT:S3_INPUT_BUCKET,S3_OUTPUT:S3_OUTPUT_BUCKET,QUEUE:JOB_QUEUE,TABLE:DYNAMODB_TABLE}' \
  --output table

echo -e "\n${BLUE}2. S3 Buckets:${NC}"
echo "Input Bucket: optimo-input-files-v2"
aws s3api head-bucket --bucket optimo-input-files-v2 2>&1 && echo -e "${GREEN}✅ Exists${NC}" || echo -e "${RED}❌ Not Found${NC}"
echo "Output Bucket: optimo-output-files"
aws s3api head-bucket --bucket optimo-output-files 2>&1 && echo -e "${GREEN}✅ Exists${NC}" || echo -e "${RED}❌ Not Found${NC}"

echo -e "\n${BLUE}3. Job Definition (optimo-job-def-v7):${NC}"
aws batch describe-job-definitions \
  --job-definition-name optimo-job-def-v7 \
  --status ACTIVE \
  --region us-west-2 \
  --query 'jobDefinitions[0].{Status:status,Revision:revision,Image:containerProperties.image}' \
  --output table

echo -e "\n${BLUE}4. Batch Compute Environment:${NC}"
aws batch describe-compute-environments \
  --compute-environments optimo-compute-env \
  --region us-west-2 \
  --query 'computeEnvironments[0].{State:state,Status:status,DesiredvCpus:computeResources.desiredvCpus}' \
  --output table

echo -e "\n${BLUE}5. Recent Jobs (last 3):${NC}"
aws dynamodb scan \
  --table-name optimo-jobs \
  --region us-west-2 \
  --max-items 3 \
  --query 'Items[*].{JobId:jobId.S,Status:status.S,BatchJobId:batchJobId.S}' \
  --output table

echo -e "\n${BLUE}6. System Health:${NC}"
LAMBDA_CONFIG=$(aws lambda get-function-configuration --function-name optimo-unified-handler --region us-west-2 --query 'Environment.Variables.JOB_DEFINITION' --output text)
if [[ "$LAMBDA_CONFIG" == "optimo-job-def-v7" ]]; then
    echo -e "${GREEN}✅ Lambda is using correct job definition (v7)${NC}"
else
    echo -e "${YELLOW}⚠️  Lambda is using: $LAMBDA_CONFIG (should be optimo-job-def-v7)${NC}"
fi

S3_BUCKET=$(aws lambda get-function-configuration --function-name optimo-unified-handler --region us-west-2 --query 'Environment.Variables.S3_INPUT_BUCKET' --output text)
if [[ "$S3_BUCKET" == "optimo-input-files-v2" ]]; then
    echo -e "${GREEN}✅ Lambda is using correct S3 bucket${NC}"
else
    echo -e "${YELLOW}⚠️  Lambda is using: $S3_BUCKET (should be optimo-input-files-v2)${NC}"
fi

echo -e "\n${BLUE}Ready to Test:${NC}"
echo "1. Go to: https://brettenf-uw.github.io/OptimizationProjectFrontEnd/"
echo "2. Upload your CSV files"
echo "3. Submit a new job"
echo "4. Your job should now use the fixed container (v7) and complete successfully!"

echo -e "\n${BLUE}Monitor new jobs with:${NC}"
echo 'aws dynamodb get-item --table-name optimo-jobs --key '"'"'{"jobId": {"S": "YOUR-JOB-ID"}}'"'"' --region us-west-2'