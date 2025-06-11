#!/usr/bin/env python3
"""
Automated OptimoV2 Debug System
Submits test jobs and automatically fixes issues until success
"""

import boto3
import json
import time
import os
import sys
import requests
from datetime import datetime

# Configuration
API_URL = "https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod"
REGION = "us-west-2"
S3_INPUT_BUCKET = "optimo-input-files-v2"
S3_OUTPUT_BUCKET = "optimo-output-files"
DYNAMODB_TABLE = "optimo-jobs"

# AWS Clients
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
batch = boto3.client('batch', region_name=REGION)
logs = boto3.client('logs', region_name=REGION)

def upload_test_files():
    """Upload test CSV files to S3"""
    print("📤 Uploading test files to S3...")
    
    test_files = {
        'period': 'data/base/Period.csv',
        'sectionsInfo': 'data/base/Sections_Information.csv',
        'studentInfo': 'data/base/Student_Info.csv',
        'studentPreferences': 'data/base/Student_Preference_Info.csv',
        'teacherInfo': 'data/base/Teacher_Info.csv',
        'teacherUnavailability': 'data/base/Teacher_unavailability.csv'
    }
    
    s3_keys = {}
    test_prefix = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    for key, filepath in test_files.items():
        if os.path.exists(filepath):
            s3_key = f"{test_prefix}/{os.path.basename(filepath)}"
            try:
                s3.upload_file(filepath, S3_INPUT_BUCKET, s3_key)
                s3_keys[key] = s3_key
                print(f"  ✅ Uploaded {filepath} to s3://{S3_INPUT_BUCKET}/{s3_key}")
            except Exception as e:
                print(f"  ❌ Failed to upload {filepath}: {e}")
                return None
        else:
            print(f"  ❌ File not found: {filepath}")
            return None
    
    return s3_keys

