# OptimoV2 Deployment Plan: GitHub Pages + AWS Batch

This guide outlines a streamlined deployment approach for OptimoV2 using GitHub Pages for the frontend and AWS Batch for on-demand optimization processing.

## 📊 Current Status (Updated: June 2025)

### ✅ Phase 1: Frontend (COMPLETE)
- **GitHub Pages**: Live at https://brettenf-UW.github.io/OptimoV2
- **React App**: Fully functional with Material-UI components
- **Features**: File upload, job submission, progress tracking, results visualization
- **Status**: Deployed and operational

### ✅ Phase 2: AWS Backend (COMPLETE)
- **Infrastructure**: Fully deployed
- **API Gateway**: Implemented with 5 endpoints
- **Lambda Functions**: Created and configured
- **AWS Batch**: Set up with c5.24xlarge instances
- **Status**: Ready for production use

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

3. **GitHub Repository Setup**
   - ✅ Code committed to local repository
   - ✅ Push to GitHub repository
   - ✅ Set up GitHub Pages deployment
   - ✅ Configure build process for production
   - ✅ Frontend deployed to https://brettenf-UW.github.io/OptimoV2

4. **API Integration Preparation**
   - ✅ Update API endpoints from mock server to AWS API Gateway URLs
   - ✅ Implement proper error handling for API failures
   - ✅ Add loading states and progress indicators
   - ✅ Configure CORS settings for production

5. **Production Deployment**
   - ✅ Create GitHub Actions workflow for CI/CD
   - ✅ Set up automated deployment to GitHub Pages
   - ✅ Configure custom domain (optional)
   - ✅ Test production build and deployment

6. **Frontend Enhancements**
   - ✅ Add file validation (CSV format, required columns)
   - ✅ Implement drag-and-drop file upload
   - ✅ Add download functionality for optimization results
   - ✅ Create user-friendly error messages
   - ✅ Add utilization summary display in results

### Phase 2: AWS Infrastructure Setup

#### ✅ **COMPLETED:**
1. **S3 Buckets**
   - ✅ Created input bucket `optimo-input-files` for uploaded files
   - ✅ Created output bucket `optimo-output-files` for optimization results
   - ✅ Set appropriate CORS policies for GitHub Pages access

2. **IAM Roles & Permissions**
   - ✅ Created role `optimo-lambda-role` for Lambda with S3 access
   - ✅ Created role `optimo-batch-role` for Batch with S3 access
   - ✅ Set up appropriate policies for each role
   - ✅ Added permissions for Secrets Manager access

3. **API Gateway**
   - ✅ Created REST API `optimo-api` with endpoints:
     - ✅ `POST /upload` - For generating presigned URLs
     - ✅ `POST /jobs` - For job submission
     - ✅ `GET /jobs` - For listing all jobs
     - ✅ `GET /jobs/{jobId}/status` - For checking job status
     - ✅ `GET /jobs/{jobId}/results` - For retrieving results
     - ✅ `POST /jobs/{jobId}/cancel` - For canceling jobs
   - ✅ Deployed to production stage

### Phase 3: AWS Batch Configuration

#### ✅ **COMPLETED:**
1. **Custom Docker Image**
   - ✅ Created Dockerfile with Python 3.9 and dependencies
   - ✅ Configured Gurobi installation
   - ✅ Added OptimoV2 application code
   - ✅ Pushed to Amazon ECR repository `optimo-batch`

2. **Batch Environment**
   - ✅ Created compute environment `optimo-compute-env`:
     - ✅ Using Spot instances for cost efficiency
     - ✅ c5.24xlarge instances (96 vCPUs, 192GB RAM)
     - ✅ Auto-scaling from 0 to 96 vCPUs
   - ✅ Created job queue `optimo-job-queue`
   - ✅ Defined job definition `optimo-job` using custom Docker image

### Phase 4: Lambda Functions

#### ✅ **COMPLETED:**
1. **Upload Handler**
   - ✅ Created `optimo-upload-handler` Lambda function
   - ✅ Implemented presigned URL generation for S3 uploads
   - ✅ Configured with environment variables

2. **Job Submission Handler**
   - ✅ Created `optimo-job-submission` Lambda function
   - ✅ Implemented AWS Batch job submission
   - ✅ Set up DynamoDB job tracking

3. **Status Checker**
   - ✅ Created `optimo-job-status` Lambda function
   - ✅ Implemented status checking from AWS Batch and DynamoDB
   - ✅ Added detailed status reporting

4. **Results Handler**
   - ✅ Created `optimo-results-handler` Lambda function
   - ✅ Implemented presigned URL generation for result downloads
   - ✅ Configured with environment variables

5. **Job Listing**
   - ✅ Created `optimo-jobs-list` Lambda function
   - ✅ Implemented retrieval of all jobs from DynamoDB
   - ✅ Configured with environment variables

6. **Job Cancellation**
   - ✅ Created `optimo-job-cancel` Lambda function
   - ✅ Implemented AWS Batch job cancellation
   - ✅ Added status update in DynamoDB

### Phase 5: Frontend Integration

