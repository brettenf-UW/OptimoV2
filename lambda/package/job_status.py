import json
import boto3
import os

batch = boto3.client('batch')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    try:
        # Get job ID from path parameters
        job_id = event['pathParameters']['jobId']
        
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
        
        job_item = response['Item']
        
        # If job is still running, check AWS Batch status
        if job_item['status'] in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']:
            batch_job_id = job_item['batchJobId']
            batch_response = batch.describe_jobs(jobs=[batch_job_id])
            
            if batch_response['jobs']:
                batch_job = batch_response['jobs'][0]
                batch_status = batch_job['status']
                
                # Update status in DynamoDB if changed
                if batch_status != job_item['status']:
                    table.update_item(
                        Key={'jobId': job_id},
                        UpdateExpression='SET #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': batch_status}
                    )
                    job_item['status'] = batch_status
                
                # Add progress information if available
                if 'statusReason' in batch_job:
                    job_item['statusReason'] = batch_job['statusReason']
        
        # Return job status
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': job_item['status'],
                'submittedAt': job_item.get('submittedAt'),
                'results': job_item.get('results'),
                'statusReason': job_item.get('statusReason', '')
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
