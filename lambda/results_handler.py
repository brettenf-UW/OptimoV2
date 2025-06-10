import json
import boto3
import os
import decimal
import logging
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'optimo-output-files')
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
        logger.info(f"Processing results request for job: {job_id}")
        
        # Get job details from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            logger.warning(f"Job not found: {job_id}")
            return cors_response(404, {'error': 'Job not found'})
        
        job_item = response['Item']
        
        # Check if job is completed
        if job_item['status'] != 'SUCCEEDED':
            logger.warning(f"Job is not completed. Current status: {job_item['status']}")
            return cors_response(400, {
                'error': f"Job is not completed. Current status: {job_item['status']}"
            })
        
        # Generate presigned URLs for result files
        results = job_item.get('results', [])
        download_urls = {}
        
        logger.info(f"Generating presigned URLs for {len(results)} result files")
        for file_key in results:
            file_name = os.path.basename(file_key)
            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': OUTPUT_BUCKET,
                    'Key': file_key
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            download_urls[file_name] = presigned_url
        
        return cors_response(200, {
            'jobId': job_id,
            'status': job_item['status'],
            'downloadUrls': download_urls
        })
        
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
