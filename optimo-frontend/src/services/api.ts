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
    let jobs: Job[] = [];
    
    if (Array.isArray(response.data)) {
      jobs = response.data;
    } else if (response.data && response.data.jobs) {
      jobs = response.data.jobs;
    } else {
      console.warn('Unexpected response format from /jobs endpoint:', response.data);
      return [];
    }
    
    // Ensure maxIterations is set from parameters if available
    return jobs.map(job => {
      if (job.parameters && job.parameters.maxIterations && !job.maxIterations) {
        job.maxIterations = job.parameters.maxIterations;
      }
      return job;
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
    console.log('Getting status for job:', jobId);
    const response = await this.api.get<Job>(`/jobs/${jobId}/status`);
    console.log('Job status response:', response.data);
    
    // Ensure maxIterations is set from parameters if available
    if (response.data && response.data.parameters && response.data.parameters.maxIterations) {
      response.data.maxIterations = response.data.parameters.maxIterations;
    }
    
    return response.data;
  }

  // Get job results
  async getJobResults(jobId: string): Promise<{
    downloadUrls: Record<string, string>,
    metrics?: any,
    chartData?: any,
    optimizationSummary?: string[]
  }> {
    console.log('Getting results for job:', jobId);
    try {
      const response = await this.api.get(`/jobs/${jobId}/results`);
      console.log('Job results response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error getting job results:', error);
      throw error;
    }
  }
  
  // Cancel job
  async cancelJob(jobId: string): Promise<void> {
    await this.api.post(`/jobs/${jobId}/cancel`);
  }
}

const apiService = new ApiService();
export default apiService;
