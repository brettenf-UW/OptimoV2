import json
import boto3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')

# Get the table name from environment variable or use default
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'optimo-jobs')

def lambda_handler(event, context):
    """
    Lambda function to list all optimization jobs with their status
    
    Returns:
        A list of jobs with their details sorted by creation time (newest first)
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', '50'))  # Default to 50 jobs
        
        # Get reference to the DynamoDB table
        table = dynamodb.Table(JOBS_TABLE)
        
        # Query the table for all jobs
        if status_filter:
            # If status filter is provided, query by status
            response = table.scan(
                FilterExpression=Key('status').eq(status_filter),
                Limit=limit
            )
        else:
            # Otherwise get all jobs
            response = table.scan(
                Limit=limit
            )
        
        jobs = response.get('Items', [])
        
        # Sort jobs by createdAt (newest first)
        jobs.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        # Format the response
        formatted_jobs = []
        for job in jobs:
            # Convert DynamoDB format to regular JSON
            job_data = {
                'jobId': job.get('jobId'),
                'status': job.get('status'),
                'createdAt': job.get('createdAt'),
                'completedAt': job.get('completedAt', None),
                'inputFiles': job.get('inputFiles', []),
                'hasResults': job.get('hasResults', False),
                'errorMessage': job.get('errorMessage', None)
            }
            formatted_jobs.append(job_data)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # For CORS support
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'jobs': formatted_jobs,
                'count': len(formatted_jobs)
            })
        }
        
    except Exception as e:
        print(f"Error listing jobs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list jobs',
                'message': str(e)
            })
        }
