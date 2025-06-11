#!/bin/bash

# OptimoV2 Comprehensive Diagnostic Tool
# This script checks all aspects of the optimization system

echo "=== OptimoV2 Diagnostic Tool ==="
echo "================================"
echo "Date: $(date)"
echo

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Docker Setup"
echo "------------------------"

# Check if Docker is running
if docker info > /dev/null 2>&1; then
    print_result 0 "Docker is running"
else
    print_result 1 "Docker is not running"
    exit 1
fi

# Check for Optimo images
if docker images | grep -q "optimo-batch"; then
    print_result 0 "Optimo Docker image found"
    docker images | grep "optimo-batch" | awk '{print "  - "$1":"$2" (ID: "$3")"}'
else
    print_result 1 "Optimo Docker image not found"
fi

# Check for v6 and v7 images in ECR
echo
echo "2. Checking ECR Images"
echo "----------------------"

for version in v6 v7; do
    if aws ecr describe-images --repository-name optimo-batch --image-ids imageTag=$version --region us-west-2 > /dev/null 2>&1; then
        print_result 0 "ECR image optimo-batch:$version exists"
    else
        print_result 1 "ECR image optimo-batch:$version not found"
    fi
done

echo
echo "3. Checking AWS Configuration"
echo "-----------------------------"

# Check AWS CLI
if aws sts get-caller-identity > /dev/null 2>&1; then
    print_result 0 "AWS credentials configured"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "  - Account ID: $ACCOUNT_ID"
else
    print_result 1 "AWS credentials not configured"
fi

# Check S3 buckets
echo
echo "4. Checking S3 Buckets"
echo "----------------------"

for bucket in optimo-input-files-v2 optimo-output-files optimo-input-files; do
    if aws s3 ls s3://$bucket > /dev/null 2>&1; then
        print_result 0 "S3 bucket $bucket accessible"
    else
        print_result 1 "S3 bucket $bucket not accessible"
    fi
done

# Check for the specific failed job files
JOB_ID="71e33b45-8b4a-4897-a2c8-728a9299a1b4"
echo
echo "5. Checking Failed Job Files (Job ID: $JOB_ID)"
echo "-----------------------------------------------"

if aws s3 ls s3://optimo-input-files-v2/$JOB_ID/ > /dev/null 2>&1; then
    print_result 0 "Input files found for job $JOB_ID"
    echo "  Files:"
    aws s3 ls s3://optimo-input-files-v2/$JOB_ID/ | awk '{print "  - "$4}'
else
    print_result 1 "Input files not found for job $JOB_ID"
fi

echo
echo "6. Checking AWS Batch Configuration"
echo "-----------------------------------"

# Check job definition
if aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE --region us-west-2 > /dev/null 2>&1; then
    print_result 0 "Job definition 'optimo-job-def' exists"
    IMAGE=$(aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE --region us-west-2 --query 'jobDefinitions[0].containerProperties.image' --output text)
    echo "  - Image: $IMAGE"
    MEMORY=$(aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE --region us-west-2 --query 'jobDefinitions[0].containerProperties.memory' --output text)
    VCPUS=$(aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE --region us-west-2 --query 'jobDefinitions[0].containerProperties.vcpus' --output text)
    echo "  - Memory: $MEMORY MB"
    echo "  - vCPUs: $VCPUS"
else
    print_result 1 "Job definition 'optimo-job-def' not found"
fi

# Check compute environment
echo
echo "7. Checking Compute Environment"
echo "-------------------------------"

CE_STATUS=$(aws batch describe-compute-environments --compute-environments optimo-compute-env --region us-west-2 --query 'computeEnvironments[0].state' --output text 2>/dev/null)
if [ "$CE_STATUS" = "ENABLED" ]; then
    print_result 0 "Compute environment is ENABLED"
else
    print_result 1 "Compute environment status: $CE_STATUS"
fi

# Check job queue
JQ_STATUS=$(aws batch describe-job-queues --job-queues optimo-job-queue --region us-west-2 --query 'jobQueues[0].state' --output text 2>/dev/null)
if [ "$JQ_STATUS" = "ENABLED" ]; then
    print_result 0 "Job queue is ENABLED"
else
    print_result 1 "Job queue status: $JQ_STATUS"
fi

echo
echo "8. Checking Local Files"
echo "-----------------------"

