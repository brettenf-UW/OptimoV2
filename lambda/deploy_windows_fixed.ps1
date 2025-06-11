# PowerShell script to deploy unified Lambda handler

Write-Host "Deploying unified Lambda handler on Windows..." -ForegroundColor Green

# Copy unified handler to package directory
Write-Host "Copying unified handler to package directory..."
Copy-Item -Path "unified_handler.py" -Destination "package\" -Force

# Create deployment package
Write-Host "Creating deployment package..."
# Remove old zip if exists
if (Test-Path unified_handler.zip) {
    Remove-Item unified_handler.zip -Force
}

# Create new zip using Compress-Archive
Compress-Archive -Path "package\*" -DestinationPath "unified_handler.zip" -Force

# Verify zip was created
if (Test-Path unified_handler.zip) {
    Write-Host "Zip file created successfully" -ForegroundColor Green
    
    # Update Lambda function
    Write-Host "Updating Lambda function code..."
    aws lambda update-function-code `
        --function-name optimo-unified-handler `
        --zip-file fileb://unified_handler.zip `
        --region us-west-2
    
    # Clean up
    Write-Host "Cleaning up..."
    Remove-Item unified_handler.zip -Force
    
    Write-Host "Deployment complete!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create zip file" -ForegroundColor Red
}