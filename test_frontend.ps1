# OptimoV2 Frontend Test Script
# This script makes it easy to test the frontend with mock data

Write-Host "OptimoV2 Frontend Test Helper" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "optimo-frontend")) {
    Write-Host "Error: Please run this script from the OptimoV2 root directory" -ForegroundColor Red
    exit 1
}

# Navigate to frontend directory
Set-Location optimo-frontend

Write-Host "Starting Frontend Test Environment..." -ForegroundColor Green
Write-Host ""
Write-Host "This will open TWO terminal windows:" -ForegroundColor Yellow
Write-Host "1. Mock API Server (port 5000)" -ForegroundColor White
Write-Host "2. React Frontend (port 3000)" -ForegroundColor White
Write-Host ""
Write-Host "Your browser will open automatically to http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Start mock server in new window
Write-Host "Starting Mock Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host 'Mock API Server' -ForegroundColor Green; Write-Host 'Running on http://localhost:5000' -ForegroundColor White; Write-Host ''; npm run mock-server"

# Wait a moment for mock server to start
Start-Sleep -Seconds 2

# Start React app in new window
Write-Host "Starting React Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host 'React Frontend' -ForegroundColor Green; Write-Host 'Starting on http://localhost:3000' -ForegroundColor White; Write-Host ''; npm start"

Write-Host ""
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "TEST INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Wait for browser to open (may take 30-60 seconds)" -ForegroundColor White
Write-Host "2. Upload CSV files from: C:\dev\OptimoV2\data\base\" -ForegroundColor White
Write-Host "3. Click 'Submit Job' to start optimization" -ForegroundColor White
Write-Host "4. Watch the progress bar update" -ForegroundColor White
Write-Host "5. Download results when complete" -ForegroundColor White
Write-Host ""
Write-Host "To stop: Close both PowerShell windows" -ForegroundColor Yellow
Write-Host ""

# Return to root directory
Set-Location ..