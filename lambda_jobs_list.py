import json
import boto3
import os
import decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# Initialize clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')

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
        
        # Get all jobs from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        
        # Scan the table to get all jobs
        response = table.scan()
        jobs = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            jobs.extend(response.get('Items', []))
        
        # Convert DynamoDB format to frontend format
        formatted_jobs = []
        for job in jobs:
            formatted_job = {
                'id': job.get('jobId', ''),
                'status': convert_batch_status_to_frontend(job.get('status', 'UNKNOWN')),
                'progress': job.get('progress', 0),
                'createdAt': convert_timestamp_to_iso(job.get('submittedAt', job.get('createdAt', 0))),
                'updatedAt': convert_timestamp_to_iso(job.get('updatedAt', job.get('submittedAt', 0))),
                'currentStep': job.get('currentStep', ''),
                'maxIterations': job.get('parameters', {}).get('maxIterations', 5)
            }
            
            # Add completedAt if the job is complete
            if job.get('completedAt'):
                formatted_job['completedAt'] = convert_timestamp_to_iso(job.get('completedAt'))
            
            # Add error message if job failed
            if job.get('statusReason'):
                formatted_job['error'] = job.get('statusReason')
            
            formatted_jobs.append(formatted_job)
        
        # Sort by creation date (newest first)
        formatted_jobs.sort(key=lambda x: x['createdAt'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps(formatted_jobs, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def convert_batch_status_to_frontend(batch_status):
    """Convert AWS Batch status to frontend status"""
    status_map = {
        'SUBMITTED': 'pending',
        'PENDING': 'pending',
        'QUEUED': 'pending',
        'RUNNABLE': 'pending',
        'STARTING': 'pending',
        'RUNNING': 'running',
        'SUCCEEDED': 'completed',
        'FAILED': 'failed',
        'CANCELED': 'failed',
        'CANCELLED': 'failed',
        'COMPLETED': 'completed'
    }
    return status_map.get(batch_status.upper(), 'pending')

def convert_timestamp_to_iso(timestamp):
    """Convert Unix timestamp to ISO 8601 format"""
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).isoformat() + 'Z'
    elif isinstance(timestamp, str):
        # If it's already a string, return as is
        return timestamp
    else:
        # Default to current time if invalid
        return datetime.now().isoformat() + 'Z'