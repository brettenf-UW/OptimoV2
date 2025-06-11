# Full deployment script for unified Lambda handler

Write-Host "Full deployment of unified Lambda handler..." -ForegroundColor Green

# Copy updated handler
Write-Host "Copying unified handler to package directory..."
Copy-Item unified_handler.py -Destination package\ -Force

# Change to package directory
Set-Location package

# Create full deployment package
Write-Host "Creating deployment package..."
if (Test-Path ..\unified_handler_full.zip) {
    Remove-Item ..\unified_handler_full.zip -Force
}

# Create zip with all dependencies
Compress-Archive -Path * -DestinationPath ..\unified_handler_full.zip -Force

# Go back
Set-Location ..

# Check zip size
$zipSize = (Get-Item unified_handler_full.zip).Length / 1MB
Write-Host "Deployment package size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Yellow

# Update Lambda
Write-Host "Updating Lambda function..."
aws lambda update-function-code `
    --function-name optimo-unified-handler `
    --zip-file fileb://unified_handler_full.zip `
    --region us-west-2

# Wait for update
Write-Host "Waiting for Lambda to update..."
Start-Sleep -Seconds 5

# Get last modified time
$lastModified = aws lambda get-function --function-name optimo-unified-handler --region us-west-2 --query 'Configuration.LastModified' --output text
Write-Host "Lambda last modified: $lastModified" -ForegroundColor Green

# Clean up
Remove-Item unified_handler_full.zip -Force

Write-Host "Deployment complete!" -ForegroundColor Green