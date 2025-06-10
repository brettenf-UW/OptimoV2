# OptimoV2 Complete Deployment Plan & Architecture

## 📊 System Overview

OptimoV2 is a production-ready class schedule optimization system that combines:
- **Frontend**: React application hosted on GitHub Pages
- **Backend**: Serverless AWS architecture with Lambda, Batch, and S3
- **Optimization Engine**: MILP solver (Gurobi) with Gemini AI enhancements

## 🏗️ Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────────────┐
│                              GitHub Pages                                │
│                          React Frontend (SPA)                            │
└─────────────────────┬───────────────────────────────────┬───────────────┘
                      │                                   │
                      ▼                                   ▼
┌─────────────────────────────────┐     ┌────────────────────────────────┐
│      API Gateway (REST)         │     │        CloudFront CDN           │
│   https://3dbrbfl8f3.execute-   │     │    (Static Asset Delivery)      │
│   api.us-west-2.amazonaws.com   │     └────────────────────────────────┘
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Lambda Functions                              │
├─────────────────────────────────┬───────────────────────────────────────┤
│ • upload-handler                │ • job-submission                      │
│ • jobs-list-handler             │ • job-status                          │
│ • results-handler-real-metrics  │ • job-cancel-handler                  │
│ • job-completion-handler        │                                       │
└─────────┬───────────────────────┴──────────┬────────────────────────────┘
          │                                  │
          ▼                                  ▼
┌─────────────────────┐         ┌───────────────────────┐
│     DynamoDB        │         │      AWS Batch        │
│   (optimo-jobs)     │         │  (Compute Environment)│
└─────────────────────┘         └───────────┬───────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
          ┌─────────────────────┐                   ┌─────────────────────┐
          │   S3 Input Bucket   │                   │  S3 Output Bucket   │
          │ optimo-input-files  │                   │ optimo-output-files │
          └─────────────────────┘                   └─────────────────────┘
```

### Component Details

#### Frontend (GitHub Pages)
- **URL**: https://brettenf-uw.github.io/OptimoV2
- **Technology**: React with Material-UI
- **Features**:
  - File upload with drag-and-drop
  - Real-time job monitoring
  - Results visualization with charts
  - Job history tracking
  - Responsive design

#### API Gateway
- **URL**: https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod
- **Endpoints**:
  ```
  POST   /upload                 - Get presigned URL for file upload
  POST   /jobs                   - Submit new optimization job
  GET    /jobs                   - List all jobs
  GET    /jobs/{jobId}/status    - Get job status
  GET    /jobs/{jobId}/results   - Get job results
  POST   /jobs/{jobId}/cancel    - Cancel running job
  ```

#### Lambda Functions
Each function has specific responsibilities:
- **upload-handler**: Generates presigned S3 URLs for secure file uploads
- **job-submission**: Creates batch jobs and manages job queue
- **job-status**: Retrieves real-time status from Batch and DynamoDB
- **jobs-list-handler**: Returns paginated list of all jobs
- **results-handler-real-metrics**: Calculates metrics and generates download URLs
- **job-completion-handler**: Updates DynamoDB when Batch jobs complete

#### AWS Batch
- **Compute Environment**: optimo-compute-env
  - Instance Type: c5.24xlarge (96 vCPUs, 192GB RAM)
  - Spot instances for cost optimization
  - Auto-scaling 0-96 vCPUs
- **Job Queue**: optimo-job-queue
- **Job Definition**: optimo-job-updated
  - Docker image with Python 3.9, Gurobi, and optimization code

#### Data Storage
- **DynamoDB Table**: optimo-jobs
  - Primary Key: jobId
  - Stores job metadata, status, and results
- **S3 Buckets**:
  - Input: optimo-input-files (user uploads)
  - Output: optimo-output-files (optimization results)

## 🚀 Deployment Guide

### Prerequisites
- AWS CLI configured with appropriate credentials
- Node.js 16+ and npm installed
- Docker (for building Batch container)
- GitHub account with Pages enabled

### Step 1: Deploy Frontend

```bash
# Clone repository
git clone https://github.com/brettenf-uw/OptimoV2.git
cd OptimoV2/optimo-frontend

# Install dependencies
npm install

# Configure environment
echo "REACT_APP_API_URL=https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod" > .env

# Build and deploy
npm run build
npm run deploy
```

### Step 2: Deploy Lambda Functions

```bash
cd ../lambda

