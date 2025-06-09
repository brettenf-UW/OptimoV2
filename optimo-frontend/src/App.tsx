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
  };

  const handleJobSubmitted = (jobId: string) => {
    setCurrentJobId(jobId);
    handleNext();
  };

  const handleJobComplete = (job: Job) => {
    setCompletedJob(job);
    handleNext();
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

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Paper elevation={3} sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
              Class Schedule Optimizer
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
                      {index === 2 && (
                        <JobStatus
                          jobId={currentJobId || undefined}
                          onJobComplete={handleJobComplete}
                        />
                      )}
                      {index === 3 && completedJob && (
                        <Results job={completedJob} />
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
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;