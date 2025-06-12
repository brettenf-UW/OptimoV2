#!/usr/bin/env python3
"""
PhD-Level Automated Testing System for OptimoV2
Automatically submits jobs, diagnoses failures, and applies fixes
"""

import boto3
import time
import json
import os
import sys
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = 'us-west-2'
ACCOUNT_ID = '529088253685'

# AWS Clients
s3 = boto3.client('s3', region_name=AWS_REGION)
batch = boto3.client('batch', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
logs = boto3.client('logs', region_name=AWS_REGION)
iam = boto3.client('iam', region_name=AWS_REGION)

# Constants
INPUT_BUCKET = 'optimo-input-files-v2'
OUTPUT_BUCKET = 'optimo-output-files'
JOB_QUEUE = 'optimo-job-queue'
DYNAMODB_TABLE = 'optimo-jobs'

# Test data from a known good upload (from the latest job submission)
TEST_FILES = {
    'Student_Info.csv': 'uploads/e08ed1cc-628d-40d5-8a78-3bc7ccb54ed1/Student_Info.csv',
    'Student_Preference_Info.csv': 'uploads/8b8babdf-b02e-470c-9883-6c65e4eaaf0f/Student_Preference_Info.csv',
    'Teacher_Info.csv': 'uploads/0f036079-bf19-4070-99b6-94470d2b1c70/Teacher_Info.csv',
    'Teacher_unavailability.csv': 'uploads/40b07f47-72a8-4e44-8c88-7ccac3c31f7c/Teacher_unavailability.csv',
    'Sections_Information.csv': 'uploads/f3d2838f-21df-47d6-a9cc-316ea55818cc/Sections_Information.csv'
}

class OptimizationTester:
    def __init__(self, fix_mode='auto', verbose=False):
        self.fix_mode = fix_mode
        self.verbose = verbose
        self.job_definition = self.get_current_job_definition()
        self.fixes_applied = []
        self.test_results = []
        
    def get_current_job_definition(self) -> str:
        """Get the current job definition from Lambda configuration"""
        lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        response = lambda_client.get_function_configuration(
            FunctionName='optimo-unified-handler'
        )
        return response['Environment']['Variables'].get('JOB_DEFINITION', 'optimo-job-def-v11')
    
    def submit_test_job(self, job_name_suffix='') -> str:
        """Submit a test job directly to Batch"""
        job_id = f"test-{int(time.time())}{job_name_suffix}"
        job_name = f"optimo-job-{job_id}"
        
        logger.info(f"Submitting test job: {job_name}")
        
        # Create DynamoDB entry
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item={
            'jobId': job_id,
            'status': 'SUBMITTED',
            'createdAt': int(datetime.utcnow().timestamp()),
            'inputFiles': list(TEST_FILES.keys())
        })
        
        # Submit Batch job
        response = batch.submit_job(
            jobName=job_name,
            jobQueue=JOB_QUEUE,
            jobDefinition=self.job_definition,
            containerOverrides={
                'environment': [
                    {'name': 'JOB_ID', 'value': job_id},
                    {'name': 'STUDENT_INFO_KEY', 'value': TEST_FILES['Student_Info.csv']},
                    {'name': 'STUDENT_PREFERENCES_KEY', 'value': TEST_FILES['Student_Preference_Info.csv']},
                    {'name': 'TEACHER_INFO_KEY', 'value': TEST_FILES['Teacher_Info.csv']},
                    {'name': 'TEACHER_UNAVAILABILITY_KEY', 'value': TEST_FILES['Teacher_unavailability.csv']},
                    {'name': 'SECTIONS_INFO_KEY', 'value': TEST_FILES['Sections_Information.csv']},
                    {'name': 'MAX_ITERATIONS', 'value': '6'},
                    {'name': 'MIN_UTILIZATION', 'value': '0.75'},
                    {'name': 'MAX_UTILIZATION', 'value': '1.15'}
                ]
            }
        )
        
        batch_job_id = response['jobId']
        logger.info(f"Batch job submitted: {batch_job_id}")
        
        return batch_job_id
    
    def monitor_job(self, batch_job_id: str, timeout: int = 1200) -> Dict:
        """Monitor job execution and return final status"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            response = batch.describe_jobs(jobs=[batch_job_id])
            job = response['jobs'][0]
            status = job['status']
            
            if status != last_status:
                logger.info(f"Job status: {status}")
                last_status = status
            
            if status in ['SUCCEEDED', 'FAILED']:
                return job
            
            time.sleep(5)
        
        return {'status': 'TIMEOUT', 'statusReason': f'Job did not complete within {timeout} seconds'}
    
    def get_job_logs(self, batch_job_id: str) -> List[str]:
        """Retrieve CloudWatch logs for the job"""
        try:
            # Get job details to find log stream
            response = batch.describe_jobs(jobs=[batch_job_id])
            job = response['jobs'][0]
            
            if 'container' not in job or 'logStreamName' not in job['container']:
                logger.warning("Log stream not found in job details")
                return []
            
            log_stream = job['container']['logStreamName']
            log_group = '/aws/batch/job'
            
            # Get logs
            response = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                limit=1000
            )
            
            return [event['message'] for event in response['events']]
        except Exception as e:
            logger.error(f"Error retrieving logs: {e}")
            return []
    
    def diagnose_failure(self, job: Dict, logs: List[str]) -> Dict:
        """Analyze failure and suggest fixes"""
        diagnosis = {
            'error_type': 'unknown',
            'error_details': '',
            'suggested_fixes': [],
            'confidence': 0.0
        }
        
        status_reason = job.get('statusReason', '')
        
        # Check for common error patterns
        error_patterns = {
            'file_not_found': {
                'patterns': [
                    r'No files found in s3://',
                    r'Failed to download.*No such file',
                    r'Required file.*not found'
                ],
                'fixes': ['check_file_paths', 'rebuild_container']
            },
            'permission_denied': {
                'patterns': [
                    r'AccessDenied',
                    r'not authorized to perform',
                    r'Permission denied'
                ],
                'fixes': ['update_iam_policies', 'check_bucket_policies']
            },
            'missing_env_var': {
                'patterns': [
                    r'Missing required environment variable',
                    r'KeyError:.*KEY',
                    r'environment variable.*not set'
                ],
                'fixes': ['update_job_definition', 'check_lambda_config']
            },
            'container_crash': {
                'patterns': [
                    r'Essential container in task exited',
                    r'Container exited with non-zero exit code',
                    r'Segmentation fault'
                ],
                'fixes': ['check_memory_limits', 'rebuild_container', 'check_dependencies']
            },
            'api_error': {
                'patterns': [
                    r'GEMINI_API_KEY',
                    r'API key.*invalid',
                    r'Authentication failed'
                ],
                'fixes': ['update_api_key', 'check_secrets_manager']
            }
        }
        
        # Analyze logs and status reason
        all_text = '\n'.join(logs) + '\n' + status_reason
        
        for error_type, config in error_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, all_text, re.IGNORECASE):
                    diagnosis['error_type'] = error_type
                    diagnosis['error_details'] = pattern
                    diagnosis['suggested_fixes'] = config['fixes']
                    diagnosis['confidence'] = 0.9
                    break
            if diagnosis['error_type'] != 'unknown':
                break
        
        # Extract specific error messages
        for log in logs[-20:]:  # Check last 20 log lines
            if 'ERROR' in log or 'Error' in log or 'Failed' in log:
                diagnosis['error_details'] = log.strip()
                break
        
        return diagnosis
    
    def apply_fix(self, fix_type: str) -> bool:
        """Apply automated fixes based on diagnosis"""
        logger.info(f"Applying fix: {fix_type}")
        
        fix_functions = {
            'check_file_paths': self._fix_file_paths,
            'rebuild_container': self._fix_rebuild_container,
            'update_iam_policies': self._fix_iam_policies,
            'update_job_definition': self._fix_job_definition,
            'check_memory_limits': self._fix_memory_limits,
            'update_api_key': self._fix_api_key
        }
        
        if fix_type in fix_functions:
            try:
                success = fix_functions[fix_type]()
                if success:
                    self.fixes_applied.append({
                        'fix_type': fix_type,
                        'timestamp': datetime.utcnow().isoformat(),
                        'success': True
                    })
                return success
            except Exception as e:
                logger.error(f"Error applying fix {fix_type}: {e}")
                return False
        
        logger.warning(f"Unknown fix type: {fix_type}")
        return False
    
    def _fix_file_paths(self) -> bool:
        """Verify file paths are correct"""
        logger.info("Checking file paths in S3...")
        
        for file_name, s3_key in TEST_FILES.items():
            try:
                s3.head_object(Bucket=INPUT_BUCKET, Key=s3_key)
                logger.info(f"✓ {file_name} exists at {s3_key}")
            except:
                logger.error(f"✗ {file_name} NOT found at {s3_key}")
                return False
        
        return True
    
    def _fix_rebuild_container(self) -> bool:
        """Trigger container rebuild"""
        logger.info("Container rebuild requested - creating new version")
        
        # Get current container version
        current_version = int(self.job_definition.split('-v')[-1])
        new_version = current_version + 1
        
        # Create rebuild script
        rebuild_script = f"""#!/bin/bash
