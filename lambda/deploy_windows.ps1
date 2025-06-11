# PowerShell script to deploy unified Lambda handler

Write-Host "Deploying unified Lambda handler on Windows..." -ForegroundColor Green

# Copy unified handler to package directory
Write-Host "Copying unified handler to package directory..."
Copy-Item -Path "unified_handler.py" -Destination "package\" -Force

# Change to package directory
Set-Location -Path "package"

# Create deployment package
Write-Host "Creating deployment package..."
# Remove old zip if exists
if (Test-Path ..\unified_handler.zip) {
    Remove-Item ..\unified_handler.zip
}

# Create new zip (using .NET compression)
Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($PWD, "..\unified_handler.zip")

# Go back to lambda directory
Set-Location -Path ".."

# Update Lambda function
Write-Host "Updating Lambda function code..."
aws lambda update-function-code `
    --function-name optimo-unified-handler `
    --zip-file fileb://unified_handler.zip `
    --region us-west-2

# Clean up
Write-Host "Cleaning up..."
Remove-Item unified_handler.zip

Write-Host "Deployment complete!" -ForegroundColor Green