#### ✅ **COMPLETED:**
1. **API Integration**
   - ✅ Created configuration file to import AWS settings
   - ✅ Updated API service to use AWS API Gateway endpoints
   - ✅ Implemented presigned URL workflow for file uploads
   - ✅ Updated job status checking to use new API endpoints
   - ✅ Implemented result downloading using presigned URLs
   - ✅ Added job cancellation functionality

2. **Build and Deployment**
   - ✅ Updated build process to include AWS configuration
   - ✅ Fixed TypeScript errors in the API service
   - ✅ Tested production build with AWS backend
   - ✅ Deployed to GitHub Pages

### Phase 6: Gurobi License Management

#### ✅ **COMPLETED:**
1. **Secure License Storage**
   - ✅ Created AWS Secrets Manager secret for Gurobi license
   - ✅ Set up IAM permissions for Batch jobs to access the secret
   - ✅ Updated Batch job definition with environment variables

2. **Runtime License Retrieval**
   - ✅ Updated batch job script to retrieve license at runtime
   - ✅ Implemented secure license handling in the container
   - ✅ Added proper error handling and logging

## Frontend Integration Details

The frontend has been updated to work with the AWS backend using the following approach:

### Configuration

Created a configuration file at `optimo-frontend/src/config.ts`:

```typescript
// src/config.ts
const config = {
  api: {
    baseUrl: process.env.REACT_APP_API_URL || "https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod"
  },
  buckets: {
    input: "optimo-input-files",
    output: "optimo-output-files"
  },
  region: "us-west-2"
};

export default config;
```

### API Service Updates

Updated the API service to use presigned URLs for file uploads and downloads:

```typescript
// Get presigned URL for file upload
async getUploadUrl(fileName: string, fileType: string): Promise<{uploadUrl: string, fileKey: string}> {
  const response = await this.api.post('/upload', { fileName, fileType });
  return response.data;
}

// Upload file using presigned URL
async uploadFile(url: string, file: File): Promise<void> {
  await axios.put(url, file, {
    headers: {
      'Content-Type': file.type
    }
  });
}

// Submit job with file keys
async submitJob(data: JobSubmissionData): Promise<Job> {
  // First upload all files and get their keys
  const fileKeys: string[] = [];
  
  for (const [key, file] of Object.entries(data.files)) {
    if (file) {
      // Get presigned URL
      const { uploadUrl, fileKey } = await this.getUploadUrl(file.name, file.type);
      
      // Upload file
      await this.uploadFile(uploadUrl, file);
      
      // Add file key to the list
      fileKeys.push(fileKey);
    }
  }
  
  // Submit job with file keys
  const response = await this.api.post<Job>('/jobs', {
    files: fileKeys,
    parameters: data.parameters
  });
  
  return response.data;
}

// Download result file using presigned URL
async downloadResult(url: string, fileName: string): Promise<Blob> {
  const response = await axios.get(url, {
    responseType: 'blob'
  });
  
  // Return the blob directly
  return new Blob([response.data]);
}

// Cancel job
async cancelJob(jobId: string): Promise<void> {
  await this.api.post(`/jobs/${jobId}/cancel`);
}
```

### Build and Deployment Process

To build and deploy the frontend with AWS integration:

1. Ensure the environment variables are set in `.env`:
   ```
   REACT_APP_API_URL=https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod
   ```

2. Navigate to the frontend directory:
   ```bash
   cd optimo-frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Build the production version:
   ```bash
   npm run build
   ```

5. Deploy to GitHub Pages:
   ```bash
   npm run deploy
   ```

## Gurobi License Management

The Gurobi license is securely managed using AWS Secrets Manager:

1. **Secret Storage**:
   - Created a secret named `optimo/gurobi-license` in AWS Secrets Manager
   - License content is encrypted at rest and in transit

2. **Access Control**:
   - Added IAM policy to `optimo-batch-role` to allow access to the secret
   - Only authorized batch jobs can retrieve the license

3. **Runtime Retrieval**:
   - Batch job script retrieves the license at runtime
   - License is stored in the container's ephemeral storage
   - Environment variable `GRB_LICENSE_FILE` is set to point to the license file

4. **License Updates**:
   - License can be updated in Secrets Manager without rebuilding Docker images
   - All new batch jobs will automatically use the updated license

## Next Steps and Considerations

1. **Testing**
   - Perform end-to-end testing with real data
   - Verify file upload and download functionality
   - Test job submission and status tracking
   - Validate optimization results

2. **Security**
   - Consider implementing API Gateway authorization
   - Set up CloudFront for content delivery (optional)
   - Review IAM permissions for least privilege

3. **Monitoring**
   - Set up CloudWatch alarms for job failures
   - Monitor Batch compute environment usage
   - Track costs with AWS Cost Explorer

4. **Cost Optimization**
   - Review Spot instance usage and interruption rates
   - Adjust instance types based on performance data
   - Consider reserved instances for predictable workloads

5. **Maintenance**
   - Set up automated testing for the pipeline
   - Create backup strategy for important data
   - Document the deployment process for team members

6. **Troubleshooting**
   - Check CloudWatch logs for Lambda function errors
   - Verify CORS settings in API Gateway
   - Monitor S3 bucket permissions and access