# Check critical Python files
FILES_TO_CHECK=(
    "scripts/run_batch_job.py"
    "scripts/run_batch_job_updated.py"
    "scripts/run_pipeline.py"
    "src/pipeline/runner.py"
    "src/core/milp_wrapper.py"
    "config/settings.yaml"
    "requirements.txt"
    "Dockerfile"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        print_result 0 "File exists: $file"
    else
        print_result 1 "File missing: $file"
    fi
done

echo
echo "9. Checking Python Dependencies"
echo "-------------------------------"

# Test Python imports in Docker container
echo "Testing Python imports in container..."

cat > /tmp/test_imports.py << 'EOF'
import sys
sys.path.append('/app')

try:
    import gurobipy
    print("✓ gurobipy")
except Exception as e:
    print(f"✗ gurobipy: {e}")

try:
    import google.generativeai
    print("✓ google.generativeai")
except Exception as e:
    print(f"✗ google.generativeai: {e}")

try:
    from src.pipeline.runner import PipelineRunner
    print("✓ PipelineRunner")
except Exception as e:
    print(f"✗ PipelineRunner: {e}")

try:
    from src.core.milp_wrapper import MILPModel
    print("✓ MILPModel")
except Exception as e:
    print(f"✗ MILPModel: {e}")
EOF

if docker images | grep -q "optimo-batch"; then
    docker run --rm -v /tmp/test_imports.py:/test_imports.py optimo-batch:latest python /test_imports.py 2>/dev/null || print_warning "Failed to test imports in container"
fi

echo
echo "10. Checking Container Entry Point"
echo "----------------------------------"

# Check what the container actually runs
if docker images | grep -q "optimo-batch"; then
    ENTRYPOINT=$(docker inspect optimo-batch:latest --format='{{.Config.Entrypoint}}' 2>/dev/null)
    CMD=$(docker inspect optimo-batch:latest --format='{{.Config.Cmd}}' 2>/dev/null)
    echo "Container configuration:"
    echo "  - Entrypoint: $ENTRYPOINT"
    echo "  - Cmd: $CMD"
fi

echo
echo "11. Known Issues"
echo "----------------"

# Check for the specific bug we found
if grep -q "OptimizationPipeline" scripts/run_batch_job_updated.py 2>/dev/null; then
    print_warning "run_batch_job_updated.py imports non-existent OptimizationPipeline class"
    echo "  Should import PipelineRunner instead"
fi

# Check if run_batch_job.py has been overwritten
if diff -q scripts/run_batch_job.py scripts/run_batch_job_updated.py > /dev/null 2>&1; then
    print_warning "run_batch_job.py has been overwritten with run_batch_job_updated.py"
fi

echo
echo "12. CloudWatch Logs"
echo "-------------------"

# Get recent failed jobs
echo "Recent failed Batch jobs:"
aws logs filter-log-events \
    --log-group-name /aws/batch/job \
    --filter-pattern '"Pipeline failed"' \
    --start-time $(($(date +%s) - 3600))000 \
    --region us-west-2 \
    --max-items 5 \
    --query 'events[*].[timestamp,message]' \
    --output text 2>/dev/null | head -5 || echo "  No recent failures found"

echo
echo "=== Diagnostic Summary ==="
echo "========================="

# Print key findings
echo
echo "CRITICAL ISSUES FOUND:"
echo "1. The container v6 is failing because it can't find /app/scripts/run_pipeline.py"
echo "2. run_batch_job_updated.py has a bug - imports non-existent OptimizationPipeline class"
echo "3. The rebuild script overwrites run_batch_job.py with the buggy version"
echo
echo "RECOMMENDED FIXES:"
echo "1. Fix run_batch_job_updated.py to use subprocess instead of importing OptimizationPipeline"
echo "2. OR: Fix the import to use PipelineRunner instead"
echo "3. Rebuild container with correct scripts"
echo "4. Update job definition to use the new container"
echo
echo "To fix immediately, run:"
echo "  1. cp scripts/run_batch_job.py scripts/run_batch_job.backup.py"
echo "  2. Fix the import issue in run_batch_job_updated.py"
echo "  3. ./rebuild_container.sh"
echo "  4. Update Lambda to use 'optimo-job-updated' job definition"

# Clean up
rm -f /tmp/test_imports.py