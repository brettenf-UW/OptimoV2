#!/usr/bin/env python3
"""
Direct job submission test - bypasses API to test Batch directly
"""

import boto3
import os
import uuid
from datetime import datetime

# Configuration
REGION = "us-west-2"
S3_INPUT_BUCKET = "optimo-input-files-v2"
S3_OUTPUT_BUCKET = "optimo-output-files"
DYNAMODB_TABLE = "optimo-jobs"
JOB_QUEUE = "optimo-job-queue"
JOB_DEFINITION = "optimo-job-def-v9"

# AWS Clients
s3 = boto3.client('s3', region_name=REGION)
batch = boto3.client('batch', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def upload_test_files_direct():
    """Upload test files directly to S3 with proper structure"""
    print("📤 Uploading test files directly to S3...")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    print(f"Job ID: {job_id}")
    
    # Test files
    test_files = {
        'Period.csv': 'data/base/Period.csv',
        'Sections_Information.csv': 'data/base/Sections_Information.csv',
        'Student_Info.csv': 'data/base/Student_Info.csv',
        'Student_Preference_Info.csv': 'data/base/Student_Preference_Info.csv',
        'Teacher_Info.csv': 'data/base/Teacher_Info.csv',
        'Teacher_unavailability.csv': 'data/base/Teacher_unavailability.csv'
    }
    
    # Upload files to job-specific folder
    for filename, filepath in test_files.items():
        if os.path.exists(filepath):
            s3_key = f"{job_id}/{filename}"
            try:
                s3.upload_file(filepath, S3_INPUT_BUCKET, s3_key)
                print(f"✅ Uploaded to s3://{S3_INPUT_BUCKET}/{s3_key}")
            except Exception as e:
                print(f"❌ Failed to upload {filepath}: {e}")
                return None
    
    return job_id

def submit_batch_job_direct(job_id):
    """Submit job directly to Batch"""
    print(f"\n📨 Submitting Batch job directly...")
    
    # Environment variables for the job
    environment = [
        {'name': 'JOB_ID', 'value': job_id},
        {'name': 'S3_INPUT_BUCKET', 'value': S3_INPUT_BUCKET},
        {'name': 'S3_OUTPUT_BUCKET', 'value': S3_OUTPUT_BUCKET},
        {'name': 'DYNAMODB_TABLE', 'value': DYNAMODB_TABLE},
        {'name': 'MAX_ITERATIONS', 'value': '1'},
        {'name': 'MIN_UTILIZATION', 'value': '0.7'},
        {'name': 'MAX_UTILIZATION', 'value': '1.15'},
        {'name': 'OPTIMAL_RANGE_MIN', 'value': '0.8'},
        {'name': 'OPTIMAL_RANGE_MAX', 'value': '1.0'}
    ]
    
    try:
        # Submit to Batch
        response = batch.submit_job(
            jobName=f'optimo-job-{job_id}',
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEFINITION,
            containerOverrides={'environment': environment}
        )
        
        batch_job_id = response['jobId']
        print(f"✅ Batch job submitted: {batch_job_id}")
        
        # Create DynamoDB entry
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item={
            'jobId': job_id,
            'batchJobId': batch_job_id,
            'status': 'SUBMITTED',
            'submittedAt': int(datetime.now().timestamp()),
            'inputBucket': S3_INPUT_BUCKET,
            'outputBucket': S3_OUTPUT_BUCKET
        })
        
        return batch_job_id
        
    except Exception as e:
        print(f"❌ Batch submission failed: {e}")
        return None

def monitor_batch_job(batch_job_id):
    """Monitor Batch job status"""
    print(f"\n👀 Monitoring Batch job {batch_job_id}...")
    
    import time
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < 600:  # 10 minute timeout
        try:
            response = batch.describe_jobs(jobs=[batch_job_id])
            if response['jobs']:
                job = response['jobs'][0]
                status = job['status']
                
                if status != last_status:
                    print(f"📊 Status: {status}")
                    last_status = status
                    
                    # Print additional info for certain statuses
                    if status == 'FAILED':
                        print(f"❌ Status reason: {job.get('statusReason', 'Unknown')}")
                        if 'container' in job:
                            print(f"Exit code: {job['container'].get('exitCode', 'N/A')}")
                            log_stream = job['container'].get('logStreamName')
                            if log_stream:
                                print(f"Log stream: {log_stream}")
                    
                if status in ['SUCCEEDED', 'FAILED']:
                    return job
                
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(10)
    
    print("⏱️ Timeout")
    return None

def main():
    """Main test function"""
    print("🧪 Direct Batch Job Test")
    print("=" * 50)
    
    # Upload files
    job_id = upload_test_files_direct()
    if not job_id:
        print("❌ Failed to upload files")
        return
    
    # Submit job
    batch_job_id = submit_batch_job_direct(job_id)
    if not batch_job_id:
        print("❌ Failed to submit job")
        return
    
    # Monitor job
    result = monitor_batch_job(batch_job_id)
    if result and result['status'] == 'SUCCEEDED':
        print(f"\n🎉 SUCCESS! Job completed!")
        print(f"Check results at: s3://{S3_OUTPUT_BUCKET}/{job_id}/")
    else:
        print(f"\n❌ Job failed or timed out")
        if result:
            print(f"Final status: {result['status']}")
            print("\nRun this command to see logs:")
            if 'container' in result:
                log_stream = result['container'].get('logStreamName')
                if log_stream:
                    print(f"aws logs get-log-events --log-group-name /aws/batch/job --log-stream-name '{log_stream}' --region {REGION}")

if __name__ == "__main__":
    main()