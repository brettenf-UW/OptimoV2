# PowerShell script to build and push container v13 with argument fix
Write-Host "=== Building OptimoV2 Container v13 with Pipeline Argument Fix ===" -ForegroundColor Blue

$REGION = "us-west-2"
$ACCOUNT_ID = "529088253685"
$ECR_REPO = "optimo-batch"
$TAG = "v13"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build the container
Write-Host "Building Docker image with fixed pipeline arguments..." -ForegroundColor Yellow
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

Write-Host "`n✅ Container v13 built and pushed successfully!" -ForegroundColor Green
Write-Host "✅ This container includes:" -ForegroundColor Green
Write-Host "   - Fixed file download from environment variables" -ForegroundColor Green
Write-Host "   - python-dotenv dependency" -ForegroundColor Green
Write-Host "   - Correct pipeline arguments (--input-dir instead of --data-dir)" -ForegroundColor Green
Write-Host "`nNow run this to create job definition v13:" -ForegroundColor Cyan
Write-Host "./create_job_def_v13.sh" -ForegroundColor Cyan