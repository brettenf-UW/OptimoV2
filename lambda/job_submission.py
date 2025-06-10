import json
import boto3
import os
import uuid
import time
import decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr

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
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get input files from request
        input_files = body.get('files', [])
        parameters = body.get('parameters', {})
        
        print(f"Input files: {input_files}")
        print(f"Parameters: {parameters}")
        
        if not input_files:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No input files provided'
                })
            }
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Convert float values to Decimal for DynamoDB
        if parameters:
            for key, value in parameters.items():
                if isinstance(value, float):
                    parameters[key] = decimal.Decimal(str(value))
        
        # Check if there are any running or submitted jobs
        table = dynamodb.Table(TABLE_NAME)
        running_jobs = table.scan(
            FilterExpression=Attr('status').eq('RUNNING') | Attr('status').eq('SUBMITTED')
        )
        
        # Filter out jobs that don't have a batchJobId (truly running jobs)
        running_jobs_with_batch = [job for job in running_jobs['Items'] if 'batchJobId' in job]
        
        # Determine job status and position
        timestamp = int(time.time())
        status = 'SUBMITTED'
        position = 0
        batch_job_id = None
        
        if running_jobs_with_batch:
            # If there are running jobs, queue this job
            status = 'QUEUED'
            position = len(running_jobs_with_batch)
        else:
            # No running jobs, submit to AWS Batch immediately
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
            batch_job_id = batch_job['jobId']
        
        # Store job information in DynamoDB
        item = {
            'jobId': job_id,
            'status': status,
            'submittedAt': timestamp,
            'queuedAt': timestamp,
            'inputFiles': input_files,
            'position': position
        }
        
        if batch_job_id:
            item['batchJobId'] = batch_job_id
        
        if parameters:
            item['parameters'] = parameters
        
        print(f"Saving item to DynamoDB: {json.dumps(item, cls=DecimalEncoder)}")
        table.put_item(Item=item)
        
        # Return job ID to client
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': status,
                'position': position,
                'submittedAt': timestamp
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
