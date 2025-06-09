# OptimoV2 Frontend

A React-based web interface for the OptimoV2 class schedule optimization system. This application provides an intuitive UI for uploading scheduling data, configuring optimization parameters, monitoring job progress, and downloading results.

## Features

- **File Upload**: Drag-and-drop interface for uploading CSV files
- **Job Submission**: Configure optimization parameters and submit jobs
- **Real-time Status Tracking**: Monitor job progress with live updates
- **Results Download**: Download optimized schedules and reports
- **Material-UI Design**: Clean, professional interface
- **GitHub Pages Ready**: Configured for easy deployment

## Prerequisites

- Node.js 16+ and npm
- Git (for version control)

## Setup Instructions

### 1. Install Dependencies

```bash
cd optimo-frontend
npm install
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=https://your-api-endpoint.com/api
```

### 3. Run Development Server

```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Deployment

### GitHub Pages

1. Update the `homepage` field in `package.json`:
   ```json
   "homepage": "https://yourusername.github.io/OptimoV2"
   ```

2. Deploy to GitHub Pages:
   ```bash
   npm run deploy
   ```

### Automated Deployment

The project includes a GitHub Actions workflow that automatically deploys to GitHub Pages when you push to the `main` branch.

## Project Structure

```
optimo-frontend/
├── public/               # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── FileUpload.tsx
│   │   ├── JobSubmission.tsx
│   │   ├── JobStatus.tsx
│   │   └── Results.tsx
│   ├── services/        # API service layer
│   │   └── api.ts
│   ├── types/           # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx          # Main application component
│   └── index.tsx        # Application entry point
├── .github/
│   └── workflows/       # GitHub Actions
└── package.json

```

## Component Overview

### FileUpload
- Drag-and-drop file upload interface
- Validates required vs optional files
- Shows upload status for each file

### JobSubmission
- Optimization parameter configuration
- Utilization target sliders
- AI provider selection
- Job submission handling

### JobStatus
- Real-time job progress tracking
- Job history list
- Auto-refresh for active jobs
- Cancel job functionality

### Results
- Download individual result files
- Download all results at once
- Shows job completion details

## API Integration

The application expects the following API endpoints:

- `POST /api/jobs` - Submit new optimization job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/:id` - Get job status
- `POST /api/jobs/:id/cancel` - Cancel job
- `GET /api/jobs/:id/results/:type` - Download result file

## Required CSV Files

The system requires these CSV files:
- `Student_Info.csv` - Student enrollment data
- `Teacher_Info.csv` - Teacher availability
- `Course_Info.csv` - Course definitions
- `Room_Info.csv` - Room capacity and features

Optional files:
- `Student_Requests.csv` - Student course preferences
- `Teacher_Preferences.csv` - Teacher scheduling preferences

## Development

### Available Scripts

- `npm start` - Run development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run deploy` - Deploy to GitHub Pages

### Code Style

The project uses TypeScript for type safety. Follow these conventions:
- Use functional components with hooks
- Define interfaces for all props and state
- Keep components focused and reusable
- Use Material-UI components consistently

## Troubleshooting

### Build Issues
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### Deployment Issues
- Ensure GitHub Pages is enabled in repository settings
- Check that the `homepage` field in `package.json` is correct
- Verify GitHub Actions has permissions to deploy

## Future Enhancements

- Add authentication/authorization
- Implement job result caching
- Add data visualization for schedules
- Support for multiple file formats
- Real-time collaboration features