import json
import boto3
import os
import decimal
import logging
import traceback
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
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
        logger.info(f"Using table: {TABLE_NAME}")
        
        # Get all jobs from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        
        # Extract items from response
        items = response.get('Items', [])
        logger.info(f"Found {len(items)} jobs")
        
        # Convert DynamoDB items to JSON-serializable format
        jobs = []
        for item in items:
            # Convert timestamps to ISO format if needed
            if 'submittedAt' in item and isinstance(item['submittedAt'], (int, float, decimal.Decimal)):
                item['submittedAt'] = int(item['submittedAt'])
            
            jobs.append(item)
        
        # Return jobs as JSON response
        return cors_response(200, jobs)
        
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
