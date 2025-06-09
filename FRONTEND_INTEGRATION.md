# Frontend Integration with AWS Backend

This document outlines the steps taken to integrate the OptimoV2 frontend with the AWS backend services.

## Configuration Setup

Created a configuration file at `optimo-frontend/src/config.ts` that imports AWS settings:

```typescript
// Import AWS configuration from the project root
import awsConfig from '../../config/aws_config.json';

// Export configuration for use in the frontend
export default {
  api: {
    baseUrl: awsConfig.api.baseUrl
  },
  buckets: {
    input: awsConfig.buckets.input,
    output: awsConfig.buckets.output
  },
  region: awsConfig.region
};
```

## API Service Updates

Updated the API service in `optimo-frontend/src/services/api.ts` to use presigned URLs for file uploads and downloads:

```typescript
import axios, { AxiosInstance } from 'axios';
import { Job, JobSubmissionData, JobResults } from '../types';
import config from '../config';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    // Use the API URL from the config file
    const baseURL = process.env.REACT_APP_API_URL || config.api.baseUrl;
    
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

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
    const fileKeys = [];
    
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
    const response = await this.api.post('/jobs', {
      files: fileKeys,
      parameters: data.parameters
    });
    
    return response.data;
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<Job> {
    const response = await this.api.get(`/jobs/${jobId}/status`);
    return response.data;
  }

  // Get job results
  async getJobResults(jobId: string): Promise<{downloadUrls: Record<string, string>}> {
    const response = await this.api.get(`/jobs/${jobId}/results`);
    return response.data;
  }

  // Download result file using presigned URL
  async downloadResult(url: string, fileName: string): Promise<void> {
    const response = await axios.get(url, {
      responseType: 'blob'
    });
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
}

export default new ApiService();
```

## File Upload Flow

The updated file upload flow now works as follows:

1. User selects files for upload in the frontend
2. Frontend requests presigned URLs from the API Gateway
3. Lambda function generates presigned URLs for each file
4. Frontend uploads files directly to S3 using the presigned URLs
5. Frontend submits job with references to the uploaded files
6. Lambda function creates a job in AWS Batch and tracks it in DynamoDB

## Job Status Checking

The job status checking flow has been updated:

1. Frontend requests job status from API Gateway using job ID
2. Lambda function checks status in DynamoDB and AWS Batch
3. Frontend displays status information to the user

## Result Downloading

The result downloading flow now uses presigned URLs:

1. Frontend requests results for a completed job
2. Lambda function generates presigned URLs for each result file
3. Frontend displays download links to the user
4. User clicks on links to download files directly from S3

## Build and Deployment Process

To build and deploy the frontend with AWS integration:

1. Ensure the AWS configuration is correctly set up in `config/aws_config.json`
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
