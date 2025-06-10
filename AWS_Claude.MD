# Comprehensive AWS Setup Guide for OptimoV2

## 1. S3 Buckets Setup

bash
# Create S3 bucket for input files
aws s3api create-bucket \
    --bucket optimo-input-files \
    --region us-west-2 \
    --create-bucket-configuration LocationConstraint=us-west-2

# Create S3 bucket for output files
aws s3api create-bucket \
    --bucket optimo-output-files \
    --region us-west-2 \
    --create-bucket-configuration LocationConstraint=us-west-2

# Configure CORS for input bucket
aws s3api put-bucket-cors --bucket optimo-input-files --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://brettenf-uw.github.io"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'

# Configure CORS for output bucket
aws s3api put-bucket-cors --bucket optimo-output-files --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://brettenf-uw.github.io"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'


## 2. IAM Roles and Policies Setup

bash
# Create IAM role for Lambda functions
aws iam create-role \
    --role-name optimo-lambda-role \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }'

# Create IAM role for Batch jobs
aws iam create-role \
    --role-name optimo-batch-role \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "batch.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }'

# Create Lambda policy
aws iam create-policy \
    --policy-name optimo-lambda-policy \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "s3:GetObject",
            "s3:PutObject",
            "s3:ListBucket",
            "s3:DeleteObject"
          ],
          "Resource": [
            "arn:aws:s3:::optimo-input-files",
            "arn:aws:s3:::optimo-input-files/*",
            "arn:aws:s3:::optimo-output-files",
            "arn:aws:s3:::optimo-output-files/*"
          ]
        },
        {
          "Effect": "Allow",
          "Action": [
            "dynamodb:PutItem",
            "dynamodb:GetItem",
            "dynamodb:UpdateItem",
            "dynamodb:DeleteItem",
            "dynamodb:Scan",
            "dynamodb:Query"
          ],
          "Resource": "arn:aws:dynamodb:us-west-2:*:table/optimo-jobs"
        },
        {
          "Effect": "Allow",
          "Action": [
            "batch:SubmitJob",
            "batch:DescribeJobs",
            "batch:TerminateJob"
          ],
          "Resource": "*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          "Resource": "arn:aws:logs:us-west-2:*:*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "lambda:InvokeFunction"
          ],
          "Resource": "arn:aws:lambda:us-west-2:*:function:optimo-*"
        }
      ]
    }'

# Create Batch policy
aws iam create-policy \
    --policy-name optimo-batch-policy \
    --policy-document '{
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
            "arn:aws:s3:::optimo-input-files",
            "arn:aws:s3:::optimo-input-files/*",
            "arn:aws:s3:::optimo-output-files",
            "arn:aws:s3:::optimo-output-files/*"
          ]
        },
        {
          "Effect": "Allow",
          "Action": [
            "dynamodb:PutItem",
            "dynamodb:GetItem",
            "dynamodb:UpdateItem"
          ],
          "Resource": "arn:aws:dynamodb:us-west-2:*:table/optimo-jobs"
        },
        {
          "Effect": "Allow",
          "Action": [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          "Resource": "arn:aws:logs:us-west-2:*:*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "secretsmanager:GetSecretValue"
          ],
          "Resource": "arn:aws:secretsmanager:us-west-2:*:secret:optimo/gurobi-license*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "lambda:InvokeFunction"
          ],
          "Resource": "arn:aws:lambda:us-west-2:*:function:optimo-job-completion-handler"
        }
      ]
    }'

# Attach policies to roles
aws iam attach-role-policy \
    --role-name optimo-lambda-role \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/optimo-lambda-policy

aws iam attach-role-policy \
    --role-name optimo-batch-role \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/optimo-batch-policy


## 3. DynamoDB Table Setup

bash
# Create DynamoDB table
aws dynamodb create-table \
    --table-name optimo-jobs \
    --attribute-definitions AttributeName=jobId,AttributeType=S \
    --key-schema AttributeName=jobId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-west-2


## 4. Docker Image for AWS Batch

