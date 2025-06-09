# Create a properly encoded .env file
$envContent = @"
# API Keys
GEMINI_API_KEY=your-gemini-api-key-here

# Gurobi License Path
GRB_LICENSE_FILE=C:\dev\gurobi.lic
"@

# Save with UTF-8 encoding without BOM
[System.IO.File]::WriteAllText("$PWD\.env", $envContent, [System.Text.UTF8Encoding]::new($false))

Write-Host ".env file created successfully!" -ForegroundColor Green
Write-Host "Please edit the file and replace 'your-gemini-api-key-here' with your actual API key" -ForegroundColor Yellow

# Open in notepad
notepad .env