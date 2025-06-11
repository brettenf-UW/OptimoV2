# PowerShell script to build and push container v8
Write-Host "=== Building OptimoV2 Container v8 (PowerShell) ===" -ForegroundColor Blue

$REGION = "us-west-2"
$ACCOUNT_ID = "529088253685"
$ECR_REPO = "optimo-batch"
$TAG = "v8"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build the container
Write-Host "Building Docker image..." -ForegroundColor Yellow
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

Write-Host "`n✅ Container v8 built and pushed successfully!" -ForegroundColor Green
Write-Host "✅ Lambda is already configured to use optimo-job-def-v8" -ForegroundColor Green
Write-Host "`nThe container now includes the region fix for boto3." -ForegroundColor Cyan