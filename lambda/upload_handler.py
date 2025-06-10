import json
import boto3
import os
import uuid
import logging
import traceback
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_INPUT_BUCKET', 'optimo-input-files')

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
        
        # Parse request
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        logger.info(f"Processing upload request for file: {file_name}, type: {file_type}")
        
        if not file_name or not file_type:
            return cors_response(400, {'error': 'Missing fileName or fileType'})
        
        # Generate a unique file key
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_key = f"uploads/{timestamp}-{file_name}"
        
        # Generate presigned URL for upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_key,
                'ContentType': file_type
            },
            ExpiresIn=300  # URL expires in 5 minutes
        )
        
        logger.info(f"Generated presigned URL for file key: {file_key}")
        return cors_response(200, {
            'uploadUrl': presigned_url,
            'fileKey': file_key
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
        'body': json.dumps(body_dict)
    }
