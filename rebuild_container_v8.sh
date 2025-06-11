#!/bin/bash

# Rebuild container v8 with region fix
echo "=== Building OptimoV2 Container v8 ==="

REGION="us-west-2"
ACCOUNT_ID="529088253685"
ECR_REPO="optimo-batch"
TAG="v8"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build the container
echo "Building Docker image..."
docker build -t $ECR_REPO:$TAG .

# Tag for ECR
echo "Tagging image..."
docker tag $ECR_REPO:$TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$TAG

# Push to ECR
echo "Pushing to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$TAG

# Create new job definition
echo "Creating new job definition..."
cat > /tmp/job-definition-v8.json << EOF
{
    "jobDefinitionName": "optimo-job-def-v8",
    "type": "container",
    "containerProperties": {
        "image": "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$TAG",
        "vcpus": 72,
        "memory": 140000,
        "jobRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/optimo-batch-role",
        "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
        "environment": [
            {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files-v2"},
            {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
            {"name": "DYNAMODB_TABLE", "value": "optimo-jobs"},
            {"name": "AWS_REGION", "value": "us-west-2"},
            {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"}
        ]
    }
}
EOF

aws batch register-job-definition --cli-input-json file:///tmp/job-definition-v8.json --region $REGION

# Update Lambda to use new job definition
echo "Updating Lambda to use v8..."
aws lambda update-function-configuration \
    --function-name optimo-unified-handler \
    --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v8}' \
    --region $REGION

echo
echo "✅ Container v8 deployed!"
echo "✅ Lambda updated to use optimo-job-def-v8"
echo
echo "The new container includes:"
echo "- AWS_DEFAULT_REGION set explicitly"
echo "- Region fix for boto3 initialization"
echo
echo "Try submitting a new job - it should work now!"

# Clean up
rm /tmp/job-definition-v8.json