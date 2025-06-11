# Quick PowerShell script to deploy Lambda fix

Write-Host "Deploying Lambda fix for DynamoDB Decimal issue..." -ForegroundColor Green

# Copy updated handler
Copy-Item unified_handler.py -Destination package\ -Force

# Create minimal zip (just the handler file)
Set-Location package
if (Test-Path ..\unified_fix.zip) {
    Remove-Item ..\unified_fix.zip -Force
}

# Create zip with just the handler
Compress-Archive -Path unified_handler.py -DestinationPath ..\unified_fix.zip -Force

Set-Location ..

# Update Lambda
aws lambda update-function-code `
    --function-name optimo-unified-handler `
    --zip-file fileb://unified_fix.zip `
    --region us-west-2

# Clean up
Remove-Item unified_fix.zip -Force

Write-Host "Fix deployed!" -ForegroundColor Green