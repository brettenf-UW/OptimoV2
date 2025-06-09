# PowerShell script to run with Claude Sonnet
param(
    [string]$size = "small"
)

Write-Host "Running OptimoV2 with Claude Sonnet 3.5..." -ForegroundColor Cyan
python scripts/run_pipeline.py --ai-provider claude --generate-test-data $size