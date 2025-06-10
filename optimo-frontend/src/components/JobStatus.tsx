import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  Button,
  Divider,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { Job, BatchStatus } from '../types';
import api from '../services/api';
import { getStatusDisplay, getStatusColor, isJobInProgress, isJobCompleted, canCancelJob } from '../utils/jobStatus';

interface JobStatusProps {
  jobId?: string;
  onJobComplete?: (job: Job) => void;
  showJobsList?: boolean;
  showCurrentJob?: boolean;
  onJobSelect?: (job: Job | null) => void;
  selectedJobId?: string;
  refreshTrigger?: number;
}

interface IterationProgress {
  iteration: number;
  status: 'pending' | 'running' | 'completed';
  step: string;
  details?: string;
}

export const JobStatus: React.FC<JobStatusProps> = ({ 
  jobId, 
  onJobComplete,
  showJobsList = true,
  showCurrentJob = true,
  onJobSelect,
  selectedJobId,
  refreshTrigger
}) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [iterations, setIterations] = useState<IterationProgress[]>([]);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Generate iteration progress based on job progress
  const updateIterationProgress = (job: Job) => {
    if (!job.maxIterations) job.maxIterations = 3; // Default to 3 iterations
    
    // For completed jobs, set all iterations to completed
    if (job.status === 'SUCCEEDED') {
      const completedIterations: IterationProgress[] = [];
      for (let i = 0; i < job.maxIterations; i++) {
        completedIterations.push({
          iteration: i,
          status: 'completed',
          step: 'Completed',
          details: `Iteration ${i} completed successfully`
        });
      }
      setIterations(completedIterations);
      return;
    }
    
    const progressPerIteration = 100 / job.maxIterations;
    const currentIteration = Math.floor(job.progress / progressPerIteration);
    const currentIterationProgress = (job.progress % progressPerIteration) / progressPerIteration * 100;
    
    const newIterations: IterationProgress[] = [];
    
    for (let i = 0; i < job.maxIterations; i++) {
      if (i < currentIteration) {
        newIterations.push({
          iteration: i,
          status: 'completed',
          step: 'Completed',
          details: `Iteration ${i} completed successfully`
        });
      } else if (i === currentIteration) {
        let step = 'Initializing...';
        let details = '';
        
        if (currentIterationProgress < 20) {
          step = 'Running MILP optimization...';
          details = 'Solving constraints and generating initial schedule';
        } else if (currentIterationProgress < 40) {
          step = 'Analyzing utilization...';
          details = 'Calculating section utilization percentages';
        } else if (currentIterationProgress < 60) {
          step = 'Running Gemini AI analysis...';
          details = 'Getting optimization suggestions from AI';
        } else if (currentIterationProgress < 80) {
          step = 'Applying optimizations...';
          details = 'Implementing SPLIT/MERGE/ADD/REMOVE actions';
        } else {
          step = 'Finalizing iteration...';
          details = 'Preparing for next iteration';
        }
        
        newIterations.push({
          iteration: i,
          status: 'running',
          step,
          details
        });
      } else {
        newIterations.push({
          iteration: i,
          status: 'pending',
          step: 'Waiting...',
          details: `Iteration ${i} pending`
        });
      }
    }
    
    setIterations(newIterations);
  };

  const fetchJobs = async () => {
    if (!isInitialLoad) {
      setLoading(true);
    }
    setError(null);
    try {
      const fetchedJobs = await api.getJobs();
      // Ensure fetchedJobs is an array
      const jobsArray = Array.isArray(fetchedJobs) ? fetchedJobs : [];
      // Sort by creation date (newest first)
      const sortedJobs = jobsArray.sort((a, b) => {
        return (b.createdAt || 0) - (a.createdAt || 0);
      });
      // Show the 5 most recent jobs (including running ones)
      setJobs(sortedJobs.slice(0, 5));
      setIsInitialLoad(false);
    } catch (err: any) {
      console.error('Failed to fetch jobs:', err);
      setError('Failed to fetch jobs');
      setJobs([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchJobStatus = async (id: string) => {
    try {
      const job = await api.getJobStatus(id);
      setSelectedJob(job);
      
      // Update iteration progress
      updateIterationProgress(job);
      
      // Update job in list
      setJobs(prevJobs => 
        prevJobs.map(j => j.id === id ? job : j)
      );

      // Check if job completed successfully
      if (isJobCompleted(job.status) && onJobComplete) {
        console.log('Job completed, triggering results display:', job);
        onJobComplete(job);
      }
    } catch (err: any) {
      setError(`Failed to fetch job status: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger]); // Refetch when a new job is submitted

  // Add a small delay when refreshTrigger changes to ensure the new job is in the database
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      const timer = setTimeout(() => {
        fetchJobs();
      }, 1000); // 1 second delay
      return () => clearTimeout(timer);
    }
  }, [refreshTrigger]);

  // Also fetch jobs on mount and when showJobsList changes
  useEffect(() => {
    if (showJobsList) {
      fetchJobs();
    }
  }, [showJobsList]);

  useEffect(() => {
    if (jobId) {
      fetchJobStatus(jobId);
    }
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedJob && selectedJob.id && isJobInProgress(selectedJob.status)) {
      const interval = setInterval(() => {
        if (selectedJob.id) {
          fetchJobStatus(selectedJob.id);
        }
      }, 2000); // Poll every 2 seconds for smoother updates

      return () => clearInterval(interval);
    }
  }, [selectedJob]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-refresh job list if any jobs are running
  useEffect(() => {
    const hasRunningJobs = jobs.some(job => isJobInProgress(job.status));
    
    if (hasRunningJobs && showJobsList) {
      const interval = setInterval(() => {
        fetchJobs();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [jobs, showJobsList]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCancelJob = async (id: string) => {
    try {
      await api.cancelJob(id);
      fetchJobs();
    } catch (err: any) {
      setError(`Failed to cancel job: ${err.message}`);
    }
  };

  const getStatusIcon = (status: BatchStatus) => {
    switch (status) {
      case 'SUBMITTED':
      case 'PENDING':
        return <ScheduleIcon color="action" />;
      case 'RUNNABLE':
      case 'STARTING':
        return <PlayArrowIcon color="action" />;
      case 'RUNNING':
        return <PlayArrowIcon color="primary" />;
      case 'SUCCEEDED':
        return <CheckCircleIcon color="success" />;
      case 'FAILED':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon color="action" />;
    }
  };

  // Removed - using imported getStatusColor instead

  const getIterationIcon = (status: IterationProgress['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'running':
        return <PlayArrowIcon color="primary" fontSize="small" />;
      default:
        return <ScheduleIcon color="action" fontSize="small" />;
    }
  };

  return (
    <Box>
      {showCurrentJob && jobId && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                Job Progress
              </Typography>
              <IconButton onClick={() => fetchJobStatus(jobId)} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {selectedJob && selectedJob.id && selectedJob.id === jobId && (
            <>
              <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getStatusIcon(selectedJob.status)}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      Current Job: {selectedJob.id.substring(0, 8)}
                    </Typography>
                    <Chip
                      label={getStatusDisplay(selectedJob.status)}
                      color={getStatusColor(selectedJob.status)}
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Box>

                  {selectedJob.status === 'RUNNING' && (
                    <>
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Overall Progress
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={selectedJob.progress}
                          sx={{ mb: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {selectedJob.currentStep || 'Processing...'} ({selectedJob.progress}%)
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      <Typography variant="subtitle2" gutterBottom>
                        Iteration Progress
                      </Typography>
                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Stepper activeStep={iterations.findIndex(i => i.status === 'running')} orientation="vertical">
                          {iterations.map((iter, index) => (
                            <Step key={index} completed={iter.status === 'completed'}>
                              <StepLabel
                                StepIconComponent={() => getIterationIcon(iter.status)}
                                optional={
                                  iter.status === 'running' && (
                                    <Typography variant="caption">{iter.details}</Typography>
                                  )
                                }
                              >
                                Iteration {iter.iteration}
                              </StepLabel>
                              <StepContent>
                                <Typography variant="body2" color="text.secondary">
                                  {iter.step}
                                </Typography>
                                {iter.status === 'running' && (
                                  <LinearProgress sx={{ mt: 1, mb: 2 }} />
                                )}
                              </StepContent>
                            </Step>
                          ))}
                        </Stepper>
                      </Paper>
                    </>
                  )}

                  {selectedJob.status === 'SUCCEEDED' && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      Optimization completed successfully! All {selectedJob.maxIterations || 3} iterations finished.
                    </Alert>
                  )}

                  {selectedJob.error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {selectedJob.error}
                    </Alert>
                  )}

                  {selectedJob.status === 'RUNNING' && (
                    <Box sx={{ mt: 2 }}>
                      <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        startIcon={<CancelIcon />}
                        onClick={() => handleCancelJob(selectedJob.id)}
                      >
                        Cancel Job
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </>
          )}
          </CardContent>
        </Card>
      )}

      {showJobsList && (
        <Card sx={{ 
          mt: showCurrentJob && jobId ? 3 : 0,
          backgroundColor: 'transparent',
          boxShadow: 'none'
        }}>
          <CardContent sx={{ p: 0 }}>
            {!showCurrentJob && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mb: 2 }}>
                <IconButton onClick={fetchJobs} disabled={loading} size="small">
                  <RefreshIcon />
                </IconButton>
              </Box>
            )}

            <List sx={{ py: 0, px: 0 }}>
            {jobs.map((job, index) => {
              // Get job properties
              const jobId = job.id;
              const jobStatus = job.status;
              // Convert Unix timestamp (seconds) to Date object
              const jobCreatedAt = new Date((job.createdAt || Date.now() / 1000) * 1000);
              
              return (
                <ListItem
                  key={jobId}
                  button
                  selected={selectedJobId === jobId}
                  onClick={() => {
                    const jobData = {...job, id: jobId};
                    
                    // Toggle selection
                    if (selectedJobId === jobId) {
                      // Deselect - this should clear the selection
                      setSelectedJob(null);
                      if (onJobSelect) {
                        onJobSelect(null);
                      }
                    } else {
                      // Select
                      setSelectedJob(jobData);
                      if (onJobSelect) {
                        onJobSelect(jobData);
                      }
                      // If job is completed, trigger the results view
                      if (jobStatus === 'SUCCEEDED' && onJobComplete) {
                        onJobComplete(jobData);
                      }
                    }
                  }}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 1,
                    backgroundColor: '#ffffff',
                    border: '1px solid #e0e0e0',
                    '&:hover': {
                      backgroundColor: '#f5f5f5',
                      borderColor: '#1976d2',
                    },
                    '&.Mui-selected': {
                      backgroundColor: '#e3f2fd',
                      borderColor: '#1976d2',
                      '&:hover': {
                        backgroundColor: '#bbdefb',
                      }
                    }
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2">
                        {new Date(jobCreatedAt).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </Typography>
                    }
                    secondary={
                      <Box component="span">
                        {(() => {
                          switch (jobStatus) {
                            case 'RUNNING':
                              return (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2" color="primary" component="span">
                                    In Progress • {job.progress || 0}%
                                  </Typography>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={job.progress || 0} 
                                    sx={{ width: 60, height: 4 }}
                                  />
                                </Box>
                              );
                            case 'SUCCEEDED':
                              return (
                                <Typography variant="body2" component="span" sx={{ color: '#4caf50', fontWeight: 500 }}>
                                  ✓ Completed • Click to view results
                                </Typography>
                              );
                            case 'FAILED':
                              return (
                                <Typography variant="body2" component="span" sx={{ color: '#f44336' }}>
                                  ✗ Failed
                                </Typography>
                              );
                            case 'SUBMITTED':
                            case 'PENDING':
                              return (
                                <Typography variant="body2" color="text.secondary" component="span">
                                  Queued...
                                </Typography>
                              );
                            case 'RUNNABLE':
                            case 'STARTING':
                              return (
                                <Typography variant="body2" color="primary" component="span">
                                  Starting...
                                </Typography>
                              );
                            default:
                              return (
                                <Typography variant="body2" color="text.secondary" component="span">
                                  {getStatusDisplay(jobStatus)}
                                </Typography>
                              );
                          }
                        })()}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    {getStatusIcon(jobStatus)}
                  </ListItemSecondaryAction>
                </ListItem>
              );
            })}
          </List>

            {jobs.length === 0 && !loading && (
              <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 3 }}>
                No previous optimization runs found.
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
