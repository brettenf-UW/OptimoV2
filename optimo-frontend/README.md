# OptimoV2 Frontend

React-based web application for the OptimoV2 class schedule optimization system.

## Features

- **File Upload**: Drag-and-drop CSV file uploads with validation
- **Job Management**: Submit, monitor, and cancel optimization jobs
- **Real-time Updates**: Live progress tracking with iteration details
- **Results Visualization**: Interactive charts and downloadable results
- **Job History**: View and access previous optimization runs

## Tech Stack

- React 18 with TypeScript
- Material-UI for components
- Recharts for data visualization
- Axios for API communication
- GitHub Pages for hosting

## Development

### Prerequisites
- Node.js 16+
- npm or yarn

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app runs at http://localhost:3000

### Environment Variables
Create a `.env` file:
```
REACT_APP_API_URL=https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod
```

For local development with mock server:
```
REACT_APP_API_URL=http://localhost:5000/api
```

## Project Structure

```
src/
├── components/         # React components
│   ├── FileUpload.tsx    # File upload interface
│   ├── JobSubmission.tsx # Job configuration and submission
│   ├── JobStatus.tsx     # Status monitoring and history
│   └── Results.tsx       # Results display and charts
├── services/          # API integration
│   └── api.ts           # API service layer
├── types/             # TypeScript definitions
├── App.tsx           # Main application component
└── index.tsx         # Application entry point
```

## Building & Deployment

### Production Build
```bash
npm run build
```

### Deploy to GitHub Pages
```bash
npm run deploy
```

The app is deployed to: https://brettenf-uw.github.io/OptimoV2

## API Integration

The frontend communicates with AWS services through API Gateway:

- **File Upload**: Uses presigned S3 URLs for secure uploads
- **Job Submission**: Sends jobs to AWS Batch via Lambda
- **Status Updates**: Polls for real-time progress
- **Results**: Downloads from S3 with presigned URLs

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - See LICENSE file for details