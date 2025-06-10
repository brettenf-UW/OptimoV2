import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
import decimal
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check for running jobs
        table = dynamodb.Table(TABLE_NAME)
        running_jobs = table.scan(
            FilterExpression=Attr('status').eq('RUNNING') | Attr('status').eq('SUBMITTED')
        )
        
        # Filter out jobs that don't have a batchJobId (truly running jobs)
        running_jobs_with_batch = [job for job in running_jobs['Items'] if 'batchJobId' in job]
        
        # If there are running jobs, don't start a new one
        if running_jobs_with_batch:
            print(f"There are already {len(running_jobs_with_batch)} running jobs. Not starting a new one.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No action taken, jobs already running'
                })
            }
        
        # Look for queued jobs
        queued_jobs = table.scan(
            FilterExpression=Attr('status').eq('QUEUED')
        )
        
        if not queued_jobs['Items']:
            print("No queued jobs found.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No queued jobs found'
                })
            }
        
        # Sort by position and timestamp
        sorted_jobs = sorted(queued_jobs['Items'], key=lambda x: (x.get('position', 999), x.get('queuedAt', 0)))
        
        if not sorted_jobs:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No jobs to process'
                })
            }
        
        # Get the next job
        next_job = sorted_jobs[0]
        job_id = next_job['jobId']
        input_files = next_job.get('inputFiles', [])
        
        print(f"Starting job {job_id}")
        
        # Submit to AWS Batch
        batch_job = batch.submit_job(
            jobName=f'optimo-job-{job_id}',
            jobQueue=JOB_QUEUE,
            jobDefinition='optimo-job-updated',
            containerOverrides={
                'environment': [
                    {
                        'name': 'jobId',
                        'value': job_id
                    },
                    {
                        'name': 'inputFiles',
                        'value': ','.join(input_files)
                    }
                ]
            }
        )
        
        # Update job status in DynamoDB
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, batchJobId = :batchJobId, startedAt = :startedAt",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SUBMITTED',
                ':batchJobId': batch_job['jobId'],
                ':startedAt': int(datetime.now().timestamp())
            }
        )
        
        # Update positions of remaining queued jobs
        for i, job in enumerate(sorted_jobs[1:]):
            table.update_item(
                Key={'jobId': job['jobId']},
                UpdateExpression="SET #position = :position",
                ExpressionAttributeNames={'#position': 'position'},
                ExpressionAttributeValues={
                    ':position': i
                }
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Started job {job_id}',
                'jobId': job_id,
                'batchJobId': batch_job['jobId']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
