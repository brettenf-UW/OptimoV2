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
import { Job } from '../types';
import api from '../services/api';

interface JobStatusProps {
  jobId?: string;
  onJobComplete?: (job: Job) => void;
  showJobsList?: boolean;
  showCurrentJob?: boolean;
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
  showCurrentJob = true
}) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [iterations, setIterations] = useState<IterationProgress[]>([]);

  // Generate iteration progress based on job progress
  const updateIterationProgress = (job: Job) => {
    if (!job.maxIterations) job.maxIterations = 3; // Default to 3 iterations
    
    // For completed jobs, set all iterations to completed
    if (job.status === 'completed' || job.status === 'COMPLETED') {
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
    setLoading(true);
    setError(null);
    try {
      const fetchedJobs = await api.getJobs();
      // Ensure fetchedJobs is an array
      const jobsArray = Array.isArray(fetchedJobs) ? fetchedJobs : [];
      // Sort by creation date and take only the last 3 jobs
      const sortedJobs = jobsArray.sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      // Only show the 3 most recent jobs
      setJobs(sortedJobs.slice(0, 3));
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

      // Check for both lowercase 'completed' and uppercase 'COMPLETED' status
      if ((job.status === 'completed' || job.status === 'COMPLETED') && onJobComplete) {
        console.log('Job completed, triggering results display:', job);
        onJobComplete(job);
      }
    } catch (err: any) {
      setError(`Failed to fetch job status: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (jobId) {
      fetchJobStatus(jobId);
    }
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedJob && ['pending', 'running'].includes(selectedJob.status)) {
      const interval = setInterval(() => {
        fetchJobStatus(selectedJob.id);
      }, 2000); // Poll every 2 seconds for smoother updates

      return () => clearInterval(interval);
    }
  }, [selectedJob]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCancelJob = async (id: string) => {
    try {
      await api.cancelJob(id);
      fetchJobs();
    } catch (err: any) {
      setError(`Failed to cancel job: ${err.message}`);
    }
  };

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return <ScheduleIcon color="action" />;
      case 'running':
        return <PlayArrowIcon color="primary" />;
      case 'completed':
      case 'COMPLETED':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
    }
  };

  const getStatusColor = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'running':
        return 'primary';
      case 'completed':
      case 'COMPLETED':
        return 'success';
      case 'failed':
        return 'error';
    }
  };

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

            {selectedJob && selectedJob.id === jobId && (
            <>
              <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getStatusIcon(selectedJob.status)}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      Current Job: {selectedJob.id.substring(0, 8)}
                    </Typography>
                    <Chip
                      label={selectedJob.status.toUpperCase()}
                      color={getStatusColor(selectedJob.status)}
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Box>

                  {selectedJob.status === 'running' && (
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

                  {(selectedJob.status === 'completed' || selectedJob.status === 'COMPLETED') && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      Optimization completed successfully! All {selectedJob.maxIterations || 3} iterations finished.
                    </Alert>
                  )}

                  {selectedJob.error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {selectedJob.error}
                    </Alert>
                  )}

                  {selectedJob.status === 'running' && (
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
        <Card sx={{ mt: showCurrentJob && jobId ? 3 : 0 }}>
          <CardContent>
            {!showCurrentJob && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <IconButton onClick={fetchJobs} disabled={loading} size="small">
                  <RefreshIcon />
                </IconButton>
              </Box>
            )}

            <List sx={{ py: 0 }}>
            {jobs.map((job, index) => {
              // Ensure job has required properties
              const jobId = job?.id || job?.jobId || `unknown-${index}`;
              const jobStatus = job?.status || 'unknown';
              const jobCreatedAt = job?.createdAt || job?.submittedAt || new Date();
              
              return (
                <ListItem
                  key={jobId}
                  button
                  onClick={() => {
                    setSelectedJob({...job, id: jobId});
                    // If job is completed, trigger the results view
                    if ((jobStatus === 'completed' || jobStatus === 'COMPLETED') && onJobComplete) {
                      onJobComplete({...job, id: jobId});
                    }
                  }}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 1,
                    backgroundColor: index === 0 ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                    '&:hover': {
                      backgroundColor: 'rgba(25, 118, 210, 0.12)',
                    }
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2" fontWeight={index === 0 ? 600 : 400}>
                        {new Date(jobCreatedAt).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="body2" color="text.secondary">
                        {jobStatus === 'running' && `In Progress • ${job.progress || 0}%`}
                        {(jobStatus === 'completed' || jobStatus === 'COMPLETED') && 
                          <span style={{ color: '#4caf50', fontWeight: 500 }}>
                            ✓ Completed • Click to view results
                          </span>
                        }
                        {jobStatus === 'failed' && <span style={{ color: '#f44336' }}>✗ Failed</span>}
                        {jobStatus === 'pending' && 'Pending...'}
                      </Typography>
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