bash
# Create ECR repository
aws ecr create-repository \
    --repository-name optimo-batch \
    --region us-west-2

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Build Docker image
cd /mnt/c/dev/OptimoV2
docker build -t optimo-batch:latest .

# Tag and push image
docker tag optimo-batch:latest ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:latest
docker push ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:latest


## 5. AWS Batch Configuration

bash
# Create compute environment
aws batch create-compute-environment \
    --compute-environment-name optimo-compute-env \
    --type MANAGED \
    --state ENABLED \
    --compute-resources '{
      "type": "SPOT",
      "allocationStrategy": "SPOT_CAPACITY_OPTIMIZED",
      "minvCpus": 0,
      "maxvCpus": 96,
      "instanceTypes": ["c5.24xlarge"],
      "subnets": ["subnet-XXXXXXXX", "subnet-YYYYYYYY"],
      "securityGroupIds": ["sg-ZZZZZZZZ"],
      "instanceRole": "ecsInstanceRole",
      "spotIamFleetRole": "arn:aws:iam::ACCOUNT_ID:role/AmazonEC2SpotFleetRole"
    }' \
    --service-role arn:aws:iam::ACCOUNT_ID:role/service-role/AWSBatchServiceRole \
    --region us-west-2

# Create job queue
aws batch create-job-queue \
    --job-queue-name optimo-job-queue \
    --state ENABLED \
    --priority 1 \
    --compute-environment-order order=1,computeEnvironment=optimo-compute-env \
    --region us-west-2

