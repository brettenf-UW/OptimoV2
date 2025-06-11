# PowerShell script to build and push container v9 with file download fix
Write-Host "=== Building OptimoV2 Container v9 with File Download Fix ===" -ForegroundColor Blue

$REGION = "us-west-2"
$ACCOUNT_ID = "529088253685"
$ECR_REPO = "optimo-batch"
$TAG = "v9"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build the container
Write-Host "Building Docker image with fixed run_batch_job.py..." -ForegroundColor Yellow
docker build -t "${ECR_REPO}:${TAG}" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

# Tag for ECR
Write-Host "Tagging image..." -ForegroundColor Yellow
docker tag "${ECR_REPO}:${TAG}" "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${ECR_REPO}:${TAG}"

# Push to ECR
Write-Host "Pushing to ECR..." -ForegroundColor Yellow
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${ECR_REPO}:${TAG}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker push failed!" -ForegroundColor Red
    exit 1
}

# Update job definition to use v9
Write-Host "`nUpdating job definition to use container v9..." -ForegroundColor Yellow

$jobDef = @{
    jobDefinitionName = "optimo-job-def-v10"
    type = "container"
    containerProperties = @{
        image = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${ECR_REPO}:${TAG}"
        vcpus = 72
        memory = 140000
        jobRoleArn = "arn:aws:iam::${ACCOUNT_ID}:role/optimo-batch-role"
        executionRoleArn = "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole"
        environment = @(
            @{name="S3_INPUT_BUCKET"; value="optimo-input-files-v2"}
            @{name="S3_OUTPUT_BUCKET"; value="optimo-output-files"}
            @{name="DYNAMODB_TABLE"; value="optimo-jobs"}
            @{name="AWS_REGION"; value="us-west-2"}
            @{name="AWS_DEFAULT_REGION"; value="us-west-2"}
            @{name="LICENSE_SECRET_NAME"; value="optimo/gurobi-license"}
            @{name="GEMINI_API_KEY"; value="AIzaSyAQC-ytf_lcDK_WZ0ZuOMG8r24QBqvKds0"}
            @{name="JOB_COMPLETION_HANDLER"; value="optimo-job-completion-handler"}
        )
        logConfiguration = @{
            logDriver = "awslogs"
            options = @{
                "awslogs-group" = "/aws/batch/job"
                "awslogs-region" = $REGION
                "awslogs-stream-prefix" = "optimo-job-def-v10"
            }
        }
    }
}

$jobDefJson = $jobDef | ConvertTo-Json -Depth 10
$jobDefJson | Out-File -FilePath "job-def-v10.json" -Encoding UTF8

aws batch register-job-definition --cli-input-json file://job-def-v10.json --region $REGION

# Update Lambda to use v10
Write-Host "`nUpdating Lambda to use job-def-v10..." -ForegroundColor Yellow
aws lambda update-function-configuration `
    --function-name optimo-unified-handler `
    --environment 'Variables={S3_INPUT_BUCKET=optimo-input-files-v2,S3_OUTPUT_BUCKET=optimo-output-files,DYNAMODB_TABLE=optimo-jobs,JOB_QUEUE=optimo-job-queue,JOB_DEFINITION=optimo-job-def-v10}' `
    --region $REGION

Remove-Item job-def-v10.json

Write-Host "`n✅ Container v9 built and pushed successfully!" -ForegroundColor Green
Write-Host "✅ Job definition v10 created using container v9" -ForegroundColor Green
Write-Host "✅ Lambda updated to use job-def-v10" -ForegroundColor Green
Write-Host "`nThe fix:" -ForegroundColor Cyan
Write-Host "- run_batch_job.py now reads file paths from environment variables" -ForegroundColor Cyan
Write-Host "- Files are downloaded from their actual S3 locations (uploads/...)" -ForegroundColor Cyan
Write-Host "- No more 'No files found' errors!" -ForegroundColor Cyan