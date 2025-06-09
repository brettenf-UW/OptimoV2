import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { FileUpload as FileUploadType, UploadedFiles } from '../types';

interface FileUploadProps {
  onFilesChange: (files: UploadedFiles) => void;
  uploadedFiles: UploadedFiles;
}

const REQUIRED_FILES = [
  { key: 'studentInfo', label: 'Student Info', filename: 'Student_Info.csv' },
  { key: 'studentPreferences', label: 'Student Preferences', filename: 'Student_Preference_Info.csv' },
  { key: 'teacherInfo', label: 'Teacher Info', filename: 'Teacher_Info.csv' },
  { key: 'teacherUnavailability', label: 'Teacher Unavailability', filename: 'Teacher_unavailability.csv' },
  { key: 'sectionsInfo', label: 'Sections Information', filename: 'Sections_Information.csv' },
];

const OPTIONAL_FILES = [
  { key: 'periods', label: 'Period Information', filename: 'Period.csv' },
];

export const FileUpload: React.FC<FileUploadProps> = ({ onFilesChange, uploadedFiles }) => {
  const [fileStatuses, setFileStatuses] = React.useState<Record<string, FileUploadType>>({});

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = { ...uploadedFiles };
    const newStatuses = { ...fileStatuses };

    acceptedFiles.forEach((file) => {
      // Match file to expected filenames
      const allFiles = [...REQUIRED_FILES, ...OPTIONAL_FILES];
      const matchedFile = allFiles.find(
        (f) => file.name.toLowerCase() === f.filename.toLowerCase()
      );

      if (matchedFile) {
        newFiles[matchedFile.key as keyof UploadedFiles] = file;
        newStatuses[matchedFile.key] = {
          name: file.name,
          file: file,
          status: 'success',
        };
      } else {
        // Handle unmatched files
        const key = file.name.replace('.csv', '');
        newStatuses[key] = {
          name: file.name,
          file: file,
          status: 'error',
          error: 'File name does not match expected format',
        };
      }
    });

    setFileStatuses(newStatuses);
    onFilesChange(newFiles);
  }, [uploadedFiles, fileStatuses, onFilesChange]);

  const removeFile = (key: string) => {
    const newFiles = { ...uploadedFiles };
    delete newFiles[key as keyof UploadedFiles];
    
    const newStatuses = { ...fileStatuses };
    delete newStatuses[key];
    
    setFileStatuses(newStatuses);
    onFilesChange(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: true,
  });

  const renderFileList = (files: typeof REQUIRED_FILES, required: boolean) => {
    return files.map((fileInfo) => {
      const uploadedFile = uploadedFiles[fileInfo.key as keyof UploadedFiles];
      const status = fileStatuses[fileInfo.key];

      return (
        <ListItem key={fileInfo.key}>
          <ListItemIcon>
            {uploadedFile ? (
              <CheckCircleIcon color="success" />
            ) : status?.status === 'error' ? (
              <ErrorIcon color="error" />
            ) : (
              <FileIcon color={required ? 'error' : 'disabled'} />
            )}
          </ListItemIcon>
          <ListItemText
            primary={fileInfo.label}
            secondary={
              uploadedFile
                ? uploadedFile.name
                : `Expected: ${fileInfo.filename} ${required ? '(Required)' : '(Optional)'}`
            }
          />
          {uploadedFile && (
            <IconButton
              edge="end"
              aria-label="delete"
              onClick={() => removeFile(fileInfo.key)}
            >
              <DeleteIcon />
            </IconButton>
          )}
        </ListItem>
      );
    });
  };

  const allRequiredFilesUploaded = REQUIRED_FILES.every(
    (f) => uploadedFiles[f.key as keyof UploadedFiles]
  );

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          mb: 3,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive
            ? 'Drop the CSV files here...'
            : 'Drag and drop CSV files here, or click to select'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload all required CSV files to proceed with optimization
        </Typography>
      </Paper>

      {!allRequiredFilesUploaded && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Please upload all required files before submitting a job.
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>
        Required Files
      </Typography>
      <Paper sx={{ mb: 3 }}>
        <List>{renderFileList(REQUIRED_FILES, true)}</List>
      </Paper>

      <Typography variant="h6" gutterBottom>
        Optional Files
      </Typography>
      <Paper>
        <List>{renderFileList(OPTIONAL_FILES, false)}</List>
      </Paper>
    </Box>
  );
};