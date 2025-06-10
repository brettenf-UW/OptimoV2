import { BatchStatus } from '../types';

// Map AWS Batch status to user-friendly display
export const getStatusDisplay = (status: BatchStatus): string => {
  const statusMap: Record<BatchStatus, string> = {
    'SUBMITTED': 'Queued',
    'PENDING': 'Queued',
    'RUNNABLE': 'Starting',
    'STARTING': 'Starting',
    'RUNNING': 'Running',
    'SUCCEEDED': 'Completed',
    'FAILED': 'Failed'
  };
  
  return statusMap[status] || status;
};

// Get status color for UI
export const getStatusColor = (status: BatchStatus): 'default' | 'primary' | 'success' | 'error' => {
  switch (status) {
    case 'SUBMITTED':
    case 'PENDING':
      return 'default';
    case 'RUNNABLE':
    case 'STARTING':
    case 'RUNNING':
      return 'primary';
    case 'SUCCEEDED':
      return 'success';
    case 'FAILED':
      return 'error';
    default:
      return 'default';
  }
};

// Check if job is still in progress
export const isJobInProgress = (status: BatchStatus): boolean => {
  return ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING'].includes(status);
};

// Check if job has completed successfully
export const isJobCompleted = (status: BatchStatus): boolean => {
  return status === 'SUCCEEDED';
};

// Check if job can be cancelled
export const canCancelJob = (status: BatchStatus): boolean => {
  return ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING'].includes(status);
};

// Get progress percentage based on status
export const getDefaultProgress = (status: BatchStatus): number => {
  const progressMap: Record<BatchStatus, number> = {
    'SUBMITTED': 0,
    'PENDING': 5,
    'RUNNABLE': 10,
    'STARTING': 15,
    'RUNNING': 50, // Will be overridden by actual progress
    'SUCCEEDED': 100,
    'FAILED': 0
  };
  
  return progressMap[status] || 0;
};