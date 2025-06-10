# OptimoV2 Quick Start Guide

## Overview
OptimoV2 is an AI-powered class schedule optimization system that uses Mixed Integer Linear Programming (MILP) and Gemini AI to create optimal schedules while maximizing section utilization.

## Prerequisites
- AWS Account with appropriate permissions
- Node.js 16+ and npm
- Python 3.9+
- Git

## Quick Start (Using Deployed System)

### 1. Access the Application
Navigate to: https://brettenf-uw.github.io/OptimoV2

### 2. Upload Your Data Files
Required CSV files:
- `Period.csv` - Class periods/time slots
- `Sections_Information.csv` - Available sections with capacities
- `Student_Info.csv` - Student enrollment data
- `Student_Preference_Info.csv` - Student course preferences
- `Teacher_Info.csv` - Teacher assignments
- `Teacher_unavailability.csv` - Teacher scheduling constraints

### 3. Configure Optimization Parameters
- **Max Iterations**: Number of optimization rounds (default: 3)
- **Min Utilization**: Minimum acceptable section fill rate (default: 0.75)
- **Max Utilization**: Maximum section capacity (default: 1.15)
- **Optimal Range**: Target utilization range (0.8 - 1.0)

### 4. Submit and Monitor
- Click "Submit Job" to start optimization
- Monitor progress in real-time
- View iteration-by-iteration improvements

### 5. Download Results
Once complete, download:
- `Master_Schedule.csv` - Final optimized schedule
- `Student_Assignments.csv` - Student-to-section mappings
- `Teacher_Schedule.csv` - Teacher assignments
- `Constraint_Violations.csv` - Any unresolved conflicts

## Local Development Setup

### Frontend Development
```bash
cd optimo-frontend
npm install
npm start
```

The frontend will run at http://localhost:3000

### Backend Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run local optimization
python scripts/run_pipeline.py
```

## Deployment

### Deploy Frontend Updates
```bash
cd optimo-frontend
npm run build
npm run deploy
```

### Deploy Lambda Functions
```bash
cd lambda
./update_lambda.sh
```

## Architecture Overview

```
Frontend (React)          Backend (AWS)
    │                         │
    ├─ Upload Files ─────────→ S3 Input Bucket
    │                         │
    ├─ Submit Job ──────────→ API Gateway → Lambda
    │                         │                ↓
    ├─ Monitor Status ←──────┤           AWS Batch
    │                         │                ↓
    └─ Download Results ←────┤           S3 Output Bucket
```

## Key Features

### 1. Multi-Iteration Optimization
- Initial MILP solve for base schedule
- AI-powered analysis of utilization
- Iterative improvements via SPLIT/MERGE/ADD/REMOVE actions

### 2. Real-Time Progress Tracking
- Live status updates
- Per-iteration progress visualization
- Detailed metrics and charts

### 3. Comprehensive Results
- Utilization distribution charts
- Teacher load analysis
- Constraint violation reporting
- Downloadable CSV results

## Troubleshooting

### Common Issues

1. **Job Stuck in RUNNABLE**
   - Check AWS Batch compute environment
   - Verify Gurobi license is configured

2. **CORS Errors**
   - Ensure API Gateway CORS is enabled
   - Check Lambda function CORS headers

3. **Results Not Loading**
   - Verify S3 bucket permissions
   - Check Lambda execution role

### Debug Commands
```bash
# Check job status
aws dynamodb get-item --table-name optimo-jobs --key '{"jobId": {"S": "YOUR-JOB-ID"}}'

# View Lambda logs
aws logs tail /aws/lambda/optimo-jobs-list --follow

# Check Batch job
aws batch describe-jobs --jobs YOUR-BATCH-JOB-ID
```

## Support

For issues or questions:
1. Check CloudWatch logs for detailed error messages
2. Verify all AWS services are running in us-west-2
3. Ensure IAM roles have required permissions

## Next Steps
- Configure email notifications for job completion
- Set up CloudWatch alarms for failures
- Customize optimization parameters for your institution