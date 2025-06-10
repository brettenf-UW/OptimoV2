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
    
    return jobs;
  }

  // Get presigned URL for file upload
  async getUploadUrl(fileName: string, fileType: string): Promise<{uploadUrl: string, fileKey: string}> {
    const response = await this.api.post('/upload', { fileName: fileName, fileType: fileType });
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
    // First upload all files and get their S3 keys
    const s3Keys: Record<string, string> = {};
    
    for (const [key, file] of Object.entries(data.files)) {
      if (file) {
        // Get presigned URL
        const { uploadUrl, fileKey } = await this.getUploadUrl(file.name, file.type);
        
        // Upload file
        await this.uploadFile(uploadUrl, file);
        
        // Map to expected s3Keys format
        s3Keys[key] = fileKey;
      }
    }
    
    // Submit job with s3Keys and parameters matching unified handler format
    const response = await this.api.post<Job>('/jobs', {
      s3Keys,
      parameters: {
        maxIterations: data.parameters.maxIterations,
        minUtilization: data.parameters.minUtilization,
        maxUtilization: data.parameters.maxUtilization,
        optimalRangeMin: data.parameters.optimalMinUtilization,
        optimalRangeMax: data.parameters.optimalMaxUtilization
      }
    });
    
    return response.data;
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<Job> {
    console.log('Getting status for job:', jobId);
    const response = await this.api.get<Job>(`/jobs/${jobId}/status`);
    console.log('Job status response:', response.data);
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
