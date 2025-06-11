# PowerShell commands to control AWS Batch compute environment

# Function to scale down (save money when not in use)
function Stop-OptimoCompute {
    Write-Host "Scaling down Optimo compute environment to 0 vCPUs..." -ForegroundColor Yellow
    aws batch update-compute-environment `
        --compute-environment optimo-compute-env `
        --state ENABLED `
        --compute-resources minvCpus=0,maxvCpus=256,desiredvCpus=0 `
        --region us-west-2
    Write-Host "Complete! Instances will terminate in ~5 minutes." -ForegroundColor Green
    Write-Host "Cost: $0/hour when no jobs are running" -ForegroundColor Cyan
}

# Function to scale up (prepare for optimization jobs)
function Start-OptimoCompute {
    Write-Host "Scaling up Optimo compute environment to 72 vCPUs..." -ForegroundColor Yellow
    aws batch update-compute-environment `
        --compute-environment optimo-compute-env `
        --state ENABLED `
        --compute-resources minvCpus=32,maxvCpus=256,desiredvCpus=72 `
        --region us-west-2
    Write-Host "Complete! Instances will be ready in ~3-5 minutes." -ForegroundColor Green
    Write-Host "Cost: ~$1.08/hour (2 spot instances)" -ForegroundColor Cyan
}

# Function to check current status
function Get-OptimoComputeStatus {
    Write-Host "Checking Optimo compute environment status..." -ForegroundColor Yellow
    $env = aws batch describe-compute-environments `
        --compute-environments optimo-compute-env `
        --region us-west-2 `
        --output json | ConvertFrom-Json
    
    $compute = $env.computeEnvironments[0].computeResources
    Write-Host ""
    Write-Host "Current Settings:" -ForegroundColor Cyan
    Write-Host "  Min vCPUs: $($compute.minvCpus)"
    Write-Host "  Max vCPUs: $($compute.maxvCpus)"
    Write-Host "  Desired vCPUs: $($compute.desiredvCpus)"
    Write-Host "  Status: $($env.computeEnvironments[0].status)"
    Write-Host ""
    
    if ($compute.desiredvCpus -eq 0) {
        Write-Host "💤 Compute environment is SLEEPING (saving money)" -ForegroundColor Green
    } else {
        Write-Host "🚀 Compute environment is ACTIVE (ready for jobs)" -ForegroundColor Green
        Write-Host "   Estimated cost: ~$$('{0:N2}' -f ($compute.desiredvCpus * 0.015))/hour" -ForegroundColor Yellow
    }
}

# Quick commands
Write-Host "AWS Batch Compute Environment Control" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Available commands:" -ForegroundColor White
Write-Host "  Stop-OptimoCompute     # Scale to 0 (save money)" -ForegroundColor Green
Write-Host "  Start-OptimoCompute    # Scale to 72 vCPUs (2 instances)" -ForegroundColor Green
Write-Host "  Get-OptimoComputeStatus # Check current status" -ForegroundColor Green
Write-Host ""
Write-Host "Quick one-liners:" -ForegroundColor White
Write-Host '  aws batch update-compute-environment --compute-environment optimo-compute-env --compute-resources desiredvCpus=0 --region us-west-2' -ForegroundColor Gray
Write-Host '  aws batch update-compute-environment --compute-environment optimo-compute-env --compute-resources desiredvCpus=72 --region us-west-2' -ForegroundColor Gray