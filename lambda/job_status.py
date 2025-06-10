import json
import boto3
import os
import logging
import traceback
import decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

batch = boto3.client('batch')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    # Handle OPTIONS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://brettenf-uw.github.io',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': ''
        }
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get job ID from path parameters
        job_id = event['pathParameters']['jobId']
        logger.info(f"Processing job status request for job: {job_id}")
        
        # Get job details from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            logger.warning(f"Job not found: {job_id}")
            return cors_response(404, {'error': 'Job not found'})
        
        job_item = response['Item']
        
        # If job is still running, check AWS Batch status
        if job_item['status'] in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']:
            batch_job_id = job_item.get('batchJobId')
            if batch_job_id:
                logger.info(f"Checking AWS Batch status for job: {batch_job_id}")
                
                batch_response = batch.describe_jobs(jobs=[batch_job_id])
                
                if batch_response['jobs']:
                    batch_job = batch_response['jobs'][0]
                    batch_status = batch_job['status']
                    
                    # Update status in DynamoDB if changed
                    if batch_status != job_item['status']:
                        logger.info(f"Updating job status from {job_item['status']} to {batch_status}")
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
        response_data = {
            'jobId': job_id,
            'status': job_item['status'],
            'submittedAt': job_item.get('submittedAt'),
            'results': job_item.get('results'),
            'statusReason': job_item.get('statusReason', '')
        }
        
        logger.info(f"Returning job status: {job_item['status']}")
        return cors_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return cors_response(500, {'error': str(e)})

def cors_response(status_code, body_dict):
    """
    Helper function to create a response with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://brettenf-uw.github.io',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        },
        'body': json.dumps(body_dict, cls=DecimalEncoder)
    }
