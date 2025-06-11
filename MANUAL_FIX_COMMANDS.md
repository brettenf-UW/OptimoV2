# OptimoV2 Manual Fix Commands

## Current Situation
- ✅ Container v7 is built and pushed to ECR
- ✅ Job definition `optimo-job-def-v7` is created
- ❌ Lambda is still using old configuration (wrong job definition and S3 bucket)
- ❌ Your recent job used the old broken container

## Step 1: Update Lambda Environment Variables

Run this command to update the Lambda to use the correct job definition and S3 bucket:

```bash
aws lambda update-function-configuration \
  --function-name optimo-unified-handler \
  --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v7}' \
  --region us-west-2
```

## Step 2: Wait for Lambda Update

Check the update status (wait until State is "Active" and LastUpdateStatus is "Successful"):

```bash
aws lambda get-function-configuration --function-name optimo-unified-handler --region us-west-2 --query '{State:State,LastUpdateStatus:LastUpdateStatus}'
```

## Step 3: Verify Lambda Configuration

Confirm the Lambda has the correct environment variables:

```bash
aws lambda get-function-configuration --function-name optimo-unified-handler  --region us-west-2 --query 'Environment.Variables' | grep -E "JOB_DEFINITION|S3_INPUT_BUCKET"
```

Expected output:
```
"S3_INPUT_BUCKET": "optimo-input-files-v2",
"JOB_DEFINITION": "optimo-job-def-v7"
```

## Step 4: Test New Job Submission

1. Go to https://brettenf-uw.github.io/OptimizationProjectFrontEnd/
2. Upload your CSV files
3. Submit a new optimization job
4. Note the new job ID

## Step 5: Monitor the New Job

Replace `<JOB_ID>` with your actual job ID:

```bash
# Check job status in DynamoDB
aws dynamodb get-item \
  --table-name optimo-jobs \
  --key '{"jobId": {"S": "<JOB_ID>"}}' \
  --region us-west-2 \
  --query 'Item.{status:status.S,progress:progress.N,message:currentStep.S}'

# Find the Batch job ID
aws batch list-jobs \
  --job-queue optimo-job-queue \
  --region us-west-2 \
  --max-results 10 \
  --query 'jobSummaryList[?contains(jobName, `<JOB_ID>`)].{name:jobName,id:jobId,status:status}'
```

## Step 6: Check CloudWatch Logs

Once you have the Batch job ID from step 5:

```bash
# Get log stream name
aws logs describe-log-streams \
  --log-group-name /aws/batch/job \
  --order-by LastEventTime \
  --descending \
  --limit 5 \
  --region us-west-2 \
  --query 'logStreams[*].logStreamName'

# View logs (replace LOG_STREAM_NAME with actual value)
aws logs get-log-events \
  --log-group-name /aws/batch/job \
  --log-stream-name "<LOG_STREAM_NAME>" \
  --start-from-head \
  --region us-west-2 \
  --output text | grep -E "INFO|ERROR|WARNING"
```

## Expected Success Indicators

✅ Job runs for more than 3 minutes (not failing at 3 min or 1 second)  
✅ Logs show "Running command: python /app/scripts/run_pipeline.py"  
✅ Logs show optimization iterations progressing  
✅ Job status changes to "SUCCEEDED"  
✅ Output files appear in S3  

## If Job Still Fails

### Check which container/definition was used:

```bash
# Get job details
aws batch describe-jobs \
  --jobs "<BATCH_JOB_ID>" \
  --region us-west-2 \
  --query 'jobs[0].{definition:jobDefinition,image:container.image,status:status,reason:statusReason}'
```

### If using wrong definition:
- The Lambda update may not have completed
- Try resubmitting after 5 minutes
- Or manually deploy the Lambda code:

```bash
cd /mnt/c/dev/OptimoV2/lambda
./deploy_unified.sh
```

### If still seeing "can't find run_pipeline.py":
The container v7 may not have built correctly. Rebuild:

```bash
cd /mnt/c/dev/OptimoV2
# Ensure the fixed script is in place
cp scripts/run_batch_job_fixed.py scripts/run_batch_job.py

# Rebuild and push
docker build -t optimo-batch:v7 .
docker tag optimo-batch:v7 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 529088253685.dkr.ecr.us-west-2.amazonaws.com
docker push 529088253685.dkr.ecr.us-west-2.amazonaws.com/optimo-batch:v7
```

## Quick Status Check Script

Save this as `check_optimo_status.sh`:

```bash
#!/bin/bash
echo "=== OptimoV2 Status Check ==="
echo

echo "1. Lambda Configuration:"
aws lambda get-function-configuration \
  --function-name optimo-unified-handler \
  --region us-west-2 \
  --query 'Environment.Variables.{JOB_DEF:JOB_DEFINITION,S3_BUCKET:S3_INPUT_BUCKET}' \
  --output table

echo
echo "2. Active Job Definitions:"
aws batch describe-job-definitions \
  --status ACTIVE \
  --region us-west-2 \
  --query 'jobDefinitions[?contains(jobDefinitionName, `optimo`)].{Name:jobDefinitionName,Rev:revision,Image:containerProperties.image}' \
  --output table

echo
echo "3. Recent Jobs (last 5):"
aws batch list-jobs \
  --job-queue optimo-job-queue \
  --region us-west-2 \
  --max-results 5 \
  --query 'jobSummaryList[*].{Name:jobName,Status:status,Created:createdAt}' \
  --output table
```

## Success Criteria

Your optimization system is working when:
1. Lambda uses `optimo-job-def-v7` and `optimo-input-files-v2`
2. Jobs run for 8-15 minutes (not failing immediately)
3. CloudWatch logs show pipeline execution and iterations
4. Output files appear in S3 bucket
5. Job status in DynamoDB shows "SUCCEEDED"

## Next Optimization Job Should Work!

After completing steps 1-3, your next job submission should use the fixed container and complete successfully.