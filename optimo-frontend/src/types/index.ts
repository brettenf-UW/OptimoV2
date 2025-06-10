export interface FileUpload {
  name: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
}

// AWS Batch job statuses
export type BatchStatus = 'SUBMITTED' | 'PENDING' | 'RUNNABLE' | 'STARTING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';

export interface Job {
  id: string;
  status: BatchStatus;
  createdAt: number; // Unix timestamp
  completedAt?: number; // Unix timestamp
  progress: number;
  currentStep?: string;
  error?: string;
  maxIterations?: number;
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
