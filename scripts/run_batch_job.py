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
lambda_client = boto3.client('lambda')

# Get environment variables
INPUT_BUCKET = os.environ.get('S3_INPUT_BUCKET', 'optimo-input-files')
OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'optimo-output-files')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
LICENSE_SECRET_NAME = os.environ.get('LICENSE_SECRET_NAME', 'optimo/gurobi-license')
JOB_COMPLETION_HANDLER = os.environ.get('JOB_COMPLETION_HANDLER', 'optimo-job-completion-handler')

def notify_job_completion(job_id, status):
    """Notify the job completion handler that the job has finished"""
    try:
        logger.info(f"Notifying job completion handler for job {job_id} with status {status}")
        lambda_client.invoke(
            FunctionName=JOB_COMPLETION_HANDLER,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'jobId': job_id,
                'status': status
            })
        )
        logger.info(f"Successfully notified completion handler for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to notify completion handler: {str(e)}")

def get_gurobi_license():
    """Retrieve Gurobi license from AWS Secrets Manager and save to file"""
    try:
        logger.info(f"Retrieving Gurobi license from Secrets Manager: {LICENSE_SECRET_NAME}")
        response = secretsmanager.get_secret_value(SecretId=LICENSE_SECRET_NAME)
        license_content = response['SecretString']
        
        # Create the Gurobi license directory if it doesn't exist
        os.makedirs(os.path.expanduser('~/.gurobi'), exist_ok=True)
        
        # Write the license file
        license_path = os.path.expanduser('~/.gurobi/gurobi.lic')
        with open(license_path, 'w') as f:
            f.write(license_content)
        
        # Set environment variable for Gurobi
        os.environ['GRB_LICENSE_FILE'] = license_path
        logger.info(f"Gurobi license saved to {license_path}")
        
        return license_path
    except Exception as e:
        logger.error(f"Error retrieving Gurobi license: {str(e)}")
        raise

def update_job_status(job_id, status, message=None):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        update_expression = "SET #status = :status, updatedAt = :updatedAt"
        expression_values = {
            ':status': status,
            ':updatedAt': int(datetime.now().timestamp())
        }
        
        if message:
            update_expression += ", statusMessage = :message"
            expression_values[':message'] = message
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expression_values
        )
        logger.info(f"Updated job {job_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")

def download_input_files(job_id, file_keys):
    """Download input files from S3"""
    try:
        input_dir = tempfile.mkdtemp()
        file_paths = {}
        
        for key in file_keys:
            local_path = os.path.join(input_dir, os.path.basename(key))
            s3.download_file(INPUT_BUCKET, key, local_path)
            file_paths[key] = local_path
            logger.info(f"Downloaded {key} to {local_path}")
        
        return input_dir, file_paths
    except Exception as e:
        logger.error(f"Error downloading input files: {str(e)}")
        update_job_status(job_id, "FAILED", f"Failed to download input files: {str(e)}")
        raise

def run_optimization(job_id, input_files):
    """Run the optimization process"""
    try:
        # This is where you would call your optimization code
        # For now, we'll just simulate the optimization process
        logger.info(f"Running optimization for job {job_id}")
        update_job_status(job_id, "RUNNING", "Optimization in progress")
        
        # TODO: Replace with actual optimization code
        # import your_optimization_module
        # results = your_optimization_module.run(input_files)
        
        # Simulate results for now
        output_dir = tempfile.mkdtemp()
        results = {
            'solution': os.path.join(output_dir, 'solution.csv'),
            'report': os.path.join(output_dir, 'report.pdf')
        }
        
        # Create dummy output files
        with open(results['solution'], 'w') as f:
            f.write("teacher,class,period\nTeacher1,Math101,1\nTeacher2,Science101,2\n")
        
        with open(results['report'], 'w') as f:
            f.write("Optimization Report\n\nObjective Value: 95.5\nConstraints Satisfied: 100%\n")
        
        return results
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        update_job_status(job_id, "FAILED", f"Optimization failed: {str(e)}")
        raise

def upload_results(job_id, result_files):
    """Upload result files to S3"""
    try:
        output_keys = {}
        
        for name, local_path in result_files.items():
            key = f"{job_id}/{os.path.basename(local_path)}"
            s3.upload_file(local_path, OUTPUT_BUCKET, key)
            output_keys[name] = key
            logger.info(f"Uploaded {local_path} to {OUTPUT_BUCKET}/{key}")
        
        return output_keys
    except Exception as e:
        logger.error(f"Error uploading results: {str(e)}")
        update_job_status(job_id, "FAILED", f"Failed to upload results: {str(e)}")
        raise

def main():
    """Main function to process the batch job"""
    try:
        # Get job parameters
        job_id = os.environ.get('jobId')
        input_files = os.environ.get('inputFiles', '').split(',')
        
        if not job_id or not input_files:
            logger.error("Missing required parameters: jobId or inputFiles")
            sys.exit(1)
        
        logger.info(f"Starting job {job_id} with input files: {input_files}")
        
        # Get Gurobi license
        license_path = get_gurobi_license()
        
        # Update job status
        update_job_status(job_id, "PROCESSING", "Downloading input files")
        
        # Download input files
        input_dir, file_paths = download_input_files(job_id, input_files)
        
        # Run optimization
        update_job_status(job_id, "RUNNING", "Running optimization")
        result_files = run_optimization(job_id, file_paths)
        
        # Upload results
        update_job_status(job_id, "UPLOADING", "Uploading results")
        output_keys = upload_results(job_id, result_files)
        
        # Update job status with results
        update_job_status(job_id, "COMPLETED", json.dumps({"outputFiles": output_keys}))
        
        # Notify job completion handler
        notify_job_completion(job_id, "COMPLETED")
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        if job_id:
            update_job_status(job_id, "FAILED", f"Job failed: {str(e)}")
            # Notify job completion handler of failure
            notify_job_completion(job_id, "FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
