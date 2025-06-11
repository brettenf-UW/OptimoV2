# Simple Lambda deployment script

Write-Host "Deploying Lambda with presigned URL fix..." -ForegroundColor Green

# Copy updated handler
Copy-Item unified_handler.py -Destination package\ -Force

# Change to package directory
Set-Location package

# Create deployment package
Write-Host "Creating deployment package..."
if (Test-Path ..\lambda_deployment.zip) {
    Remove-Item ..\lambda_deployment.zip -Force
}

# Create zip with all dependencies
Compress-Archive -Path * -DestinationPath ..\lambda_deployment.zip -Force

# Go back
Set-Location ..

# Update Lambda
Write-Host "Updating Lambda function..."
aws lambda update-function-code `
    --function-name optimo-unified-handler `
    --zip-file fileb://lambda_deployment.zip `
    --region us-west-2

# Clean up
Remove-Item lambda_deployment.zip -Force

Write-Host "Lambda deployment complete!" -ForegroundColor Green