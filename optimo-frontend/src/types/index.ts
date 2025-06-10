export interface FileUpload {
  name: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

export interface Job {
  id: string;
  jobId?: string; // Optional jobId for backend compatibility
  status: 'pending' | 'running' | 'completed' | 'failed' | 'COMPLETED'; // Added 'COMPLETED' for backend compatibility
  createdAt: Date;
  updatedAt: Date;
  submittedAt?: Date; // Optional submittedAt for backend compatibility
  progress: number;
  currentStep?: string;
  error?: string;
  results?: JobResults;
  maxIterations?: number;
  parameters?: any; // Parameters from backend including maxIterations
}

export interface JobResults {
  masterSchedule?: string;
  studentAssignments?: string;
  teacherSchedule?: string;
  constraintViolations?: string;
  utilizationReport?: string;
}

export interface UploadedFiles {
  studentInfo?: File;
  studentPreferences?: File;
  teacherInfo?: File;
  teacherUnavailability?: File;
  sectionsInfo?: File;
  periods?: File;
}

export interface JobSubmissionData {
  files: UploadedFiles;
  parameters: OptimizationParameters;
}

export interface OptimizationParameters {
  maxIterations: number;
  minUtilization: number;
  maxUtilization: number;
  optimalMinUtilization: number;
  optimalMaxUtilization: number;
}
