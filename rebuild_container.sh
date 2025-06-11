#!/bin/bash

# Quick rebuild and push script for the batch container

echo "Building and pushing updated container..."

# Copy the updated script over the old one
cp scripts/run_batch_job_updated.py scripts/run_batch_job.py

# Build the container
docker build -t optimo-batch:v7 .

# Tag for ECR
docker tag optimo-batch:v7 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 529088253685.dkr.ecr.us-west-2.amazonaws.com

# Push to ECR
docker push 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7

# Update job definition to use v7
aws batch register-job-definition \
  --job-definition-name optimo-job-updated \
  --type container \
  --container-properties '{
    "image": "529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7",
    "vcpus": 72,
    "memory": 140000,
    "jobRoleArn": "arn:aws:iam::529088253685:role/optimo-batch-role",
    "environment": [
      {"name": "AWS_REGION", "value": "us-west-2"},
      {"name": "DYNAMODB_TABLE", "value": "optimo-jobs"},
      {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
      {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files"}
    ]
  }' \
  --region us-west-2

echo "Done! New job definition created with v7 image."