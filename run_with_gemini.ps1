# PowerShell script to run with Gemini
param(
    [string]$size = "small"
)

Write-Host "Running OptimoV2 with Gemini 2.0 Flash..." -ForegroundColor Green
python scripts/run_pipeline.py --ai-provider gemini --generate-test-data $size