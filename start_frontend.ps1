# Simple Frontend Starter - ONE COMMAND DOES EVERYTHING

Write-Host "Starting OptimoV2 Frontend..." -ForegroundColor Green

# Go to frontend directory
cd optimo-frontend

# Run the dev command (both servers in one terminal)
Write-Host "Starting app on http://localhost:3000" -ForegroundColor Cyan
npm run dev

# When user stops with Ctrl+C, go back
cd ..