# Package and deploy each function
for func in upload_handler job_submission job_status jobs_list_handler results_handler_real_metrics job_completion_handler job_cancel_handler; do
    zip ${func}.zip ${func}.py
    aws lambda update-function-code --function-name optimo-${func//_/-} --zip-file fileb://${func}.zip
done
```

### Step 3: Configure API Gateway

```bash
# Enable CORS (if not already done)
./enable_cors_existing_api.sh

# Deploy API changes
aws apigateway create-deployment --rest-api-id 3dbrbfl8f3 --stage-name prod
```

### Step 4: Set Up EventBridge Rule

```bash
# Create rule for Batch job completion
aws events put-rule --name optimo-batch-job-state-change \
    --event-pattern '{"source":["aws.batch"],"detail-type":["Batch Job State Change"],"detail":{"status":["SUCCEEDED","FAILED"],"jobQueue":["optimo-job-queue"]}}' \
    --state ENABLED

# Add Lambda target
aws events put-targets --rule optimo-batch-job-state-change \
    --targets "Id=1,Arn=arn:aws:lambda:us-west-2:529088253685:function:optimo-job-completion-handler"
```

### Step 5: Deploy Batch Container

```bash
cd ../

# Build Docker image
docker build -t optimo-batch .

# Push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 529088253685.dkr.ecr.us-west-2.amazonaws.com
docker tag optimo-batch:latest 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:latest
docker push 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:latest

# Update job definition
aws batch register-job-definition --job-definition-name optimo-job --type container \
    --container-properties file://job-definition.json
```

## 🔧 Configuration

### Environment Variables

#### Lambda Functions
```
DYNAMODB_TABLE=optimo-jobs
S3_INPUT_BUCKET=optimo-input-files
S3_OUTPUT_BUCKET=optimo-output-files
JOB_QUEUE=optimo-job-queue
JOB_DEFINITION=optimo-job-updated
```

#### Frontend (.env)
```
REACT_APP_API_URL=https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod
```

### IAM Roles

#### Lambda Execution Role (optimo-lambda-role)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/optimo-jobs"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GeneratePresignedUrl"
      ],
      "Resource": [
        "arn:aws:s3:::optimo-input-files/*",
        "arn:aws:s3:::optimo-output-files/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "batch:SubmitJob",
        "batch:DescribeJobs",
        "batch:ListJobs"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📊 Monitoring & Operations

### CloudWatch Dashboards
Monitor key metrics:
- Lambda invocations and errors
- Batch job status distribution
- S3 bucket usage
- DynamoDB read/write capacity

### Alarms
Set up alarms for:
- Lambda function errors > 1%
- Batch job failures > 10%
- DynamoDB throttling
- S3 bucket size > 100GB

### Logging
All components log to CloudWatch:
- `/aws/lambda/{function-name}` - Lambda logs
- `/aws/batch/job` - Batch job output
- API Gateway access logs

## 💰 Cost Optimization

### Current Setup (Estimated Monthly)
- Lambda: ~$10 (assuming 1000 jobs/month)
- Batch: ~$200 (Spot instances, 50 hours/month)
- S3: ~$5 (100GB storage)
- DynamoDB: ~$5 (on-demand pricing)
- API Gateway: ~$3 (1M requests)
- **Total: ~$223/month**

### Cost Reduction Strategies
1. Use Batch Spot instances (already implemented)
2. Set S3 lifecycle policies for old results
3. Use DynamoDB on-demand pricing (already implemented)
4. Implement result caching in Lambda

## 🔒 Security

### Data Protection
- All data encrypted at rest (S3, DynamoDB)
- TLS encryption for all API calls
- Presigned URLs expire after 5 minutes

### Access Control
- IAM roles follow least privilege principle
- API Gateway uses CORS to restrict origins
- No public access to S3 buckets

### Compliance
- All data remains in us-west-2 region
- CloudTrail enabled for audit logging
- No PII stored in logs

## 🚨 Troubleshooting

### Common Issues

#### Job Stuck in RUNNABLE
```bash
# Check compute environment
aws batch describe-compute-environments --compute-environments optimo-compute-env

# Check for capacity issues
aws ec2 describe-spot-instance-requests --filters "Name=state,Values=active"
```

#### CORS Errors
```bash
# Test CORS headers
curl -X OPTIONS https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs \
     -H "Origin: https://brettenf-uw.github.io" \
     -H "Access-Control-Request-Method: GET"
```

#### Job Failures
```bash
# Check Batch logs
aws logs get-log-events --log-group-name /aws/batch/job \
     --log-stream-name optimo-job-queue/default/{job-id}

# Check DynamoDB for error details
aws dynamodb get-item --table-name optimo-jobs \
     --key '{"jobId": {"S": "YOUR-JOB-ID"}}'
```

## 📈 Performance Optimization

### Current Performance
- Average job completion: 8-15 minutes
- API response time: <200ms
- Frontend load time: <2 seconds

### Optimization Opportunities
1. Implement CloudFront for API caching
2. Use Lambda Provisioned Concurrency for cold starts
3. Optimize Docker image size
4. Implement parallel processing in Batch

## 🔄 Maintenance

### Regular Tasks
- **Weekly**: Review CloudWatch logs for errors
- **Monthly**: Check AWS costs and optimize
- **Quarterly**: Update dependencies and security patches

### Backup Strategy
- DynamoDB: Point-in-time recovery enabled
- S3: Versioning enabled on output bucket
- Code: GitHub repository with tags for releases

## 📝 Future Enhancements

1. **Email Notifications**
   - SES integration for job completion emails
   - Customizable notification preferences

2. **Advanced Analytics**
   - Historical optimization trends
   - Performance benchmarking
   - ML-based parameter suggestions

3. **Multi-Tenant Support**
   - User authentication with Cognito
   - Organization-based data isolation
   - Usage quotas and billing

4. **API Enhancements**
   - GraphQL endpoint
   - WebSocket for real-time updates
   - Batch job submission API

## 📞 Support

For production issues:
1. Check CloudWatch Logs
2. Review this documentation
3. Check AWS Service Health Dashboard
4. Contact AWS Support (if available)

---

Last Updated: June 2025
Version: 2.0