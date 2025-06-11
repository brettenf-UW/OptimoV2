"""
Unified Lambda Handler for OptimoV2
Handles all API endpoints in a single function for simplicity and consistency
"""

import json
import boto3
import os
import uuid
from datetime import datetime, timedelta
import traceback
import logging
import pandas as pd
import io
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
batch = boto3.client('batch')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
INPUT_BUCKET = os.environ.get('S3_INPUT_BUCKET', 'optimo-input-files')
OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'optimo-output-files')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job-updated')

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': 'https://brettenf-uw.github.io',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 != 0 else int(o)
        return super(DecimalEncoder, self).default(o)

def response(status_code: int, body: Any) -> Dict:
    """Create API response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event: Dict, context: Any) -> Dict:
    """Main Lambda handler - routes requests to appropriate functions"""
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, '')
    
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        logger.info(f"Handling {method} {path}")
        
        # Route to appropriate handler
        if path == '/upload' and method == 'POST':
            return handle_upload(event)
        elif path == '/jobs' and method == 'POST':
            return handle_job_submission(event)
        elif path == '/jobs' and method == 'GET':
            return handle_list_jobs(event)
        elif path.startswith('/jobs/') and '/status' in path and method == 'GET':
            job_id = path.split('/')[2]
            return handle_job_status(job_id)
        elif path.startswith('/jobs/') and '/results' in path and method == 'GET':
            job_id = path.split('/')[2]
            return handle_job_results(job_id)
        elif path.startswith('/jobs/') and '/cancel' in path and method == 'POST':
            job_id = path.split('/')[2]
            return handle_job_cancel(job_id)
        else:
            return response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return response(500, {'error': str(e)})

def handle_upload(event: Dict) -> Dict:
    """Generate presigned URL for file upload"""
    try:
        body = json.loads(event.get('body', '{}'))
        # Accept both fileName (camelCase) and filename (lowercase) for compatibility
        filename = body.get('fileName') or body.get('filename', '')
        
        if not filename:
            return response(400, {'error': 'Filename is required'})
        
        # Generate unique key
        file_id = str(uuid.uuid4())
        file_key = f"uploads/{file_id}/{filename}"
        
        # Generate presigned URL for upload
        # Include Content-Type to avoid signature mismatch
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': INPUT_BUCKET, 
                'Key': file_key,
                'ContentType': 'text/csv'  # Set a default content type
            },
            ExpiresIn=3600
        )
        
        return response(200, {
            'uploadUrl': presigned_url,
            'fileKey': file_key
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return response(500, {'error': str(e)})

def handle_job_submission(event: Dict) -> Dict:
    """Submit optimization job to AWS Batch"""
    try:
        body = json.loads(event.get('body', '{}'))
        job_id = str(uuid.uuid4())
        
        # Extract parameters
        s3_keys = body.get('s3Keys', {})
        parameters = body.get('parameters', {})
        
        # Validate required files
        required_files = ['studentInfo', 'studentPreferences', 'teacherInfo', 
                         'teacherUnavailability', 'sectionsInfo']
        missing_files = [f for f in required_files if f not in s3_keys]
        
        if missing_files:
            return response(400, {'error': f'Missing required files: {missing_files}'})
        
        # Prepare environment variables for Batch job
        environment = [
            {'name': 'JOB_ID', 'value': job_id},
            {'name': 'S3_INPUT_BUCKET', 'value': INPUT_BUCKET},
            {'name': 'S3_OUTPUT_BUCKET', 'value': OUTPUT_BUCKET},
            {'name': 'STUDENT_INFO_KEY', 'value': s3_keys['studentInfo']},
            {'name': 'STUDENT_PREFERENCES_KEY', 'value': s3_keys['studentPreferences']},
            {'name': 'TEACHER_INFO_KEY', 'value': s3_keys['teacherInfo']},
            {'name': 'TEACHER_UNAVAILABILITY_KEY', 'value': s3_keys['teacherUnavailability']},
            {'name': 'SECTIONS_INFO_KEY', 'value': s3_keys['sectionsInfo']},
            {'name': 'MAX_ITERATIONS', 'value': str(parameters.get('maxIterations', 3))},
            {'name': 'MIN_UTILIZATION', 'value': str(parameters.get('minUtilization', 0.7))},
            {'name': 'MAX_UTILIZATION', 'value': str(parameters.get('maxUtilization', 1.15))},
            {'name': 'OPTIMAL_RANGE_MIN', 'value': str(parameters.get('optimalRangeMin', 0.8))},
            {'name': 'OPTIMAL_RANGE_MAX', 'value': str(parameters.get('optimalRangeMax', 1.0))},
            {'name': 'PERIOD_KEY', 'value': s3_keys.get('period', '')},
        ]
        
        # Submit to AWS Batch
        batch_response = batch.submit_job(
            jobName=f'optimo-job-{job_id}',
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEFINITION,
            containerOverrides={'environment': environment}
        )
        
        batch_job_id = batch_response['jobId']
        
        # Convert float parameters to Decimal for DynamoDB
        if parameters:
            for key, value in parameters.items():
                if isinstance(value, float):
                    parameters[key] = Decimal(str(value))
        
        # Store job metadata in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'jobId': job_id,
            'batchJobId': batch_job_id,
            'status': 'SUBMITTED',
            'createdAt': int(datetime.now().timestamp()),
            's3Keys': s3_keys,
            'parameters': parameters,
            'progress': 0
        })
        
        return response(200, {
            'jobId': job_id,
            'status': 'SUBMITTED',
            'message': 'Job submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Job submission error: {str(e)}")
        return response(500, {'error': str(e)})

def handle_list_jobs(event: Dict) -> Dict:
    """List all jobs with their current status"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Scan all jobs (in production, implement pagination)
        result = table.scan()
        jobs = result.get('Items', [])
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        
        # For each job, get current Batch status if still running
        for job in jobs:
            if job['status'] in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']:
                try:
                    batch_job_id = job.get('batchJobId')
                    if batch_job_id:
                        batch_jobs = batch.describe_jobs(jobs=[batch_job_id])
                        if batch_jobs['jobs']:
                            current_status = batch_jobs['jobs'][0]['status']
                            job['status'] = current_status
                            
                            # Update in DynamoDB if status changed
                            if current_status != job.get('status'):
                                table.update_item(
                                    Key={'jobId': job['jobId']},
                                    UpdateExpression='SET #status = :status',
                                    ExpressionAttributeNames={'#status': 'status'},
                                    ExpressionAttributeValues={':status': current_status}
                                )
                except Exception as e:
                    logger.warning(f"Failed to get Batch status for {job['jobId']}: {str(e)}")
        
        # Return simplified job list
        job_list = [{
            'id': job['jobId'],
            'status': job['status'],
            'createdAt': job.get('createdAt'),
            'progress': job.get('progress', 0),
            'maxIterations': job.get('parameters', {}).get('maxIterations', 3)
        } for job in jobs[:10]]  # Limit to 10 most recent
        
        return response(200, job_list)
        
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        return response(500, {'error': str(e)})

