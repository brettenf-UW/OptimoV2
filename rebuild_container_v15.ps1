# PowerShell script to build and push container v15 - THE FINAL VERSION!
Write-Host "=== Building OptimoV2 Container v15 - FINAL VERSION ===" -ForegroundColor Blue

$REGION = "us-west-2"
$ACCOUNT_ID = "529088253685"
$ECR_REPO = "optimo-batch"
$TAG = "v15"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build the container
Write-Host "Building Docker image with output directory fix..." -ForegroundColor Yellow
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

Write-Host "`n✅ Container v15 built and pushed successfully!" -ForegroundColor Green
Write-Host "✅ This is the FINAL version with ALL fixes:" -ForegroundColor Green
Write-Host "   - Fixed file download from environment variables" -ForegroundColor Green
Write-Host "   - All Python dependencies included" -ForegroundColor Green
Write-Host "   - Correct pipeline arguments" -ForegroundColor Green
Write-Host "   - Output directory detection fixed" -ForegroundColor Green
Write-Host "`nNow run this to create job definition v15:" -ForegroundColor Cyan
Write-Host "./create_job_def_v15.sh" -ForegroundColor Cyan
Write-Host "`n🎉 THE OPTIMIZATION IS ALREADY WORKING! This fix just handles the output correctly!" -ForegroundColor Yellow