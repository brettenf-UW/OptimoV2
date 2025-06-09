# OptimoV2 Frontend Documentation

## Overview

The OptimoV2 frontend is a modern React application built with TypeScript that provides a user-friendly interface for school schedule optimization. It uses Material-UI for styling and Recharts for data visualization.

## Technology Stack

- **React 18.2** - Core UI framework
- **TypeScript 4.9** - Type safety and better development experience
- **Material-UI 5.14** - Modern component library following Material Design
- **Recharts 2.9** - Interactive data visualization
- **Axios** - HTTP client for API communication
- **React Dropzone** - Drag-and-drop file uploads

## Architecture

### Component Structure

```
src/
├── components/
│   ├── FileUpload.tsx       # CSV file upload with drag-and-drop
│   ├── JobSubmission.tsx    # Configuration and job submission
│   ├── JobStatus.tsx        # Real-time job monitoring with iteration progress
│   └── Results.tsx          # Dashboard with metrics and visualizations
├── services/
│   └── api.ts              # API service layer
├── types/
│   └── index.ts            # TypeScript type definitions
└── App.tsx                 # Main application component
```

### Key Features

1. **File Upload**
   - Drag-and-drop interface for CSV files
   - File validation and status indicators
   - Support for required and optional files
   - Visual feedback for upload status

2. **Job Configuration**
   - Adjustable optimization parameters
   - Visual sliders for utilization targets
   - Max iterations setting
   - Real-time validation

3. **Progress Monitoring**
   - Overall job progress bar
   - Iteration-by-iteration breakdown
   - Step-by-step status within each iteration
   - Real-time updates every 2 seconds
   - Cancel job functionality

4. **Results Dashboard**
   - 5 key metric cards with hover animations
   - Section utilization bar chart
   - Teacher workload pie chart
   - Optimization summary
   - Subtle download links for all outputs

## API Integration

The frontend communicates with the backend through a RESTful API:

### Endpoints

- `POST /api/upload` - Upload CSV files
- `POST /api/jobs` - Submit optimization job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/:jobId` - Get job status
- `POST /api/jobs/:jobId/cancel` - Cancel running job
- `GET /api/jobs/:jobId/results/:type` - Download results

### Mock Server

For development and testing, a mock server (`mock-server.js`) simulates the backend:
- Runs on port 5000
- Simulates job progress with realistic timing
- Provides mock data for testing all features

## Running the Frontend

### Development Mode

```bash
cd optimo-frontend
npm install        # First time only
npm run dev       # Starts both mock server and React app
```

### Production Build

```bash
npm run build     # Creates optimized production build
```

### Testing

Use the provided test scripts:
- `run_frontend.bat` - Simple batch file to start servers
- `test_frontend.ps1` - PowerShell script with instructions

## UI/UX Design Principles

1. **Progressive Disclosure**
   - Step-by-step workflow guides users
   - Complex features revealed as needed

2. **Visual Feedback**
   - Loading states with skeletons
   - Progress indicators for all operations
   - Success/error states clearly indicated

3. **Responsive Design**
   - Adapts to different screen sizes
   - Mobile-friendly layout
   - Accessible color contrasts

4. **Modern Aesthetics**
   - Clean Material Design components
   - Subtle animations and transitions
   - Professional color scheme
   - Consistent spacing and typography

## Component Details

### FileUpload Component
- Validates file names against expected format
- Shows upload status for each file
- Indicates required vs optional files
- Drag-and-drop with visual feedback

### JobSubmission Component
- Parameter configuration with visual sliders
- Input validation before submission
- Clear call-to-action button
- Error handling with user-friendly messages

### JobStatus Component
- Real-time progress updates
- Iteration-by-iteration breakdown:
  - Running MILP optimization
  - Analyzing utilization
  - Running Gemini AI analysis
  - Applying optimizations
  - Finalizing iteration
- Visual stepper for iteration progress
- Cancel functionality for running jobs

### Results Component
- **Metric Cards**: Key performance indicators
  - Overall utilization percentage
  - Sections optimized count
  - Students placed successfully
  - Average teacher load
  - Constraint violations
- **Visualizations**:
  - Horizontal bar chart for section utilization
  - Pie chart for teacher workload distribution
  - Color-coded for easy interpretation
- **Summary**: Clear text summary of optimizations
- **Downloads**: Subtle links for CSV and report downloads

## State Management

The app uses React's built-in state management:
- Component-level state for UI interactions
- Props for parent-child communication
- Effect hooks for side effects and API calls

## Error Handling

- API errors displayed with user-friendly messages
- Network failures handled gracefully
- Input validation prevents invalid submissions
- Fallback UI for error states

## Performance Optimizations

- Lazy loading for heavy components
- Debounced API calls
- Optimized re-renders with React.memo
- Efficient chart rendering with Recharts

## Future Enhancements

1. **Authentication & Authorization**
   - User login system
   - Role-based access control
   - Multi-tenant support

2. **Advanced Features**
   - Save/load optimization configurations
   - Compare multiple optimization runs
   - Export reports to PDF
   - Email notifications on job completion

3. **Improved Visualizations**
   - Interactive schedule grid view
   - Conflict visualization
   - Before/after comparison view
   - Custom report builder

## Deployment

The frontend is designed for easy deployment:
- Static build can be hosted on any web server
- GitHub Pages ready with homepage configuration
- Environment variables for API endpoints
- Docker-ready with multi-stage builds

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers on iOS/Android

## Accessibility

- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode compatible
- Focus indicators for interactive elements