import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')
TABLE_NAME = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    try:
        # Parse path parameters
        path_parameters = event.get('pathParameters', {})
        job_id = path_parameters.get('jobId')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing jobId parameter'
                })
            }
        
        # Get job details from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Job not found'
                })
            }
        
        job = response['Item']
        batch_job_id = job.get('batchJobId')
        
        # Cancel the AWS Batch job if it exists
        if batch_job_id:
            batch.cancel_job(
                jobId=batch_job_id,
                reason='Canceled by user'
            )
        
        # Update job status in DynamoDB
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, updatedAt = :updatedAt",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'CANCELED',
                ':updatedAt': int(datetime.now().timestamp())
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': 'CANCELED'
            })
        }
        
    except Exception as e:
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
