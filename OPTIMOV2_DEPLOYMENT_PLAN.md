# OptimoV2 Deployment Plan: GitHub Pages + AWS Batch

This guide outlines a streamlined deployment approach for OptimoV2 using GitHub Pages for the frontend and AWS Batch for on-demand optimization processing.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Pages   │────▶│  API Gateway    │────▶│  Lambda         │
│  (React App)    │     │  (REST API)     │     │  (Job Submitter)│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  S3 Buckets     │◀───▶│  AWS Batch      │◀───▶│  CloudWatch     │
│  (Data Storage) │     │  (Optimization) │     │  (Monitoring)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Implementation Steps

### Phase 1: Frontend Setup (GitHub Pages)

#### ✅ **COMPLETED:**
1. **React Application Built**
   - ✅ React app created in `optimo-frontend/` directory
   - ✅ Required dependencies installed (React, axios, Material-UI)
   - ✅ File upload component implemented (`FileUpload.tsx`)
   - ✅ Job status tracking component (`JobStatus.tsx`)
   - ✅ Results display component (`Results.tsx`)
   - ✅ Mock server for development testing (`mock-server.js`)

2. **Local Development Environment**
   - ✅ Development server configured (`npm run dev`)
   - ✅ Mock API endpoints working on port 5000
   - ✅ React app running on port 3000
   - ✅ File upload and job submission tested locally

#### 🔄 **IN PROGRESS:**
3. **GitHub Repository Setup**
   - ✅ Code committed to local repository
   - 🔲 Push to GitHub repository
   - 🔲 Set up GitHub Pages deployment
   - 🔲 Configure build process for production

#### 📋 **NEXT STEPS:**
4. **API Integration Preparation**
   - 🔲 Update API endpoints from mock server to AWS API Gateway URLs
   - 🔲 Implement proper error handling for API failures
   - 🔲 Add loading states and progress indicators
   - 🔲 Configure CORS settings for production

5. **Production Deployment**
   - 🔲 Create GitHub Actions workflow for CI/CD
   - 🔲 Set up automated deployment to GitHub Pages
   - 🔲 Configure custom domain (optional)
   - 🔲 Test production build and deployment

6. **Frontend Enhancements**
   - 🔲 Add file validation (CSV format, required columns)
   - 🔲 Implement drag-and-drop file upload
   - 🔲 Add download functionality for optimization results
   - 🔲 Create user-friendly error messages
   - 🔲 Add utilization summary display in results

#### **Current Status:**
- **Local Development**: ✅ Fully functional
- **Component Library**: ✅ Complete with all required features
- **Testing**: ✅ Manual testing with mock data successful
- **Ready for**: GitHub deployment and AWS integration

### Phase 2: AWS Infrastructure Setup

1. **S3 Buckets**
   - Create input bucket for uploaded files
   - Create output bucket for optimization results
   - Set appropriate CORS policies

2. **IAM Roles & Permissions**
   - Create role for Lambda with S3 access
   - Create role for Batch with S3 access and Gurobi license access

3. **API Gateway**
   - Create REST API with endpoints:
     - `/upload` - For file uploads
     - `/jobs` - For job submission
     - `/status/{jobId}` - For checking job status
     - `/results/{jobId}` - For retrieving results

### Phase 3: AWS Batch Configuration

1. **Create Custom Docker Image**
   - Base image with Python and required dependencies
   - Install Gurobi and configure license
   - Add OptimoV2 application code
   - Push to Amazon ECR

2. **Configure Batch Environment**
   - Create compute environment:
     - On-demand or Spot instances
     - Instance types optimized for Gurobi (m5.2xlarge recommended)
     - Auto-scaling from 0 to desired max
   - Create job queue
   - Define job definition using custom Docker image

### Phase 4: Lambda Functions

1. **Upload Handler**
   - Receive files from frontend
   - Store in S3 input bucket
   - Return presigned URLs or upload tokens

2. **Job Submission Handler**
   - Submit optimization job to AWS Batch
   - Store job metadata in DynamoDB
   - Return job ID to frontend

3. **Status Checker**
   - Query AWS Batch for job status
   - Return progress information to frontend

4. **Results Handler**
   - Generate presigned URLs for result files
   - Return download links to frontend

### Phase 5: Integration and Testing

1. **End-to-End Testing**
   - Test file upload flow
   - Test job submission
   - Test status checking
   - Test results retrieval

2. **Performance Testing**
   - Verify Gurobi optimization performance
   - Test with various school sizes
   - Optimize instance types if needed

## Detailed Implementation Guide

### Step 1: GitHub Pages Setup

```bash
# Initialize React app
npx create-react-app optimo-frontend
cd optimo-frontend

# Install dependencies
npm install axios react-dropzone @mui/material

# Configure for GitHub Pages
npm install gh-pages --save-dev
```

