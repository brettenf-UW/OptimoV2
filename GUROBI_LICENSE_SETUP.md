# Gurobi License Setup for OptimoV2

This document outlines how the Gurobi license is securely managed for the OptimoV2 application using AWS Secrets Manager.

## Overview

Instead of embedding the Gurobi license directly in the Docker image or code repository, we use AWS Secrets Manager to securely store and retrieve the license at runtime. This approach provides several benefits:

- **Security**: The license is encrypted at rest and in transit
- **Access Control**: Only authorized AWS resources can access the license
- **Auditability**: All access attempts are logged in AWS CloudTrail
- **Maintainability**: License can be updated without rebuilding Docker images

## Implementation Details

### 1. AWS Secrets Manager

The Gurobi license is stored in AWS Secrets Manager with the following configuration:

- **Secret Name**: `optimo/gurobi-license`
- **Region**: `us-west-2`
- **Description**: "Gurobi license for OptimoV2"
- **Content**: The full text of the Gurobi license file

### 2. IAM Permissions

The AWS Batch job role (`optimo-batch-role`) has been granted permission to access this secret through an IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:us-west-2:529088253685:secret:optimo/gurobi-license-*"
        }
    ]
}
```

### 3. Runtime License Retrieval

The batch job script (`run_batch_job.py`) retrieves the license at runtime using the following process:

1. Connect to AWS Secrets Manager
2. Retrieve the secret value containing the license
3. Create the Gurobi license directory (`~/.gurobi`)
4. Write the license content to `~/.gurobi/gurobi.lic`
5. Set the `GRB_LICENSE_FILE` environment variable to point to this file

### 4. AWS Batch Job Definition

The AWS Batch job definition has been updated to include the necessary environment variables:

```json
{
    "environment": [
        {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files"},
        {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
        {"name": "AWS_REGION", "value": "us-west-2"},
        {"name": "LICENSE_SECRET_NAME", "value": "optimo/gurobi-license"}
    ]
}
```

## Updating the License

When the Gurobi license needs to be updated:

1. Log in to the AWS Management Console
2. Navigate to AWS Secrets Manager
3. Select the `optimo/gurobi-license` secret
4. Click "Edit"
5. Update the secret value with the new license content
6. Save the changes

No code changes or container rebuilds are required when updating the license.

## Security Considerations

- The license is only retrieved when a batch job runs
- The license file is stored in the container's ephemeral storage
- The container is terminated after the job completes
- Access to the secret is logged in AWS CloudTrail
- The secret can be rotated if needed
