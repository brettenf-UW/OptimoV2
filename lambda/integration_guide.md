# OptimoV2 Batch Job Integration Guide

This guide explains how to integrate the metrics calculation into your AWS Batch job to ensure the frontend displays real metrics instead of hardcoded values.

## Overview

The frontend expects the Lambda function to return metrics about the optimization results, including:

- Overall utilization percentage
- Number of sections optimized
- Percentage of students placed
- Average teacher load
- Number of constraint violations
- Chart data for utilization and teacher load distributions
- A human-readable optimization summary

## Integration Steps

### 1. Add the Metrics Calculation Script

Copy the `batch_job_metrics.py` file to your Docker container. This can be done by:

- Adding it to your Docker image during build
- Downloading it from S3 at runtime
- Including it in your code repository

### 2. Install Required Dependencies

Ensure your Docker container has the necessary dependencies:

```dockerfile
# In your Dockerfile
RUN pip install pandas boto3
```

### 3. Call the Metrics Calculation Function

At the end of your batch job, after the optimization is complete and results are uploaded to S3, add the following code:

```python
import batch_job_metrics

# List of output files uploaded to S3
output_files = [
    f"{job_id}/Master_Schedule.csv",
    f"{job_id}/Student_Assignments.csv",
    f"{job_id}/Constraint_Violations.csv"
    # Add any other result files here
]

# Calculate and store metrics
metrics = batch_job_metrics.calculate_and_store_metrics(
    job_id=job_id,
    output_files=output_files,
    output_bucket='optimo-output-files',  # Use your actual bucket name
    table_name='optimo-jobs'              # Use your actual table name
)
```

### 4. Update Your DynamoDB Item

The metrics calculation function will automatically update the DynamoDB item with the calculated metrics. Make sure your batch job has the necessary IAM permissions to update the DynamoDB table.

## Required CSV File Format

The metrics calculation expects the following CSV files:

### Master_Schedule.csv
Required columns:
- `Section_ID`: Unique identifier for each section
- `Capacity`: Maximum number of students for the section (optional, defaults to 30)
- `Teacher_ID`: Identifier for the teacher assigned to the section

### Student_Assignments.csv
Required columns:
- `Student_ID`: Identifier for each student
- `Section_ID`: Identifier for the assigned section

### Constraint_Violations.csv (optional)
Any format is acceptable. The script simply counts the number of rows to determine the violation count.

## Troubleshooting

If metrics are not appearing in the frontend:

1. Check CloudWatch logs for the batch job to ensure the metrics calculation is running
2. Verify the DynamoDB item has a `metrics` attribute after the job completes
3. Ensure the Lambda function has sufficient permissions to read from DynamoDB
4. Check that the CSV files are being uploaded to S3 with the correct format

## Example Implementation

```python
# At the end of your run_batch_job.py script

# Upload result files to S3
s3_client = boto3.client('s3')
output_files = []

for file_name in ['Master_Schedule.csv', 'Student_Assignments.csv', 'Constraint_Violations.csv']:
    if os.path.exists(file_name):
        s3_key = f"{job_id}/{file_name}"
        s3_client.upload_file(file_name, 'optimo-output-files', s3_key)
        output_files.append(s3_key)

# Calculate and store metrics
import batch_job_metrics
metrics = batch_job_metrics.calculate_and_store_metrics(
    job_id=job_id,
    output_files=output_files,
    output_bucket='optimo-output-files',
    table_name='optimo-jobs'
)

# Update job status in DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('optimo-jobs')
table.update_item(
    Key={'jobId': job_id},
    UpdateExpression="set #status = :s, results = :r",
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':s': 'SUCCEEDED',
        ':r': output_files
    }
)
```