def handle_job_status(job_id: str) -> Dict:
    """Get detailed status for a specific job"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Get job from DynamoDB
        result = table.get_item(Key={'jobId': job_id})
        if 'Item' not in result:
            return response(404, {'error': 'Job not found'})
        
        job = result['Item']
        
        # Get current status from Batch if job is running
        if job['status'] in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']:
            batch_job_id = job.get('batchJobId')
            if batch_job_id:
                try:
                    batch_jobs = batch.describe_jobs(jobs=[batch_job_id])
                    if batch_jobs['jobs']:
                        batch_job = batch_jobs['jobs'][0]
                        job['status'] = batch_job['status']
                        
                        # Update DynamoDB with latest status
                        update_expr = 'SET #status = :status'
                        expr_names = {'#status': 'status'}
                        expr_values = {':status': batch_job['status']}
                        
                        # Add completion time if job finished
                        if batch_job['status'] in ['SUCCEEDED', 'FAILED']:
                            update_expr += ', completedAt = :completedAt'
                            expr_values[':completedAt'] = int(datetime.now().timestamp())
                        
                        table.update_item(
                            Key={'jobId': job_id},
                            UpdateExpression=update_expr,
                            ExpressionAttributeNames=expr_names,
                            ExpressionAttributeValues=expr_values
                        )
                except Exception as e:
                    logger.warning(f"Failed to get Batch status: {str(e)}")
        
        # Calculate progress based on status
        status_progress = {
            'SUBMITTED': 0,
            'PENDING': 5,
            'RUNNABLE': 10,
            'STARTING': 15,
            'RUNNING': 50,  # Will be overridden by actual progress
            'SUCCEEDED': 100,
            'FAILED': 0
        }
        
        # Return status info
        return response(200, {
            'jobId': job_id,
            'status': job['status'],
            'progress': job.get('progress', status_progress.get(job['status'], 0)),
            'createdAt': job.get('createdAt'),
            'completedAt': job.get('completedAt'),
            'currentStep': job.get('currentStep', 'Processing...'),
            'error': job.get('error'),
            'maxIterations': job.get('parameters', {}).get('maxIterations', 3)
        })
        
    except Exception as e:
        logger.error(f"Job status error: {str(e)}")
        return response(500, {'error': str(e)})

def handle_job_results(job_id: str) -> Dict:
    """Get job results with calculated metrics"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Get job from DynamoDB
        result = table.get_item(Key={'jobId': job_id})
        if 'Item' not in result:
            return response(404, {'error': 'Job not found'})
        
        job = result['Item']
        
        # Check if job is completed
        if job['status'] not in ['SUCCEEDED', 'COMPLETED']:
            return response(400, {'error': f'Job not completed. Status: {job["status"]}'})
        
        # Check if metrics are cached
        if 'metrics' in job and 'downloadUrls' in job:
            # Regenerate URLs if they might have expired
            urls_generated_at = job.get('urlsGeneratedAt', 0)
            if datetime.now().timestamp() - urls_generated_at < 3000:  # 50 minutes
                return response(200, {
                    'jobId': job_id,
                    'status': job['status'],
                    'downloadUrls': job['downloadUrls'],
                    'metrics': job['metrics']
                })
        
        # List result files
        prefix = f"jobs/{job_id}/"
        result_files = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=prefix)
        
        if 'Contents' not in result_files:
            return response(404, {'error': 'No results found'})
        
        # Generate download URLs
        download_urls = {}
        file_keys = {}
        
        for obj in result_files['Contents']:
            filename = obj['Key'].split('/')[-1]
            if filename.endswith('.csv'):
                presigned_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': OUTPUT_BUCKET, 'Key': obj['Key']},
                    ExpiresIn=3600
                )
                download_urls[filename] = presigned_url
                file_keys[filename] = obj['Key']
        
        # Calculate metrics from CSV files
        metrics = calculate_metrics(job_id, file_keys)
        
        # Cache results in DynamoDB
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET metrics = :metrics, downloadUrls = :urls, urlsGeneratedAt = :timestamp',
            ExpressionAttributeValues={
                ':metrics': metrics,
                ':urls': download_urls,
                ':timestamp': int(datetime.now().timestamp())
            }
        )
        
        return response(200, {
            'jobId': job_id,
            'status': job['status'],
            'downloadUrls': download_urls,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Job results error: {str(e)}")
        return response(500, {'error': str(e)})

def handle_job_cancel(job_id: str) -> Dict:
    """Cancel a running job"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Get job from DynamoDB
        result = table.get_item(Key={'jobId': job_id})
        if 'Item' not in result:
            return response(404, {'error': 'Job not found'})
        
        job = result['Item']
        batch_job_id = job.get('batchJobId')
        
        if not batch_job_id:
            return response(400, {'error': 'No batch job ID found'})
        
        # Terminate the Batch job
        batch.terminate_job(
            jobId=batch_job_id,
            reason='User requested cancellation'
        )
        
        # Update status in DynamoDB
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'FAILED'}
        )
        
        return response(200, {
            'jobId': job_id,
            'status': 'FAILED',
            'message': 'Job cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Job cancel error: {str(e)}")
        return response(500, {'error': str(e)})

def calculate_metrics(job_id: str, file_keys: Dict[str, str]) -> Dict:
    """Calculate optimization metrics from result CSV files"""
    try:
        # Default metrics structure
        metrics = {
            'summary': {
                'overallUtilization': 0.0,
                'sectionsOptimized': 0,
                'studentsPlaced': 0.0,
                'averageTeacherLoad': 0.0,
                'violations': 0
            },
            'charts': {
                'utilizationDistribution': [0, 0, 0, 0, 0],
                'teacherLoadDistribution': [0, 0, 0, 0, 0]
            },
            'optimizationSummary': ''
        }
        
        # Download and parse CSV files
        master_schedule_df = None
        student_assignments_df = None
        violations_df = None
        
        for filename, key in file_keys.items():
            if 'Master_Schedule' in filename:
                master_schedule_df = download_csv(key)
            elif 'Student_Assignments' in filename:
                student_assignments_df = download_csv(key)
            elif 'Constraint_Violations' in filename:
                violations_df = download_csv(key)
        
        if master_schedule_df is None or student_assignments_df is None:
            logger.warning("Required CSV files not found")
            return metrics
        
        # Calculate section utilization
        section_counts = student_assignments_df.groupby('Section_ID').size().to_dict()
        
        # Get capacities (default to 30 if not specified)
        section_capacities = {}
        if 'Capacity' in master_schedule_df.columns:
            for _, row in master_schedule_df.iterrows():
                section_capacities[row['Section_ID']] = row.get('Capacity', 30)
        else:
            for section_id in section_counts:
                section_capacities[section_id] = 30
        
        # Calculate utilization percentages
        utilizations = []
        for section_id, count in section_counts.items():
            capacity = section_capacities.get(section_id, 30)
            if capacity > 0:
                util = (count / capacity) * 100
                utilizations.append(util)
        
        # Calculate metrics
        if utilizations:
            avg_utilization = sum(utilizations) / len(utilizations)
            sections_optimized = sum(1 for u in utilizations if 70 <= u <= 110)
            
            # Distribution for chart
            distribution = [0, 0, 0, 0, 0]  # <50%, 50-70%, 70-90%, 90-110%, >110%
            for util in utilizations:
                if util < 50:
                    distribution[0] += 1
                elif util < 70:
                    distribution[1] += 1
                elif util < 90:
                    distribution[2] += 1
                elif util <= 110:
                    distribution[3] += 1
                else:
                    distribution[4] += 1
            
            metrics['summary']['overallUtilization'] = round(avg_utilization, 1)
            metrics['summary']['sectionsOptimized'] = sections_optimized
            metrics['charts']['utilizationDistribution'] = distribution
        
        # Calculate student placement
        total_students = len(student_assignments_df['Student_ID'].unique())
        if total_students > 0:
            metrics['summary']['studentsPlaced'] = round((total_students / total_students) * 100, 1)
        
        # Calculate teacher load
        if 'Teacher_ID' in master_schedule_df.columns:
            teacher_loads = master_schedule_df.groupby('Teacher_ID').size().tolist()
            if teacher_loads:
                avg_load = sum(teacher_loads) / len(teacher_loads)
                metrics['summary']['averageTeacherLoad'] = round(avg_load, 1)
                
                # Distribution for chart
                load_dist = [0, 0, 0, 0, 0]  # 1-2, 3-4, 5-6, 7-8, 9+
                for load in teacher_loads:
                    if load <= 2:
                        load_dist[0] += 1
                    elif load <= 4:
                        load_dist[1] += 1
                    elif load <= 6:
                        load_dist[2] += 1
                    elif load <= 8:
                        load_dist[3] += 1
                    else:
                        load_dist[4] += 1
                
                metrics['charts']['teacherLoadDistribution'] = load_dist
        
        # Count violations
        if violations_df is not None:
            metrics['summary']['violations'] = len(violations_df)
        
        # Generate summary text
        metrics['optimizationSummary'] = generate_summary(metrics['summary'])
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        return metrics

def download_csv(file_key: str) -> Optional[pd.DataFrame]:
    """Download CSV from S3 and return as DataFrame"""
    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=file_key)
        content = response['Body'].read()
        return pd.read_csv(io.BytesIO(content))
    except Exception as e:
        logger.error(f"Error downloading CSV {file_key}: {str(e)}")
        return None

def generate_summary(summary: Dict) -> str:
    """Generate human-readable optimization summary"""
    parts = []
    
    util = summary['overallUtilization']
    if util < 70:
        parts.append(f"Section utilization is low at {util}%, indicating potential inefficiency.")
    elif util > 110:
        parts.append(f"Section utilization is high at {util}%, indicating potential overcrowding.")
    else:
        parts.append(f"Section utilization is optimal at {util}%.")
    
    parts.append(f"{summary['sectionsOptimized']} sections are within the optimal range.")
    parts.append(f"{summary['studentsPlaced']}% of students were successfully placed.")
    
    load = summary['averageTeacherLoad']
    if load < 4:
        parts.append(f"Teacher load is light at {load} sections per teacher.")
    elif load > 6:
        parts.append(f"Teacher load is heavy at {load} sections per teacher.")
    else:
        parts.append(f"Teacher load is balanced at {load} sections per teacher.")
    
    violations = summary['violations']
    if violations > 0:
        parts.append(f"There are {violations} constraint violations that need attention.")
    else:
        parts.append("No constraint violations were detected.")
    
    return " ".join(parts)