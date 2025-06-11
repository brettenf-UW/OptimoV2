#!/bin/bash

echo "=== Easiest Fix: Add GEMINI_API_KEY to Job Definition ==="
echo
echo "Enter your Gemini API key:"
read -s GEMINI_API_KEY
echo

# Create job definition v9 with the API key
cat > /tmp/job-definition-v9.json << EOF
{
    "jobDefinitionName": "optimo-job-def-v9",
    "type": "container",
    "containerProperties": {
        "image": "529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v8",
        "vcpus": 72,
        "memory": 140000,
        "jobRoleArn": "arn:aws:iam::529088253685:role/optimo-batch-role",
        "executionRoleArn": "arn:aws:iam::529088253685:role/ecsTaskExecutionRole",
        "environment": [
            {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files-v2"},
            {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
            {"name": "DYNAMODB_TABLE", "value": "optimo-jobs"},
            {"name": "AWS_REGION", "value": "us-west-2"},
            {"name": "AWS_DEFAULT_REGION", "value": "us-west-2"},
            {"name": "LICENSE_SECRET_NAME", "value": "optimo/gurobi-license"},
            {"name": "GEMINI_API_KEY", "value": "$GEMINI_API_KEY"}
        ]
    }
}
EOF

# Register the job definition
echo "Creating job definition v9..."
aws batch register-job-definition --cli-input-json file:///tmp/job-definition-v9.json --region us-west-2

# Update Lambda to use v9
echo "Updating Lambda to use v9..."
aws lambda update-function-configuration \
    --function-name optimo-unified-handler \
    --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v9}' \
    --region us-west-2

echo
echo "✅ Done! Job definition v9 created with GEMINI_API_KEY"
echo "✅ Lambda updated to use v9"
echo
echo "Your next job submission will have the API key!"

# Clean up
rm /tmp/job-definition-v9.json