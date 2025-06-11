#!/usr/bin/env python3
import os
import sys
import json
import boto3
import logging
import tempfile
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('optimo-batch')

# Get environment variables
INPUT_BUCKET = os.environ.get('S3_INPUT_BUCKET', 'optimo-input-files-v2')
OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'optimo-output-files')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
LICENSE_SECRET_NAME = os.environ.get('LICENSE_SECRET_NAME', 'optimo/gurobi-license')

# Set AWS_DEFAULT_REGION for boto3
os.environ['AWS_DEFAULT_REGION'] = AWS_REGION

# Initialize AWS clients with explicit region
s3 = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
secretsmanager = boto3.client('secretsmanager', region_name=AWS_REGION)

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
        
        # Also save to /opt/gurobi/gurobi.lic for compatibility
        alt_license_path = '/opt/gurobi/gurobi.lic'
        os.makedirs(os.path.dirname(alt_license_path), exist_ok=True)
        with open(alt_license_path, 'w') as f:
            f.write(license_content)
        
        # Set environment variable
        os.environ['GRB_LICENSE_FILE'] = license_path
        
        logger.info(f"Gurobi license saved to {license_path} and {alt_license_path}")
        return license_path
    except Exception as e:
        logger.error(f"Error retrieving Gurobi license: {str(e)}")
        # Try to use existing license if available
        if os.path.exists('/opt/gurobi/gurobi.lic'):
            logger.info("Using existing Gurobi license at /opt/gurobi/gurobi.lic")
            os.environ['GRB_LICENSE_FILE'] = '/opt/gurobi/gurobi.lic'
            return '/opt/gurobi/gurobi.lic'
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
    """Download input files from S3 using environment variable keys"""
    try:
        input_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {input_dir}")
        
        # Map environment variables to local filenames
        file_mappings = {
            STUDENT_INFO_KEY: 'Student_Info.csv',
            STUDENT_PREFERENCES_KEY: 'Student_Preference_Info.csv',
            TEACHER_INFO_KEY: 'Teacher_Info.csv',
            TEACHER_UNAVAILABILITY_KEY: 'Teacher_unavailability.csv',
            SECTIONS_INFO_KEY: 'Sections_Information.csv',
            PERIOD_KEY: 'Period.csv' if PERIOD_KEY else None
        }
        
        # Download each file using the provided S3 keys
        for s3_key, local_filename in file_mappings.items():
            if s3_key and local_filename:
                local_path = os.path.join(input_dir, local_filename)
                logger.info(f"Downloading s3://{INPUT_BUCKET}/{s3_key} to {local_path}")
                
                try:
                    s3.download_file(INPUT_BUCKET, s3_key, local_path)
                    logger.info(f"Successfully downloaded {local_filename}")
                except Exception as e:
                    logger.error(f"Failed to download {s3_key}: {str(e)}")
                    raise
        
        # If PERIOD_KEY is not provided, create a default Period.csv
        period_path = os.path.join(input_dir, 'Period.csv')
        if not os.path.exists(period_path):
            logger.info("Creating default Period.csv")
            with open(period_path, 'w') as f:
                f.write("Period,Start_Time,End_Time\n")
                f.write("1,08:00,09:00\n")
                f.write("2,09:00,10:00\n")
                f.write("3,10:00,11:00\n")
                f.write("4,11:00,12:00\n")
                f.write("5,13:00,14:00\n")
                f.write("6,14:00,15:00\n")
        
        # Verify all required files exist
        required_files = ['Student_Info.csv', 'Student_Preference_Info.csv', 
                         'Teacher_Info.csv', 'Teacher_unavailability.csv', 
                         'Sections_Information.csv', 'Period.csv']
        
        for filename in required_files:
            filepath = os.path.join(input_dir, filename)
            if not os.path.exists(filepath):
                raise Exception(f"Required file {filename} not found after download")
            logger.info(f"Verified {filename} exists")
        
        return input_dir
    except Exception as e:
        logger.error(f"Error downloading input files: {str(e)}")
        update_job_status(JOB_ID, "FAILED", f"Failed to download input files: {str(e)}")
        raise

