#!/bin/bash

# Create job definition v10 using container v9
echo "Creating job definition v10 with container v9..."

cat > /tmp/job-def-v10.json << 'EOF'
{
    "jobDefinitionName": "optimo-job-def-v10",
    "type": "container",
    "containerProperties": {
        "image": "529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v9",
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
                "awslogs-stream-prefix": "optimo-job-def-v10"
            }
        }
    }
}
EOF

# Register job definition
aws batch register-job-definition --cli-input-json file:///tmp/job-def-v10.json --region us-west-2

# Clean up
rm /tmp/job-def-v10.json

echo "✅ Job definition v10 created successfully!"
echo "✅ Lambda is already configured to use job-def-v10"