# Add this to your batch job script (run_batch_job.py)
import boto3
import os
import json

def notify_job_completion(job_id, status):
    """Notify the job completion handler that the job has finished"""
    lambda_client = boto3.client('lambda')
    
    try:
        lambda_client.invoke(
            FunctionName='optimo-job-completion-handler',
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'jobId': job_id,
                'status': status
            })
        )
        print(f"Successfully notified completion handler for job {job_id} with status {status}")
    except Exception as e:
        print(f"Failed to notify completion handler: {str(e)}")

# At the end of your batch job script:
try:
    # Your optimization code here
    # ...
    
    # If successful:
    notify_job_completion(os.environ.get('jobId'), 'COMPLETED')
except Exception as e:
    print(f"Job failed: {str(e)}")
    notify_job_completion(os.environ.get('jobId'), 'FAILED')