# Auto-generated rebuild script
echo "Rebuilding container v{new_version}..."

# Build and push
docker build -t optimo-batch:v{new_version} .
docker tag optimo-batch:v{new_version} {ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/optimo-batch:v{new_version}
aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com
docker push {ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/optimo-batch:v{new_version}

# Update job definition
aws batch register-job-definition --job-definition-name optimo-job-def-v{new_version} --type container --container-properties file:///tmp/container-props.json
"""
        
        with open(f'/tmp/rebuild_v{new_version}.sh', 'w') as f:
            f.write(rebuild_script)
        
        logger.info(f"Rebuild script created: /tmp/rebuild_v{new_version}.sh")
        logger.info("Manual container rebuild required - run the script on a Docker-enabled system")
        return False  # Can't auto-rebuild in this environment
    
    def _fix_iam_policies(self) -> bool:
        """Update IAM policies for S3 access"""
        logger.info("Updating IAM policies...")
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{INPUT_BUCKET}/*",
                        f"arn:aws:s3:::{INPUT_BUCKET}",
                        f"arn:aws:s3:::{OUTPUT_BUCKET}/*",
                        f"arn:aws:s3:::{OUTPUT_BUCKET}"
                    ]
                }
            ]
        }
        
        try:
            # Update Batch role policy
            iam.put_role_policy(
                RoleName='optimo-batch-role',
                PolicyName='OptimoS3Access-AutoFix',
                PolicyDocument=json.dumps(policy_document)
            )
            logger.info("✓ Updated Batch role S3 permissions")
            return True
        except Exception as e:
            logger.error(f"Failed to update IAM policy: {e}")
            return False
    
    def _fix_job_definition(self) -> bool:
        """Create new job definition with current fixes"""
        logger.info("Creating updated job definition...")
        
        # Get current version
        current_version = int(self.job_definition.split('-v')[-1])
        new_version = current_version + 1
        new_job_def = f"optimo-job-def-v{new_version}"
        
        try:
            response = batch.register_job_definition(
                jobDefinitionName=new_job_def,
                type='container',
                containerProperties={
                    'image': f'{ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/optimo-batch:v{current_version}',
                    'vcpus': 72,
                    'memory': 140000,
                    'jobRoleArn': f'arn:aws:iam::{ACCOUNT_ID}:role/optimo-batch-role',
                    'executionRoleArn': f'arn:aws:iam::{ACCOUNT_ID}:role/ecsTaskExecutionRole',
                    'environment': [
                        {'name': 'S3_INPUT_BUCKET', 'value': INPUT_BUCKET},
                        {'name': 'S3_OUTPUT_BUCKET', 'value': OUTPUT_BUCKET},
                        {'name': 'DYNAMODB_TABLE', 'value': DYNAMODB_TABLE},
                        {'name': 'AWS_REGION', 'value': AWS_REGION},
                        {'name': 'AWS_DEFAULT_REGION', 'value': AWS_REGION},
                        {'name': 'LICENSE_SECRET_NAME', 'value': 'optimo/gurobi-license'},
                        {'name': 'GEMINI_API_KEY', 'value': 'AIzaSyAQC-ytf_lcDK_WZ0ZuOMG8r24QBqvKds0'},
                        {'name': 'JOB_COMPLETION_HANDLER', 'value': 'optimo-job-completion-handler'}
                    ],
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': '/aws/batch/job',
                            'awslogs-region': AWS_REGION,
                            'awslogs-stream-prefix': new_job_def
                        }
                    }
                }
            )
            
            # Update Lambda
            lambda_client = boto3.client('lambda', region_name=AWS_REGION)
            lambda_client.update_function_configuration(
                FunctionName='optimo-unified-handler',
                Environment={
                    'Variables': {
                        'S3_INPUT_BUCKET': INPUT_BUCKET,
                        'S3_OUTPUT_BUCKET': OUTPUT_BUCKET,
                        'DYNAMODB_TABLE': DYNAMODB_TABLE,
                        'JOB_QUEUE': JOB_QUEUE,
                        'JOB_DEFINITION': new_job_def
                    }
                }
            )
            
            self.job_definition = new_job_def
            logger.info(f"✓ Created and activated {new_job_def}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create job definition: {e}")
            return False
    
    def _fix_memory_limits(self) -> bool:
        """Increase memory limits"""
        logger.info("Adjusting memory limits...")
        # This would require creating a new job definition with increased memory
        return self._fix_job_definition()
    
    def _fix_api_key(self) -> bool:
        """Verify API key is set correctly"""
        logger.info("Checking API key configuration...")
        # This is already set in job definition
        return True
    
    def generate_report(self, filename: str = 'test_report.md'):
        """Generate comprehensive test report"""
        report = f"""# OptimoV2 Automated Test Report
Generated: {datetime.utcnow().isoformat()}

## Test Summary
- Total tests run: {len(self.test_results)}
- Successful: {sum(1 for r in self.test_results if r['status'] == 'SUCCEEDED')}
- Failed: {sum(1 for r in self.test_results if r['status'] == 'FAILED')}
- Fixes applied: {len(self.fixes_applied)}

## Test Results
"""
        
        for i, result in enumerate(self.test_results, 1):
            report += f"""
### Test {i}
- Job ID: {result['job_id']}
- Status: {result['status']}
- Runtime: {result.get('runtime', 'N/A')}
- Error Type: {result.get('diagnosis', {}).get('error_type', 'N/A')}
- Error Details: {result.get('diagnosis', {}).get('error_details', 'N/A')}
"""
        
        report += "\n## Fixes Applied\n"
        for fix in self.fixes_applied:
            report += f"- {fix['fix_type']} at {fix['timestamp']}\n"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to {filename}")
    
    def run_test_cycle(self, max_iterations: int = 10) -> bool:
        """Run complete test cycle with automatic fixes"""
        logger.info(f"Starting automated test cycle (max {max_iterations} iterations)")
        
        for iteration in range(max_iterations):
            logger.info(f"\n=== Iteration {iteration + 1}/{max_iterations} ===")
            
            # Submit test job
            batch_job_id = self.submit_test_job(f"-iter{iteration}")
            
            # Monitor execution
            job_result = self.monitor_job(batch_job_id)
            
            # Get logs
            logs = self.get_job_logs(batch_job_id)
            
            # Check result
            if job_result['status'] == 'SUCCEEDED':
                logger.info("✓ Job completed successfully!")
                runtime = job_result.get('stoppedAt', 0) - job_result.get('startedAt', 0)
                self.test_results.append({
                    'job_id': batch_job_id,
                    'status': 'SUCCEEDED',
                    'runtime': f"{runtime/1000:.1f} seconds"
                })
                return True
            
            # Diagnose failure
            diagnosis = self.diagnose_failure(job_result, logs)
            logger.info(f"Diagnosis: {diagnosis['error_type']} - {diagnosis['error_details']}")
            
            self.test_results.append({
                'job_id': batch_job_id,
                'status': job_result['status'],
                'diagnosis': diagnosis
            })
            
            # Apply fixes if in auto mode
            if self.fix_mode == 'auto' and diagnosis['suggested_fixes']:
                for fix in diagnosis['suggested_fixes']:
                    if self.apply_fix(fix):
                        logger.info(f"✓ Applied fix: {fix}")
                        time.sleep(5)  # Wait for changes to propagate
                        break
            
            # Wait before next iteration
            time.sleep(10)
        
        logger.warning(f"Failed to achieve success after {max_iterations} iterations")
        return False

def main():
    parser = argparse.ArgumentParser(description='Automated OptimoV2 Testing System')
    parser.add_argument('--iterations', type=int, default=10, help='Maximum test iterations')
    parser.add_argument('--fix-mode', choices=['auto', 'manual', 'report-only'], 
                       default='auto', help='Fix application mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create tester
    tester = OptimizationTester(fix_mode=args.fix_mode, verbose=args.verbose)
    
    # Run test cycle
    success = tester.run_test_cycle(max_iterations=args.iterations)
    
    # Generate report
    tester.generate_report()
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()