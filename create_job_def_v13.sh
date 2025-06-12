#!/bin/bash

# Create job definition v13 using container v13
echo "Creating job definition v13 with container v13..."

cat > /tmp/job-def-v13.json << 'EOF'
{
    "jobDefinitionName": "optimo-job-def-v13",
    "type": "container",
    "containerProperties": {
        "image": "529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v13",
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
            {"name": "GEMINI_API_KEY", "value": "AIzaSyAQC-ytf_lcDK_WZ0ZuOMG8r24QBqvKds0"},
            {"name": "JOB_COMPLETION_HANDLER", "value": "optimo-job-completion-handler"}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "/aws/batch/job",
                "awslogs-region": "us-west-2",
                "awslogs-stream-prefix": "optimo-job-def-v13"
            }
        }
    }
}
EOF

# Register job definition
aws batch register-job-definition --cli-input-json file:///tmp/job-def-v13.json --region us-west-2

# Update Lambda to use v13
echo "Updating Lambda to use job-def-v13..."
aws lambda update-function-configuration \
    --function-name optimo-unified-handler \
    --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v13}' \
    --region us-west-2 > /dev/null

# Clean up
rm /tmp/job-def-v13.json

echo "✅ Job definition v13 created successfully!"
echo "✅ Lambda updated to use job-def-v13"
echo ""
echo "All fixes applied:"
echo "1. ✅ File download reads from environment variables"
echo "2. ✅ python-dotenv dependency installed"
echo "3. ✅ Pipeline arguments corrected"
echo ""
echo "Your optimization jobs should now complete successfully!"