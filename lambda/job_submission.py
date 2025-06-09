import json
import boto3
import uuid
import os
import time

batch = boto3.client('batch')
dynamodb = boto3.resource('dynamodb')
JOB_QUEUE = os.environ['JOB_QUEUE']
JOB_DEFINITION = os.environ['JOB_DEFINITION']
TABLE_NAME = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        input_files = body.get('files', [])
        
        if not input_files:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No input files provided'
                })
            }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Submit batch job
        response = batch.submit_job(
            jobName=f'optimo-{job_id}',
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEFINITION,
            containerOverrides={
                'environment': [
                    {
                        'name': 'JOB_ID',
                        'value': job_id
                    },
                    {
                        'name': 'INPUT_FILES',
                        'value': ','.join(input_files)
                    }
                ]
            }
        )
        
        # Store job metadata
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'jobId': job_id,
            'batchJobId': response['jobId'],
            'status': 'SUBMITTED',
            'inputFiles': input_files,
            'submittedAt': int(time.time())
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': 'SUBMITTED'
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
