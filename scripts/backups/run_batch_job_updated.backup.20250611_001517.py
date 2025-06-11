#!/usr/bin/env python3
import os
import sys
import json
import boto3
import logging
import tempfile
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('optimo-batch')

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secretsmanager = boto3.client('secretsmanager')

# Get environment variables
INPUT_BUCKET = os.environ.get('S3_INPUT_BUCKET', 'optimo-input-files')
OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'optimo-output-files')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
LICENSE_SECRET_NAME = os.environ.get('LICENSE_SECRET_NAME', 'optimo/gurobi-license')

# Get job-specific environment variables
JOB_ID = os.environ.get('JOB_ID')
STUDENT_INFO_KEY = os.environ.get('STUDENT_INFO_KEY')
STUDENT_PREFERENCES_KEY = os.environ.get('STUDENT_PREFERENCES_KEY')
TEACHER_INFO_KEY = os.environ.get('TEACHER_INFO_KEY')
TEACHER_UNAVAILABILITY_KEY = os.environ.get('TEACHER_UNAVAILABILITY_KEY')
SECTIONS_INFO_KEY = os.environ.get('SECTIONS_INFO_KEY')
PERIOD_KEY = os.environ.get('PERIOD_KEY', '')

# Get optimization parameters
MAX_ITERATIONS = int(os.environ.get('MAX_ITERATIONS', '3'))
MIN_UTILIZATION = float(os.environ.get('MIN_UTILIZATION', '0.7'))
MAX_UTILIZATION = float(os.environ.get('MAX_UTILIZATION', '1.15'))
OPTIMAL_RANGE_MIN = float(os.environ.get('OPTIMAL_RANGE_MIN', '0.8'))
OPTIMAL_RANGE_MAX = float(os.environ.get('OPTIMAL_RANGE_MAX', '1.0'))

def get_gurobi_license():
    """Retrieve Gurobi license from AWS Secrets Manager and save to file"""
    try:
        logger.info(f"Retrieving Gurobi license from Secrets Manager: {LICENSE_SECRET_NAME}")
        response = secretsmanager.get_secret_value(SecretId=LICENSE_SECRET_NAME)
        license_content = response['SecretString']
        
        # Save to default Gurobi license location
        license_path = os.path.expanduser('~/.gurobi/gurobi.lic')
        os.makedirs(os.path.dirname(license_path), exist_ok=True)
        
        with open(license_path, 'w') as f:
            f.write(license_content)
        
        logger.info(f"Gurobi license saved to {license_path}")
        return license_path
    except Exception as e:
        logger.error(f"Error retrieving Gurobi license: {str(e)}")
        raise

def update_job_status(job_id, status, message=None, progress=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        update_expr = 'SET #status = :status'
        expression_values = {':status': status}
        expression_names = {'#status': 'status'}
        
        if message:
            update_expr += ', currentStep = :message'
            expression_values[':message'] = message
        
        if progress is not None:
            update_expr += ', progress = :progress'
            expression_values[':progress'] = progress
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        logger.info(f"Updated job {job_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")

def download_input_files():
    """Download input files from S3"""
    try:
        input_dir = tempfile.mkdtemp()
        file_paths = {}
        
        # Map environment variables to file paths
        file_mappings = {
            'student_info': STUDENT_INFO_KEY,
            'student_preferences': STUDENT_PREFERENCES_KEY,
            'teacher_info': TEACHER_INFO_KEY,
            'teacher_unavailability': TEACHER_UNAVAILABILITY_KEY,
            'sections_info': SECTIONS_INFO_KEY,
            'period': PERIOD_KEY
        }
        
        for file_type, s3_key in file_mappings.items():
            if s3_key:  # Only download if key exists
                local_path = os.path.join(input_dir, f"{file_type}.csv")
                s3.download_file(INPUT_BUCKET, s3_key, local_path)
                file_paths[file_type] = local_path
                logger.info(f"Downloaded {s3_key} to {local_path}")
        
        return input_dir, file_paths
    except Exception as e:
        logger.error(f"Error downloading input files: {str(e)}")
        update_job_status(JOB_ID, "FAILED", f"Failed to download input files: {str(e)}")
        raise

def run_optimization(file_paths):
    """Run the optimization process"""
    try:
        # Import and run the pipeline
        sys.path.append('/app')
        from src.pipeline.runner import OptimizationPipeline
        
        # Create pipeline configuration
        config = {
            'max_iterations': MAX_ITERATIONS,
            'min_utilization': MIN_UTILIZATION,
            'max_utilization': MAX_UTILIZATION,
            'optimal_range_min': OPTIMAL_RANGE_MIN,
            'optimal_range_max': OPTIMAL_RANGE_MAX,
            'job_id': JOB_ID,
            'aws_region': AWS_REGION,
            'dynamodb_table': DYNAMODB_TABLE
        }
        
        # Run pipeline
        pipeline = OptimizationPipeline(config)
        result_files = pipeline.run(file_paths)
        
        return result_files
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        update_job_status(JOB_ID, "FAILED", f"Optimization failed: {str(e)}")
        raise

def upload_results(result_files):
    """Upload result files to S3"""
    try:
        output_keys = {}
        
        for filename, filepath in result_files.items():
            key = f"jobs/{JOB_ID}/{filename}"
            s3.upload_file(filepath, OUTPUT_BUCKET, key)
            output_keys[filename] = key
            logger.info(f"Uploaded {filename} to s3://{OUTPUT_BUCKET}/{key}")
        
        return output_keys
    except Exception as e:
        logger.error(f"Error uploading results: {str(e)}")
        raise

def main():
    """Main function to process the batch job"""
    try:
        # Validate required environment variables
        if not JOB_ID:
            logger.error("Missing required environment variable: JOB_ID")
            sys.exit(1)
        
        required_keys = [STUDENT_INFO_KEY, STUDENT_PREFERENCES_KEY, 
                        TEACHER_INFO_KEY, TEACHER_UNAVAILABILITY_KEY, SECTIONS_INFO_KEY]
        
        if not all(required_keys):
            logger.error("Missing required file keys in environment variables")
            sys.exit(1)
        
        logger.info(f"Starting job {JOB_ID}")
        logger.info(f"Configuration: iterations={MAX_ITERATIONS}, utilization={MIN_UTILIZATION}-{MAX_UTILIZATION}")
        
        # Get Gurobi license
        license_path = get_gurobi_license()
        
        # Update job status
        update_job_status(JOB_ID, "PROCESSING", "Downloading input files", 10)
        
        # Download input files
        input_dir, file_paths = download_input_files()
        
        # Run optimization
        update_job_status(JOB_ID, "RUNNING", "Running optimization", 20)
        result_files = run_optimization(file_paths)
        
        # Upload results
        update_job_status(JOB_ID, "UPLOADING", "Uploading results", 90)
        output_keys = upload_results(result_files)
        
        # Update job status with results
        update_job_status(JOB_ID, "SUCCEEDED", "Job completed successfully", 100)
        
        logger.info(f"Job {JOB_ID} completed successfully")
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        if JOB_ID:
            update_job_status(JOB_ID, "FAILED", f"Job failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()