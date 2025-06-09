import axios, { AxiosInstance } from 'axios';
import { Job, JobSubmissionData, JobResults } from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    // Base URL will be updated when AWS endpoint is ready
    const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Upload files and submit job
  async submitJob(data: JobSubmissionData): Promise<Job> {
    const formData = new FormData();
    
    // Append files
    Object.entries(data.files).forEach(([key, file]) => {
      if (file) {
        formData.append(key, file);
      }
    });
    
    // Append parameters
    formData.append('parameters', JSON.stringify(data.parameters));
    
    const response = await this.api.post<Job>('/jobs', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<Job> {
    const response = await this.api.get<Job>(`/jobs/${jobId}`);
    return response.data;
  }

  // Get all jobs
  async getJobs(): Promise<Job[]> {
    const response = await this.api.get<Job[]>('/jobs');
    return response.data;
  }

  // Download result file
  async downloadResult(jobId: string, resultType: keyof JobResults): Promise<Blob> {
    const response = await this.api.get(`/jobs/${jobId}/results/${resultType}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Cancel job
  async cancelJob(jobId: string): Promise<void> {
    await this.api.post(`/jobs/${jobId}/cancel`);
  }
}

export default new ApiService();