# Create job definition
aws batch register-job-definition \
    --job-definition-name optimo-job-updated \
    --type container \
    --container-properties '{
      "image": "ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:latest",
      "vcpus": 96,
      "memory": 140000,
      "command": [],
      "jobRoleArn": "arn:aws:iam::ACCOUNT_ID:role/optimo-batch-role",
      "environment": [
        {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files"},
        {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"},
        {"name": "DYNAMODB_TABLE", "value": "optimo-jobs"},
        {"name": "JOB_COMPLETION_HANDLER", "value": "optimo-job-completion-handler"}
      ]
    }' \
    --region us-west-2


## 6. Gurobi License in Secrets Manager

bash
# Create secret for Gurobi license
aws secretsmanager create-secret \
    --name optimo/gurobi-license \
    --description "Gurobi license for OptimoV2" \
    --secret-string "YOUR_GUROBI_LICENSE_CONTENT" \
    --region us-west-2


## 7. Lambda Functions

### Job Submission Lambda

bash
# Create job_submission.py
cat > job_submission.py << 'EOL'
import json
import boto3
import os
import uuid
import time
import decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job-updated')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get input files from request
        input_files = body.get('files', [])
        parameters = body.get('parameters', {})
        
        print(f"Input files: {input_files}")
        print(f"Parameters: {parameters}")
        
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
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Convert float values to Decimal for DynamoDB
        if parameters:
            for key, value in parameters.items():
                if isinstance(value, float):
                    parameters[key] = decimal.Decimal(str(value))
        
        # Check if there are any running or submitted jobs
        table = dynamodb.Table(TABLE_NAME)
        running_jobs = table.scan(
            FilterExpression=Attr('status').eq('RUNNING') | Attr('status').eq('SUBMITTED')
        )
        
        # Filter out jobs that don't have a batchJobId (truly running jobs)
        running_jobs_with_batch = [job for job in running_jobs['Items'] if 'batchJobId' in job]
        
        # Determine job status and position
        timestamp = int(time.time())
        status = 'SUBMITTED'
        position = 0
        batch_job_id = None
        
        if running_jobs_with_batch:
            # If there are running jobs, queue this job
            status = 'QUEUED'
            position = len(running_jobs_with_batch)
        else:
            # No running jobs, submit to AWS Batch immediately
            batch_job = batch.submit_job(
                jobName=f'optimo-job-{job_id}',
                jobQueue=JOB_QUEUE,
                jobDefinition=JOB_DEFINITION,
                containerOverrides={
                    'environment': [
                        {
                            'name': 'jobId',
                            'value': job_id
                        },
                        {
                            'name': 'inputFiles',
                            'value': ','.join(input_files)
                        }
                    ]
                }
            )
            batch_job_id = batch_job['jobId']
        
        # Store job information in DynamoDB
        item = {
            'jobId': job_id,
            'status': status,
            'submittedAt': timestamp,
            'queuedAt': timestamp,
            'inputFiles': input_files,
            'position': position
        }
        
        if batch_job_id:
            item['batchJobId'] = batch_job_id
        
        if parameters:
            item['parameters'] = parameters
        
        print(f"Saving item to DynamoDB: {json.dumps(item, cls=DecimalEncoder)}")
        table.put_item(Item=item)
        
        # Return job ID to client
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': status,
                'position': position,
                'submittedAt': timestamp
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
EOL

# Create zip file
zip job_submission.zip job_submission.py

# Create Lambda function
aws lambda create-function \
    --function-name optimo-job-submission \
    --runtime python3.9 \
    --handler job_submission.lambda_handler \
    --role arn:aws:iam::ACCOUNT_ID:role/optimo-lambda-role \
    --zip-file fileb://job_submission.zip \
    --environment "Variables={DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-updated}" \
    --timeout 10 \
    --memory-size 128 \
    --region us-west-2


### Job Manager Lambda

bash
# Create job_manager.py
cat > job_manager.py << 'EOL'
import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
import decimal
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job-updated')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check for running jobs
        table = dynamodb.Table(TABLE_NAME)
        running_jobs = table.scan(
            FilterExpression=Attr('status').eq('RUNNING') | Attr('status').eq('SUBMITTED')
        )
        
        # Filter out jobs that don't have a batchJobId (truly running jobs)
        running_jobs_with_batch = [job for job in running_jobs['Items'] if 'batchJobId' in job]
        
        # If there are running jobs, don't start a new one
        if running_jobs_with_batch:
            print(f"There are already {len(running_jobs_with_batch)} running jobs. Not starting a new one.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No action taken, jobs already running'
                })
            }
        
        # Look for queued jobs
        queued_jobs = table.scan(
            FilterExpression=Attr('status').eq('QUEUED')
        )
        
        if not queued_jobs['Items']:
            print("No queued jobs found.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No queued jobs found'
                })
            }
        
        # Sort by position and timestamp
        sorted_jobs = sorted(queued_jobs['Items'], key=lambda x: (x.get('position', 999), x.get('queuedAt', 0)))
        
        if not sorted_jobs:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No jobs to process'
                })
            }
        
        # Get the next job
        next_job = sorted_jobs[0]
        job_id = next_job['jobId']
        input_files = next_job.get('inputFiles', [])
        
        print(f"Starting job {job_id}")
        
        # Submit to AWS Batch
        batch_job = batch.submit_job(
            jobName=f'optimo-job-{job_id}',
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEFINITION,
            containerOverrides={
                'environment': [
                    {
                        'name': 'jobId',
                        'value': job_id
                    },
                    {
                        'name': 'inputFiles',
                        'value': ','.join(input_files)
                    }
                ]
            }
        )
        
        # Update job status in DynamoDB
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, batchJobId = :batchJobId, startedAt = :startedAt",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SUBMITTED',
                ':batchJobId': batch_job['jobId'],
                ':startedAt': int(datetime.now().timestamp())
            }
        )
        
        # Update positions of remaining queued jobs
        for i, job in enumerate(sorted_jobs[1:]):
            table.update_item(
                Key={'jobId': job['jobId']},
                UpdateExpression="SET #position = :position",
                ExpressionAttributeNames={'#position': 'position'},
                ExpressionAttributeValues={
                    ':position': i
                }
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Started job {job_id}',
                'jobId': job_id,
                'batchJobId': batch_job['jobId']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
EOL

# Create zip file
zip job_manager.zip job_manager.py

# Create Lambda function
aws lambda create-function \
    --function-name optimo-job-manager \
    --runtime python3.9 \
    --handler job_manager.lambda_handler \
    --role arn:aws:iam::ACCOUNT_ID:role/optimo-lambda-role \
    --zip-file fileb://job_manager.zip \
    --environment "Variables={DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-updated}" \
    --timeout 30 \
    --memory-size 128 \
    --region us-west-2


### Job Completion Handler Lambda

bash
# Create job_completion_handler.py
cat > job_completion_handler.py << 'EOL'
import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
import decimal
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')
lambda_client = boto3.client('lambda')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')
JOB_QUEUE = os.environ.get('JOB_QUEUE', 'optimo-job-queue')
JOB_DEFINITION = os.environ.get('JOB_DEFINITION', 'optimo-job-updated')
JOB_MANAGER_FUNCTION = os.environ.get('JOB_MANAGER_FUNCTION', 'optimo-job-manager')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Get job ID from event
        job_id = event.get('jobId')
        status = event.get('status', 'COMPLETED')  # Default to COMPLETED if not specified
        
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing jobId parameter'
                })
            }
        
        # Update job status in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, completedAt = :completedAt",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':completedAt': int(datetime.now().timestamp())
            }
        )
        
        # Check for queued jobs
        queued_jobs = table.scan(
            FilterExpression=Attr('status').eq('QUEUED')
        )
        
        if not queued_jobs['Items']:
            print("No queued jobs found.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Job completed, no queued jobs found'
                })
            }
        
        # If there are queued jobs, invoke the job manager to start the next one
        print(f"Found {len(queued_jobs['Items'])} queued jobs. Invoking job manager.")
        lambda_client.invoke(
            FunctionName=JOB_MANAGER_FUNCTION,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'source': 'job_completion',
                'jobId': job_id
            })
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Job {job_id} marked as {status}, job manager invoked'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
EOL