def run_optimization(input_dir):
    """Run the optimization process using subprocess"""
    try:
        # Build command to run the pipeline
        cmd = [
            'python', '/app/scripts/run_pipeline.py',
            '--data-dir', input_dir,
            '--config', '/app/config/settings.yaml',
            '--api-key', os.environ.get('GEMINI_API_KEY', ''),
            '--max-iterations', str(MAX_ITERATIONS),
            '--job-id', JOB_ID,
            '--aws-region', AWS_REGION,
            '--dynamodb-table', DYNAMODB_TABLE
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the pipeline
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info("Pipeline output:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("Pipeline stderr:")
            logger.warning(result.stderr)
        
        # Find output directory (should be created by the pipeline)
        output_dir = None
        for line in result.stdout.split('\n'):
            if 'Output directory:' in line:
                output_dir = line.split('Output directory:')[1].strip()
                break
        
        if not output_dir:
            # Try to find the most recent runs directory
            runs_dir = os.path.join(os.path.dirname(input_dir), 'runs')
            if os.path.exists(runs_dir):
                subdirs = [d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))]
                if subdirs:
                    subdirs.sort()
                    output_dir = os.path.join(runs_dir, subdirs[-1])
        
        if not output_dir or not os.path.exists(output_dir):
            raise Exception("Could not find output directory from pipeline")
        
        logger.info(f"Output directory: {output_dir}")
        return output_dir
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline failed with exit code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        update_job_status(JOB_ID, "FAILED", f"Pipeline failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        update_job_status(JOB_ID, "FAILED", f"Optimization failed: {str(e)}")
        raise

def upload_results(output_dir):
    """Upload result files to S3"""
    try:
        # Find and upload result files
        result_files = [
            'MasterSchedule.csv',
            'StudentAssignments.csv', 
            'TeacherSchedule.csv',
            'ConstraintViolations.csv'
        ]
        
        uploaded_files = []
        
        for filename in result_files:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                key = f"jobs/{JOB_ID}/{filename}"
                logger.info(f"Uploading {filename} to s3://{OUTPUT_BUCKET}/{key}")
                s3.upload_file(filepath, OUTPUT_BUCKET, key)
                uploaded_files.append(key)
            else:
                logger.warning(f"Result file {filename} not found")
        
        # Also upload any iteration summary files
        for filename in os.listdir(output_dir):
            if filename.startswith('iteration_') and filename.endswith('_summary.json'):
                filepath = os.path.join(output_dir, filename)
                key = f"jobs/{JOB_ID}/{filename}"
                logger.info(f"Uploading {filename} to s3://{OUTPUT_BUCKET}/{key}")
                s3.upload_file(filepath, OUTPUT_BUCKET, key)
                uploaded_files.append(key)
        
        if not uploaded_files:
            raise Exception("No result files were uploaded")
        
        return uploaded_files
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
        
        # Check if we have the API key
        if not os.environ.get('GEMINI_API_KEY'):
            logger.error("Missing required environment variable: GEMINI_API_KEY")
            sys.exit(1)
        
        logger.info(f"Starting job {JOB_ID}")
        logger.info(f"Configuration: iterations={MAX_ITERATIONS}, utilization={MIN_UTILIZATION}-{MAX_UTILIZATION}")
        logger.info(f"Input bucket: {INPUT_BUCKET}")
        logger.info(f"Output bucket: {OUTPUT_BUCKET}")
        
        # Get Gurobi license
        try:
            license_path = get_gurobi_license()
        except Exception as e:
            logger.warning(f"Could not retrieve Gurobi license: {e}")
            logger.info("Continuing with existing license configuration")
        
        # Update job status
        update_job_status(JOB_ID, "PROCESSING", "Downloading input files", 10)
        
        # Download input files
        input_dir = download_input_files()
        
        # Run optimization
        update_job_status(JOB_ID, "RUNNING", "Running optimization", 20)
        output_dir = run_optimization(input_dir)
        
        # Upload results
        update_job_status(JOB_ID, "UPLOADING", "Uploading results", 90)
        uploaded_files = upload_results(output_dir)
        
        # Update job status with results
        update_job_status(JOB_ID, "SUCCEEDED", "Job completed successfully", 100)
        
        logger.info(f"Job {JOB_ID} completed successfully")
        logger.info(f"Uploaded {len(uploaded_files)} files")
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        update_job_status(JOB_ID, "FAILED", str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()