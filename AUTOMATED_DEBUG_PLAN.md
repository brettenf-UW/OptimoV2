# OptimoV2 Automated Debug & Fix Plan

## Overview
This plan creates an automated system to:
1. Submit test jobs using existing CSV files
2. Monitor job execution
3. Diagnose failures automatically
4. Apply fixes without manual intervention
5. Retry until successful

## Implementation Steps

### 1. Create Test Data Set
- Use CSV files from `data/base/` directory
- Create minimal test set for faster debugging

### 2. Build Automated Test Runner
- `auto_test_submit.py` - Submits jobs programmatically
- `auto_monitor.py` - Monitors job status and logs
- `auto_fix.py` - Applies fixes based on error patterns

### 3. Error Pattern Recognition
Common errors and automated fixes:
- **Region not specified** → Set AWS_DEFAULT_REGION
- **S3 Access Denied** → Update IAM policies
- **Missing API Key** → Add to job definition
- **Container not found** → Rebuild and push
- **File not found** → Check S3 keys and paths

### 4. Automated Fix Application
- Parse CloudWatch logs
- Match error patterns
- Apply appropriate fix
- Resubmit job
- Repeat until success

### 5. Cleanup
After successful run:
- Archive old scripts
- Document final working configuration
- Create success verification script

## Scripts to Create

1. **auto_debug_runner.py** - Main orchestrator
2. **test_job_submitter.py** - Submits jobs via API
3. **log_analyzer.py** - Parses logs and identifies issues
4. **fix_applier.py** - Applies fixes automatically
5. **cleanup.sh** - Removes unnecessary files

## Success Criteria
- Job runs for 8-15 minutes
- Status changes to SUCCEEDED
- Output files appear in S3
- No errors in CloudWatch logs