import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Grid,
  Slider,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { UploadedFiles, OptimizationParameters } from '../types';
import api from '../services/api';

interface JobSubmissionProps {
  uploadedFiles: UploadedFiles;
  onJobSubmitted: (jobId: string) => void;
}

export const JobSubmission: React.FC<JobSubmissionProps> = ({
  uploadedFiles,
  onJobSubmitted,
}) => {
  const [parameters, setParameters] = useState<OptimizationParameters>({
    maxIterations: 3,
    minUtilization: 0.75,
    maxUtilization: 1.15,
    optimalMinUtilization: 0.8,
    optimalMaxUtilization: 1.0,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allRequiredFilesPresent = 
    uploadedFiles.studentInfo &&
    uploadedFiles.studentPreferences &&
    uploadedFiles.teacherInfo &&
    uploadedFiles.teacherUnavailability &&
    uploadedFiles.sectionsInfo;

  const handleSubmit = async () => {
    if (!allRequiredFilesPresent) {
      setError('Please upload all required files before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const job = await api.submitJob({
        files: uploadedFiles,
        parameters,
      });
      onJobSubmitted(job.id);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to submit job. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleParameterChange = (field: keyof OptimizationParameters, value: any) => {
    setParameters({ ...parameters, [field]: value });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" component="h2" gutterBottom>
          Optimization Parameters
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Max Iterations"
              type="number"
              value={parameters.maxIterations}
              onChange={(e) => handleParameterChange('maxIterations', parseInt(e.target.value))}
              inputProps={{ min: 1, max: 10 }}
              helperText="Maximum number of optimization iterations"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography gutterBottom>
              Utilization Targets (Min: {(parameters.minUtilization * 100).toFixed(0)}% - Max: {(parameters.maxUtilization * 100).toFixed(0)}%)
            </Typography>
            <Box sx={{ px: 2 }}>
              <Slider
                value={[parameters.minUtilization, parameters.maxUtilization]}
                onChange={(e, value) => {
                  const [min, max] = value as number[];
                  handleParameterChange('minUtilization', min);
                  handleParameterChange('maxUtilization', max);
                }}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                min={0.5}
                max={1.5}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.75, label: '75%' },
                  { value: 1, label: '100%' },
                  { value: 1.25, label: '125%' },
                  { value: 1.5, label: '150%' },
                ]}
              />
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Typography gutterBottom>
              Optimal Utilization Range (Min: {(parameters.optimalMinUtilization * 100).toFixed(0)}% - Max: {(parameters.optimalMaxUtilization * 100).toFixed(0)}%)
            </Typography>
            <Box sx={{ px: 2 }}>
              <Slider
                value={[parameters.optimalMinUtilization, parameters.optimalMaxUtilization]}
                onChange={(e, value) => {
                  const [min, max] = value as number[];
                  handleParameterChange('optimalMinUtilization', min);
                  handleParameterChange('optimalMaxUtilization', max);
                }}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                min={0.5}
                max={1.5}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.75, label: '75%' },
                  { value: 1, label: '100%' },
                  { value: 1.25, label: '125%' },
                  { value: 1.5, label: '150%' },
                ]}
              />
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="contained"
                size="large"
                onClick={handleSubmit}
                disabled={!allRequiredFilesPresent || isSubmitting}
                startIcon={isSubmitting ? <CircularProgress size={20} /> : <SendIcon />}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Optimization Job'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};