# Container Update Checklist - Fix Batch Job Environment Variables

## Overview
Updating optimo-batch container from v6 to v7 to fix environment variable mismatch between Lambda and container.

## Pre-Update Status
- [ ] Current container version: v6
- [ ] Issue: Container expects wrong environment variables (jobId vs JOB_ID)
- [ ] Job failures: "Essential container in task exited"

## Phase 1: Preparation ✅
- [ ] Backup current job definition
- [ ] Document container versions
- [ ] Review updated script (run_batch_job_updated.py)
- [ ] Verify Docker is installed and working

## Phase 2: Build & Test Locally
- [ ] Copy updated script over original
- [ ] Build Docker image locally (optimo-batch:v7-test)
- [ ] Run basic local test to verify script starts correctly
- [ ] Check for any obvious errors

## Phase 3: Deploy to ECR
- [ ] Login to ECR
- [ ] Tag image for ECR (optimo-batch:v7)
- [ ] Push image to ECR
- [ ] Verify image upload in AWS Console

## Phase 4: Update Job Definition
- [ ] Create new job definition revision with v7 image
- [ ] Verify all environment variables are included
- [ ] Confirm 72 vCPUs and 140GB memory settings
- [ ] Note new job definition revision number

## Phase 5: Test & Validate
- [ ] Submit test job through UI
- [ ] Monitor CloudWatch logs
- [ ] Verify job progresses past previous failure point
- [ ] Check job reaches "RUNNING" status
- [ ] Confirm files are downloading correctly
- [ ] Wait for job completion or significant progress

## Phase 6: Cleanup
- [ ] Document successful update
- [ ] Remove test images from local Docker
- [ ] Update documentation if needed

## Rollback Plan
If issues occur:
- [ ] Have job definition backup ready
- [ ] Know how to revert to v6 quickly
- [ ] Keep v6 image in ECR (don't delete)

## Important Notes
- **DO NOT** change compute environment settings
- **DO NOT** modify Lambda functions
- **DO NOT** alter IAM roles or permissions
- **ONLY** updating the container script

## Success Metrics
- [ ] Jobs start successfully (no immediate failures)
- [ ] Environment variables are read correctly
- [ ] Files download from S3
- [ ] Optimization process begins

## Commands Reference
```bash
# Backup command
aws batch describe-job-definitions --job-definition-name optimo-job-updated --status ACTIVE --region us-west-2 > job_definition_backup.json

# Build command
docker build -t optimo-batch:v7-test .

# ECR push commands
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 529088253685.dkr.ecr.us-west-2.amazonaws.com
docker tag optimo-batch:v7-test 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7
docker push 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7

# Monitor logs
aws logs tail /aws/batch/job --follow --region us-west-2
```

---
Started: [DATE]
Completed: [DATE]
Result: [SUCCESS/FAILED]
Notes: [Any important observations]

Update Progress: Tue Jun 10 22:41:53 PDT 2025
✅ Phase 1: Preparation - Complete
✅ Phase 2: Build & Test - Complete (built v7)
✅ Phase 3: Deploy to ECR - Complete
✅ Phase 4: Job Definition - Complete (revision 7)
🔄 Phase 5: Testing - Ready to test