Add to `package.json`:
```json
"homepage": "https://yourusername.github.io/optimo-frontend",
"scripts": {
  "predeploy": "npm run build",
  "deploy": "gh-pages -d build"
}
```

Create GitHub Actions workflow file `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install and Build
        run: |
          npm install
          npm run build
      - name: Deploy
        uses: JamesIves/github-pages-deploy-action@4.1.4
        with:
          branch: gh-pages
          folder: build
```

### Step 2: AWS S3 Bucket Setup

```bash
# Create input bucket
aws s3 mb s3://optimo-input-files

# Create output bucket
aws s3 mb s3://optimo-output-files

# Configure CORS for input bucket
aws s3api put-bucket-cors --bucket optimo-input-files --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "MaxAgeSeconds": 3000
    }
  ]
}'
```

### Step 3: Create Docker Image for Batch

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Gurobi
RUN wget https://packages.gurobi.com/10.0/gurobi10.0.0_linux64.tar.gz \
    && tar -xzf gurobi10.0.0_linux64.tar.gz \
    && rm gurobi10.0.0_linux64.tar.gz

# Set Gurobi environment
ENV GUROBI_HOME=/opt/gurobi1000/linux64
ENV PATH="${GUROBI_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${GUROBI_HOME}/lib:${LD_LIBRARY_PATH}"

# Copy application code
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Entry point for batch job
ENTRYPOINT ["python", "scripts/run_batch_job.py"]
```

Build and push to ECR:
```bash
# Create ECR repository
aws ecr create-repository --repository-name optimo-batch

# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin \
    $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com

# Build and push
docker build -t optimo-batch .
docker tag optimo-batch:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com/optimo-batch:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com/optimo-batch:latest
```

### Step 4: AWS Batch Setup

```bash
# Create compute environment
aws batch create-compute-environment \
    --compute-environment-name optimo-compute-env \
    --type MANAGED \
    --state ENABLED \
    --compute-resources '{
        "type": "EC2",
        "allocationStrategy": "BEST_FIT_PROGRESSIVE",
        "minvCpus": 0,
        "maxvCpus": 16,
        "instanceTypes": ["m5.2xlarge"],
        "subnets": ["subnet-xxxxxx", "subnet-yyyyyy"],
        "securityGroupIds": ["sg-xxxxxx"],
        "instanceRole": "ecsInstanceRole"
    }'

# Create job queue
aws batch create-job-queue \
    --job-queue-name optimo-job-queue \
    --state ENABLED \
    --priority 1 \
    --compute-environment-order '{
        "order": 1,
        "computeEnvironment": "optimo-compute-env"
    }'

# Register job definition
aws batch register-job-definition \
    --job-definition-name optimo-job \
    --type container \
    --container-properties '{
        "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/optimo-batch:latest",
        "vcpus": 8,
        "memory": 30000,
        "command": [],
        "jobRoleArn": "arn:aws:iam::ACCOUNT_ID:role/optimo-batch-job-role",
        "environment": [
            {"name": "S3_INPUT_BUCKET", "value": "optimo-input-files"},
            {"name": "S3_OUTPUT_BUCKET", "value": "optimo-output-files"}
        ]
    }'
```

### Step 5: Lambda Functions Setup

Create Lambda function for job submission:
```python
import json
import boto3
import uuid
import os

batch = boto3.client('batch')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb').Table('optimo-jobs')

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        input_files = body.get('files', [])
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Submit batch job
        response = batch.submit_job(
            jobName=f'optimo-{job_id}',
            jobQueue='optimo-job-queue',
            jobDefinition='optimo-job',
            parameters={
                'jobId': job_id,
                'inputFiles': ','.join(input_files)
            }
        )
        
        # Store job metadata
        dynamodb.put_item(Item={
            'jobId': job_id,
            'batchJobId': response['jobId'],
            'status': 'SUBMITTED',
            'inputFiles': input_files,
            'submittedAt': int(time.time())
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': 'SUBMITTED'
            })
        }
        
    except Exception as e:
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
```

## Next Steps and Considerations

1. **Security**
   - Set up proper IAM roles with least privilege
   - Consider API Gateway authorization
   - Encrypt data in transit and at rest

2. **Monitoring**
   - Set up CloudWatch alarms for job failures
   - Monitor Batch compute environment usage
   - Track costs with AWS Cost Explorer

3. **Cost Optimization**
   - Use Spot instances for Batch compute environment
   - Set appropriate timeout for jobs
   - Monitor and adjust instance types based on performance

4. **Maintenance**
   - Set up automated testing for the pipeline
   - Create backup strategy for important data
   - Document the deployment process for team members