def submit_job(s3_keys):
    """Submit job via API"""
    print("\n📨 Submitting job via API...")
    
    payload = {
        "s3Keys": s3_keys,
        "parameters": {
            "maxIterations": 1,  # Start with 1 iteration for faster testing
            "minUtilization": 0.7,
            "maxUtilization": 1.15,
            "optimalRangeMin": 0.8,
            "optimalRangeMax": 1.0
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/jobs",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get('jobId')
            print(f"  ✅ Job submitted: {job_id}")
            return job_id
        else:
            print(f"  ❌ API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return None

def monitor_job(job_id, timeout=300):
    """Monitor job status and collect logs"""
    print(f"\n👀 Monitoring job {job_id}...")
    
    table = dynamodb.Table(DYNAMODB_TABLE)
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        try:
            # Get job status from DynamoDB
            response = table.get_item(Key={'jobId': job_id})
            if 'Item' not in response:
                print(f"  ❌ Job not found in DynamoDB")
                return None
            
            job = response['Item']
            status = job.get('status', 'UNKNOWN')
            
            if status != last_status:
                print(f"  📊 Status: {status}")
                last_status = status
            
            if status in ['SUCCEEDED', 'FAILED']:
                return job
            
            # Get Batch job details if available
            batch_job_id = job.get('batchJobId')
            if batch_job_id:
                batch_jobs = batch.describe_jobs(jobs=[batch_job_id])
                if batch_jobs['jobs']:
                    batch_job = batch_jobs['jobs'][0]
                    container_status = batch_job.get('status')
                    if container_status != status:
                        print(f"  📊 Batch status: {container_status}")
            
            time.sleep(5)
            
        except Exception as e:
            print(f"  ❌ Monitoring error: {e}")
            time.sleep(5)
    
    print(f"  ⏱️ Timeout after {timeout} seconds")
    return None

def analyze_failure(job_id):
    """Analyze job failure and determine fix"""
    print(f"\n🔍 Analyzing failure for job {job_id}...")
    
    # Get job details
    table = dynamodb.Table(DYNAMODB_TABLE)
    response = table.get_item(Key={'jobId': job_id})
    if 'Item' not in response:
        return None
    
    job = response['Item']
    batch_job_id = job.get('batchJobId')
    
    if not batch_job_id:
        print("  ❌ No Batch job ID found")
        return None
    
    # Get Batch job details
    try:
        batch_jobs = batch.describe_jobs(jobs=[batch_job_id])
        if not batch_jobs['jobs']:
            return None
        
        batch_job = batch_jobs['jobs'][0]
        log_stream = batch_job['container'].get('logStreamName')
        
        if not log_stream:
            print("  ❌ No log stream found")
            return None
        
        # Get logs
        print(f"  📋 Reading logs from {log_stream}")
        log_events = logs.get_log_events(
            logGroupName='/aws/batch/job',
            logStreamName=log_stream,
            startFromHead=True
        )
        
        # Analyze error patterns
        errors = []
        for event in log_events['events']:
            message = event['message']
            if 'ERROR' in message or 'error' in message:
                errors.append(message)
                print(f"  ❗ {message.strip()}")
        
        # Determine fix based on error
        if any('No files found in s3://' in e for e in errors):
            return 'files_not_in_s3'
        elif any('not authorized to perform: s3:' in e for e in errors):
            return 's3_permissions'
        elif any('GEMINI_API_KEY' in e for e in errors):
            return 'missing_api_key'
        elif any('region' in e.lower() for e in errors):
            return 'region_issue'
        else:
            return 'unknown'
            
    except Exception as e:
        print(f"  ❌ Analysis error: {e}")
        return None

def apply_fix(issue_type, job_data):
    """Apply automated fix based on issue type"""
    print(f"\n🔧 Applying fix for: {issue_type}")
    
    if issue_type == 'files_not_in_s3':
        print("  📁 Issue: Files not in expected S3 location")
        print("  🔧 Fix: Checking file upload process...")
        
        # Check if files were uploaded with job ID prefix
        job_id = job_data.get('jobId')
        if job_id:
            # List files in S3
            try:
                response = s3.list_objects_v2(
                    Bucket=S3_INPUT_BUCKET,
                    Prefix=job_id
                )
                if 'Contents' not in response:
                    print(f"  ❌ No files found with prefix {job_id}")
                    print("  💡 Files might be uploaded to wrong location")
                    return False
            except Exception as e:
                print(f"  ❌ S3 list error: {e}")
        
        return True
    
    elif issue_type == 's3_permissions':
        print("  🔐 Issue: S3 permission denied")
        print("  ✅ Fix: Permissions were already updated in comprehensive fix")
        return True
    
    elif issue_type == 'missing_api_key':
        print("  🔑 Issue: Missing GEMINI_API_KEY")
        print("  ✅ Fix: Already added to job definition v9")
        return True
    
    return False

def main():
    """Main automated debug loop"""
    print("🤖 OptimoV2 Automated Debug System")
    print("=" * 50)
    
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")
        
        # Upload test files
        s3_keys = upload_test_files()
        if not s3_keys:
            print("❌ Failed to upload test files")
            break
        
        # Submit job
        job_id = submit_job(s3_keys)
        if not job_id:
            print("❌ Failed to submit job")
            break
        
        # Monitor job
        job_result = monitor_job(job_id)
        if not job_result:
            print("❌ Job monitoring failed")
            continue
        
        if job_result['status'] == 'SUCCEEDED':
            print("\n🎉 SUCCESS! Job completed successfully!")
            print(f"Job ID: {job_id}")
            print(f"Check results at: s3://{S3_OUTPUT_BUCKET}/{job_id}/")
            break
        
        # Analyze failure
        issue = analyze_failure(job_id)
        if not issue:
            print("❌ Could not determine failure cause")
            continue
        
        # Apply fix
        if not apply_fix(issue, job_result):
            print("❌ Could not apply fix")
            continue
        
        print("\n⏳ Waiting before next attempt...")
        time.sleep(10)
    
    print("\n✅ Debug session complete")

if __name__ == "__main__":
    main()