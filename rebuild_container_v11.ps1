# PowerShell script to build and push container v11 with the ACTUAL file download fix
Write-Host "=== Building OptimoV2 Container v11 with VERIFIED File Download Fix ===" -ForegroundColor Blue

$REGION = "us-west-2"
$ACCOUNT_ID = "529088253685"
$ECR_REPO = "optimo-batch"
$TAG = "v11"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build the container
Write-Host "Building Docker image with FIXED run_batch_job.py..." -ForegroundColor Yellow
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

Write-Host "`n✅ Container v11 built and pushed successfully!" -ForegroundColor Green
Write-Host "✅ This container has the ACTUAL fix that reads from environment variables" -ForegroundColor Green
Write-Host "`nNow run this to create job definition v11:" -ForegroundColor Cyan
Write-Host "./create_job_def_v11.sh" -ForegroundColor Cyan