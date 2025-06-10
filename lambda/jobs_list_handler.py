import json
import boto3
import os
import decimal
from datetime import datetime

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
    try:
        # Get all jobs from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        
        # Extract items from response
        items = response.get('Items', [])
        
        # Convert DynamoDB items to JSON-serializable format
        jobs = []
        for item in items:
            # Convert timestamps to ISO format
            if 'createdAt' in item and isinstance(item['createdAt'], (int, float, decimal.Decimal)):
                item['createdAt'] = datetime.fromtimestamp(int(item['createdAt'])).isoformat()
            if 'updatedAt' in item and isinstance(item['updatedAt'], (int, float, decimal.Decimal)):
                item['updatedAt'] = datetime.fromtimestamp(int(item['updatedAt'])).isoformat()
            
            jobs.append(item)
        
        # Return jobs as JSON response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(jobs, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
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
