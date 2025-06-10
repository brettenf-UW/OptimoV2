import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
import decimal
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')
lambda_client = boto3.client('lambda')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job')
JOB_MANAGER_FUNCTION = os.environ.get('JOB_MANAGER_FUNCTION', 'optimo-job-manager')

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
        
        # Check if this is an EventBridge event from AWS Batch
        if event.get('source') == 'aws.batch' and event.get('detail-type') == 'Batch Job State Change':
            # Extract job details from EventBridge event
            detail = event.get('detail', {})
            batch_job_id = detail.get('jobId')
            status = detail.get('status')
            job_name = detail.get('jobName', '')
            
            # Extract our job ID from the job name (format: optimo-job-{uuid})
            if job_name.startswith('optimo-job-'):
                job_id = job_name.replace('optimo-job-', '')
            else:
                print(f"Job name doesn't match expected format: {job_name}")
                return {'statusCode': 200, 'body': json.dumps({'message': 'Not an Optimo job'})}
                
            # Map AWS Batch status to our status
            if status == 'SUCCEEDED':
                status = 'COMPLETED'
            elif status == 'FAILED':
                status = 'FAILED'
        else:
            # Direct invocation (legacy support)
            job_id = event.get('jobId')
            status = event.get('status', 'COMPLETED')
        
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing jobId parameter'
                })
            }
        
        # Update job status in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, completedAt = :completedAt",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':completedAt': int(datetime.now().timestamp())
            }
        )
        
        # Check for queued jobs
        queued_jobs = table.scan(
            FilterExpression=Attr('status').eq('QUEUED')
        )
        
        if not queued_jobs['Items']:
            print("No queued jobs found.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Job completed, no queued jobs found'
                })
            }
        
        # If there are queued jobs, invoke the job manager to start the next one
        print(f"Found {len(queued_jobs['Items'])} queued jobs. Invoking job manager.")
        lambda_client.invoke(
            FunctionName=JOB_MANAGER_FUNCTION,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'source': 'job_completion',
                'jobId': job_id
            })
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Job {job_id} marked as {status}, job manager invoked'
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
