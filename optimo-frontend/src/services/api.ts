import axios, { AxiosInstance } from 'axios';
import { Job, JobSubmissionData } from '../types';
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

  // Get all jobs
  async getJobs(): Promise<Job[]> {
    const response = await this.api.get('/jobs');
    // Handle different response formats from Lambda
    if (Array.isArray(response.data)) {
      return response.data;
    } else if (response.data && response.data.jobs) {
      return response.data.jobs;
    } else {
      console.warn('Unexpected response format from /jobs endpoint:', response.data);
      return [];
    }
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

  // Get job status
  async getJobStatus(jobId: string): Promise<Job> {
    const response = await this.api.get<Job>(`/jobs/${jobId}/status`);
    return response.data;
  }

  // Get job results
  async getJobResults(jobId: string): Promise<{downloadUrls: Record<string, string>}> {
    const response = await this.api.get<{downloadUrls: Record<string, string>}>(`/jobs/${jobId}/results`);
    return response.data;
  }

  // Download result file using presigned URL - returns the Blob directly
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
}

const apiService = new ApiService();
export default apiService;
