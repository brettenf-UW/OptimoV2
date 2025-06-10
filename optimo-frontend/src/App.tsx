import React, { useState } from 'react';
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  AppBar,
  Toolbar,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  Grid,
  Divider,
} from '@mui/material';
import { FileUpload } from './components/FileUpload';
import { JobSubmission } from './components/JobSubmission';
import { JobStatus } from './components/JobStatus';
import { Results } from './components/Results';
import { UploadedFiles, Job } from './types';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
  },
});

const steps = [
  {
    label: 'Upload Files',
    description: 'Upload required CSV files for optimization',
  },
  {
    label: 'Configure & Submit',
    description: 'Set optimization parameters and submit job',
  },
  {
    label: 'Monitor Progress',
    description: 'Track job status and progress',
  },
  {
    label: 'Download Results',
    description: 'Download optimized schedules',
  },
];

function App() {
  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFiles>({});
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [completedJob, setCompletedJob] = useState<Job | null>(null);
  const [selectedHistoryJob, setSelectedHistoryJob] = useState<Job | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setUploadedFiles({});
    setCurrentJobId(null);
    setCompletedJob(null);
    setSelectedHistoryJob(null);
  };

  const handleJobSubmitted = (jobId: string) => {
    setCurrentJobId(jobId);
    // Add a small delay before triggering refresh to ensure the job is in the database
    setTimeout(() => {
      setRefreshTrigger(prev => prev + 1); // Trigger history refresh
    }, 500);
    handleNext();
  };

  const handleJobComplete = (job: Job) => {
    setCompletedJob(job);
    if (job.id === currentJobId) {
      handleNext();
    }
  };

  const handleHistoryJobSelect = (job: Job | null) => {
    setSelectedHistoryJob(job);
    if (job) {
      // When selecting a job
      if (job.status === 'SUCCEEDED') {
        setCompletedJob(job);
        setActiveStep(3); // Jump to results step
      } else if (job.status === 'FAILED') {
        // For failed jobs, just select them but don't change step
        setCompletedJob(null);
      } else {
        // For running/pending jobs, show their progress
        setCompletedJob(null);
        // Don't change the active step, just highlight the job
      }
    } else {
      // When deselecting, always allow going back to submission
      setCompletedJob(null);
      // Keep the current step unless we were viewing results from history
      if (selectedHistoryJob && activeStep === 3 && completedJob?.id === selectedHistoryJob.id) {
        // If we were viewing history results, go back to the appropriate step
        if (currentJobId) {
          setActiveStep(2); // Go back to monitoring if there's a current job
        } else if (allRequiredFilesUploaded) {
          setActiveStep(1); // Go to submit if files are uploaded
        } else {
          setActiveStep(0); // Otherwise go to file upload
        }
      }
    }
  };

  const allRequiredFilesUploaded =
    uploadedFiles.studentInfo &&
    uploadedFiles.studentPreferences &&
    uploadedFiles.teacherInfo &&
    uploadedFiles.teacherUnavailability &&
    uploadedFiles.sectionsInfo;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              OptimoV2 - Schedule Optimization System
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Grid container spacing={3}>
            {/* Current Job Submission Section */}
            <Grid item xs={12} lg={8}>
              <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom>
                  Create New Optimization
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Upload your scheduling data and let OptimoV2 create an optimized class schedule
                  that maximizes utilization while respecting all constraints.
                </Typography>

                <Stepper activeStep={activeStep} orientation="vertical" sx={{ mt: 4 }}>
                  {steps.map((step, index) => (
                    <Step key={step.label}>
                      <StepLabel>{step.label}</StepLabel>
                      <StepContent>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {step.description}
                        </Typography>

                        <Box sx={{ mb: 2 }}>
                          {index === 0 && (
                            <FileUpload
                              uploadedFiles={uploadedFiles}
                              onFilesChange={setUploadedFiles}
                            />
                          )}
                          {index === 1 && (
                            <JobSubmission
                              uploadedFiles={uploadedFiles}
                              onJobSubmitted={handleJobSubmitted}
                            />
                          )}
                          {index === 2 && currentJobId && (
                            <JobStatus
                              jobId={currentJobId}
                              onJobComplete={handleJobComplete}
                              showJobsList={false}
                            />
                          )}
                          {index === 3 && completedJob && (
                            <>
                              <Results job={completedJob} />
                              {selectedHistoryJob && (
                                <Box sx={{ mt: 3 }}>
                                  <Button 
                                    variant="contained" 
                                    color="primary"
                                    onClick={handleReset}
                                    size="large"
                                  >
                                    Start New Optimization
                                  </Button>
                                </Box>
                              )}
                            </>
                          )}
                        </Box>

                        <Box sx={{ mb: 2 }}>
                          {index > 0 && (
                            <Button
                              variant="outlined"
                              onClick={handleBack}
                              sx={{ mt: 1, mr: 1 }}
                            >
                              Back
                            </Button>
                          )}
                          {index === 0 && (
                            <Button
                              variant="contained"
                              onClick={handleNext}
                              sx={{ mt: 1, mr: 1 }}
                              disabled={!allRequiredFilesUploaded}
                            >
                              Continue
                            </Button>
                          )}
                          {index === steps.length - 1 && (
                            <Button onClick={handleReset} sx={{ mt: 1, mr: 1 }}>
                              Start New Optimization
                            </Button>
                          )}
                        </Box>
                      </StepContent>
                    </Step>
                  ))}
                </Stepper>
              </Paper>
            </Grid>

            {/* Job History Section */}
            <Grid item xs={12} lg={4}>
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 3, 
                  backgroundColor: '#f8f9fa',
                  border: '1px solid #e9ecef'
                }}
              >
                <Typography 
                  variant="h5" 
                  gutterBottom 
                  sx={{ 
                    mb: 3,
                    pb: 2,
                    borderBottom: '2px solid #dee2e6'
                  }}
                >
                  Recent Job History
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  View and download results from your last 3 optimization runs
                </Typography>
                <Divider sx={{ mb: 3 }} />
                <JobStatus 
                  showCurrentJob={false}
                  onJobComplete={handleJobComplete}
                  onJobSelect={handleHistoryJobSelect}
                  selectedJobId={selectedHistoryJob?.id}
                  refreshTrigger={refreshTrigger}
                />
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;