# Create zip file
zip job_completion_handler.zip job_completion_handler.py

# Create Lambda function
aws lambda create-function \
    --function-name optimo-job-completion-handler \
    --runtime python3.9 \
    --handler job_completion_handler.lambda_handler \
    --role arn:aws:iam::ACCOUNT_ID:role/optimo-lambda-role \
    --zip-file fileb://job_completion_handler.zip \
    --environment "Variables={DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-updated,JOB_MANAGER_FUNCTION=optimo-job-manager}" \
    --timeout 30 \
    --memory-size 128 \
    --region us-west-2


### Upload Handler Lambda

bash
# Create upload_handler.py
cat > upload_handler.py << 'EOL'
import json
import boto3
import os
import uuid
from datetime import datetime

# Initialize S3 client
s3 = boto3.client('s3')

# Get environment variables
BUCKET_NAME = os.environ.get('S3_BUCKET', 'optimo-input-files')
UPLOAD_PREFIX = os.environ.get('UPLOAD_PREFIX', 'uploads/')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get file name and type from request
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        if not file_name or not file_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing fileName or fileType'
                })
            }
        
        # Generate a unique file key
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_key = f"{UPLOAD_PREFIX}{timestamp}-{file_name}"
        
        # Generate presigned URL for upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_key,
                'ContentType': file_type
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        # Return presigned URL to client
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'fileKey': file_key
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
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
EOL

# Create zip file
zip upload_handler.zip upload_handler.py

# Create Lambda function
aws lambda create-function \
    --function-name optimo-upload-handler \
    --runtime python3.9 \
    --handler upload_handler.lambda_handler \
    --role arn:aws:iam::ACCOUNT_ID:role/optimo-lambda-role \
    --zip-file fileb://upload_handler.zip \
    --environment "Variables={S3_BUCKET=optimo-input-files,UPLOAD_PREFIX=uploads/}" \
    --timeout 10 \
    --memory-size 128 \
    --region us-west-2


### Job Status Lambda

bash
# Create job_status.py
cat > job_status.py << 'EOL'
import json
import boto3
import os
import decimal
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
batch = boto3.client('batch')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'optimo-jobs')

# Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 != 0 else int(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        # Parse path parameters
        path_parameters = event.get('pathParameters', {})
        job_id = path_parameters.get('jobId')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing jobId parameter'
                })
            }
        
        # Get job details from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*