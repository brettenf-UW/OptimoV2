# PhD-Level Automated Testing & Debugging System for OptimoV2

## Overview
This document outlines an automated testing and debugging system that will:
1. Submit test jobs automatically
2. Monitor job execution
3. Diagnose failures
4. Apply fixes
5. Retry until successful

## Automated Testing Script

The `automated_test_system.py` script will:
- Use existing CSV files from previous uploads
- Submit jobs directly to AWS Batch
- Monitor job status in real-time
- Analyze CloudWatch logs on failure
- Suggest and apply fixes automatically
- Generate detailed diagnostic reports

## Key Features

### 1. Direct Job Submission
- Bypasses frontend to test Batch directly
- Uses known good CSV files
- Submits with proper environment variables

### 2. Real-Time Monitoring
- Polls DynamoDB for job status
- Streams CloudWatch logs
- Detects failure patterns

### 3. Automated Diagnostics
- Parses error messages
- Identifies common issues:
  - File not found errors
  - Permission denied
  - Missing environment variables
  - Container crashes
  - Memory/CPU issues

### 4. Self-Healing Actions
- Updates IAM policies
- Fixes environment variables
- Rebuilds containers if needed
- Updates job definitions

### 5. Comprehensive Reporting
- Generates markdown reports
- Tracks all attempts
- Documents fixes applied
- Provides success metrics

## Running the System

```bash
python automated_test_system.py --iterations 10 --fix-mode auto
```

Options:
- `--iterations`: Maximum attempts before giving up
- `--fix-mode`: auto/manual/report-only
- `--use-test-data`: Use synthetic test data
- `--verbose`: Detailed logging

## Expected Outcomes

The system will continue testing until:
1. A job completes successfully (8-15 minutes runtime)
2. Maximum iterations reached
3. Unrecoverable error detected

## Benefits

1. **No Manual Testing**: Automated submission and monitoring
2. **Rapid Iteration**: Tests and fixes in minutes
3. **Pattern Recognition**: Learns from failures
4. **Documentation**: Auto-generates fix reports
5. **Production Ready**: Validates entire pipeline