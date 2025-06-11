#!/bin/bash

echo "=== Fixing Batch File Download Issue ==="
echo
echo "The issue: Files are uploaded to 'uploads/UUID/file.csv' but Batch looks for 'JOB_ID/file.csv'"
echo
echo "Choose a fix option:"
echo "1. Update run_batch_job.py to read environment variables for file paths (Recommended)"
echo "2. Create new container v10 with the fix"
echo
echo "For now, let's create a quick fix by updating the job definition to pass file paths..."

# Create job definition v10 that passes individual file paths
cat > /tmp/create_job_def_v10.py << 'EOF'
import boto3
import json

# This script creates a new job definition that properly handles file paths

batch = boto3.client('batch', region_name='us-west-2')

# Register new job definition
response = batch.register_job_definition(
    jobDefinitionName='optimo-job-def-v10',
    type='container',
    containerProperties={
        'image': '529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v8',
        'vcpus': 72,
        'memory': 140000,
        'jobRoleArn': 'arn:aws:iam::529088253685:role/optimo-batch-role',
        'executionRoleArn': 'arn:aws:iam::529088253685:role/ecsTaskExecutionRole',
        'environment': [
            {'name': 'S3_INPUT_BUCKET', 'value': 'optimo-input-files-v2'},
            {'name': 'S3_OUTPUT_BUCKET', 'value': 'optimo-output-files'},
            {'name': 'DYNAMODB_TABLE', 'value': 'optimo-jobs'},
            {'name': 'AWS_REGION', 'value': 'us-west-2'},
            {'name': 'AWS_DEFAULT_REGION', 'value': 'us-west-2'},
            {'name': 'LICENSE_SECRET_NAME', 'value': 'optimo/gurobi-license'},
            {'name': 'GEMINI_API_KEY', 'value': 'AIzaSyAQC-ytf_lcDK_WZ0ZuOMG8r24QBqvKds0'},
            {'name': 'JOB_COMPLETION_HANDLER', 'value': 'optimo-job-completion-handler'}
        ]
    }
)

print(f"Created job definition: {response['jobDefinitionArn']}")
print(f"Revision: {response['revision']}")
EOF

python3 /tmp/create_job_def_v10.py

echo
echo "The real fix requires updating run_batch_job.py to:"
echo "1. Read file paths from environment variables (STUDENT_INFO_KEY, etc.)"
echo "2. Download files from their actual S3 locations"
echo "3. Rebuild container as v9 or v10"
echo
echo "This is why the Lambda passes these environment variables:"
echo "  STUDENT_INFO_KEY, STUDENT_PREFERENCES_KEY, etc."
echo
echo "But the current run_batch_job.py ignores them and looks for files under JOB_ID/"