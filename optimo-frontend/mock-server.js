const express = require('express');
const multer = require('multer');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.use(cors());
app.use(express.json());

// In-memory job storage
const jobs = {};

// Mock endpoints
app.post('/api/upload', upload.array('files'), (req, res) => {
  console.log('Files uploaded:', req.files.map(f => f.originalname));
  res.json({
    success: true,
    fileIds: req.files.map(f => f.filename)
  });
});

app.post('/api/jobs', upload.any(), (req, res) => {
  const jobId = uuidv4();
  
  // Parse parameters from request
  let maxIterations = 3; // default
  try {
    const params = req.body.parameters ? JSON.parse(req.body.parameters) : {};
    maxIterations = params.maxIterations || 3;
  } catch (e) {
    console.log('Could not parse parameters, using defaults');
  }
  
  jobs[jobId] = {
    id: jobId,
    status: 'pending',
    progress: 0,
    createdAt: new Date(),
    updatedAt: new Date(),
    currentStep: 'Initializing optimization...',
    maxIterations: maxIterations
  };
  
  console.log(`Job ${jobId} created`);
  
  // Simulate job progress with iteration details
  let progress = 0;
  const progressIncrement = 100 / (maxIterations * 5); // 5 steps per iteration
  
  const iterationSteps = [
    'Running MILP optimization...',
    'Analyzing utilization...',
    'Running Gemini AI analysis...',
    'Applying optimizations...',
    'Finalizing iteration...'
  ];
  
  const interval = setInterval(() => {
    progress += progressIncrement;
    if (progress > 100) progress = 100;
    
    jobs[jobId].progress = Math.floor(progress);
    jobs[jobId].updatedAt = new Date();
    
    // Calculate current iteration and step
    const currentIteration = Math.floor(progress / (100 / maxIterations));
    const iterationProgress = (progress % (100 / maxIterations)) / (100 / maxIterations);
    const currentStepIndex = Math.floor(iterationProgress * iterationSteps.length);
    
    if (progress < 100) {
      jobs[jobId].currentStep = `Iteration ${currentIteration}: ${iterationSteps[currentStepIndex] || 'Processing...'}`;
    }
    
    if (progress >= 100) {
      jobs[jobId].status = 'completed';
      jobs[jobId].currentStep = 'Optimization complete!';
      jobs[jobId].results = {
        masterSchedule: `/api/jobs/${jobId}/results/masterSchedule`,
        studentAssignments: `/api/jobs/${jobId}/results/studentAssignments`,
        teacherSchedule: `/api/jobs/${jobId}/results/teacherSchedule`,
        constraintViolations: `/api/jobs/${jobId}/results/constraintViolations`,
        utilizationReport: `/api/jobs/${jobId}/results/utilizationReport`
      };
      clearInterval(interval);
    } else if (progress >= 10 && jobs[jobId].status === 'pending') {
      jobs[jobId].status = 'running';
    }
  }, 1500); // Update every 1.5 seconds for smoother progress
  
  res.json(jobs[jobId]);
});

// Get all jobs
app.get('/api/jobs', (req, res) => {
  res.json(Object.values(jobs));
});

// Get specific job
app.get('/api/jobs/:jobId', (req, res) => {
  const job = jobs[req.params.jobId];
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  res.json(job);
});

// Cancel job
app.post('/api/jobs/:jobId/cancel', (req, res) => {
  const job = jobs[req.params.jobId];
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  job.status = 'cancelled';
  res.json({ success: true });
});

// Download result
app.get('/api/jobs/:jobId/results/:resultType', (req, res) => {
  const job = jobs[req.params.jobId];
  if (!job || job.status !== 'completed') {
    return res.status(404).json({ error: 'Results not ready' });
  }
  
  // Mock CSV content
  const mockData = {
    masterSchedule: 'Section,Period,Room\nS001,1,R101\nS002,2,R102',
    studentAssignments: 'Student,Section\nStudent001,S001\nStudent002,S002',
    teacherSchedule: 'Teacher,Section,Period\nTeacher001,S001,1\nTeacher002,S002,2',
    constraintViolations: 'Type,Count\nOvercapacity,0\nConflicts,0',
    utilizationReport: 'Section,Utilization\nS001,95%\nS002,87%'
  };
  
  const content = mockData[req.params.resultType] || 'No data available';
  
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', `attachment; filename="${req.params.resultType}.csv"`);
  res.send(content);
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log('\nAvailable endpoints:');
  console.log('  POST /api/upload');
  console.log('  POST /api/jobs');
  console.log('  GET  /api/jobs');
  console.log('  GET  /api/jobs/:jobId');
  console.log('  POST /api/jobs/:jobId/cancel');
  console.log('  GET  /api/jobs/:jobId/results/:resultType');
});