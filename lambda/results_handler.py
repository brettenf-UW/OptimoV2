import json
import boto3
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
OUTPUT_BUCKET = os.environ['S3_OUTPUT_BUCKET']
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
        
        # Check if job is completed
        if job_item['status'] != 'SUCCEEDED':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Job is not completed. Current status: {job_item["status"]}'
                })
            }
        
        # Generate presigned URLs for result files
        results = job_item.get('results', [])
        download_urls = {}
        
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': job_item['status'],
                'downloadUrls': download_urls
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
