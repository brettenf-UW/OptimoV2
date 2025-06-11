# OptimoV2 Optimization Failure Troubleshooting Guide

## Problem Statement
Every optimization job submission is failing with "Essential container in task exited" error. Jobs run for approximately 3 minutes before failing.

**Example Failed Job:**
- Job ID: `optimo-job-71e33b45-8b4a-4897-a2c8-728a9299a1b4`
- Task ARN: `1dbcbd02-ed4e-467e-819e-dba96758b3d8`
- Duration: ~3 minutes before failure
- Error: "Essential container in task exited"

## Comprehensive Testing Strategy

### Phase 1: Container Environment Verification

#### 1.1 Container Build and Local Testing
```bash
# Test 1: Verify Docker image builds successfully
docker build -t optimo-test .
docker images | grep optimo-test

# Test 2: Run container locally with minimal test
docker run --rm optimo-test python -c "print('Container starts successfully')"

# Test 3: Check all required dependencies
docker run --rm optimo-test python -c "
import gurobipy
import google.generativeai
import pandas as pd
import numpy as np
print('All core dependencies loaded')
"

# Test 4: Verify Gurobi license
docker run --rm -e GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic optimo-test python -c "
from gurobipy import *
m = Model('test')
print('Gurobi initialized successfully')
"
```

#### 1.2 Environment Variables Check
```bash
# Test 5: List all required environment variables
docker run --rm optimo-test env | grep -E "(GEMINI|GRB|AWS|PYTHONPATH)"

# Test 6: Verify environment variables are passed correctly
docker run --rm \
  -e GEMINI_API_KEY="test-key" \
  -e GRB_LICENSE_FILE="/opt/gurobi/gurobi.lic" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  optimo-test python -c "
import os
print(f'GEMINI_API_KEY: {os.getenv(\"GEMINI_API_KEY\", \"NOT SET\")}')
print(f'GRB_LICENSE_FILE: {os.getenv(\"GRB_LICENSE_FILE\", \"NOT SET\")}')
print(f'AWS_DEFAULT_REGION: {os.getenv(\"AWS_DEFAULT_REGION\", \"NOT SET\")}')
"
```

### Phase 2: AWS Batch Configuration Verification

#### 2.1 Job Definition Inspection
```bash
# Test 7: Check current job definition
aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE

# Test 8: Verify environment variables in job definition
aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE \
  --query 'jobDefinitions[0].containerProperties.environment'

# Test 9: Check resource allocations
aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE \
  --query 'jobDefinitions[0].containerProperties.{memory:memory,vcpus:vcpus}'
```

#### 2.2 Compute Environment and Job Queue
```bash
# Test 10: Verify compute environment status
aws batch describe-compute-environments --compute-environments optimo-compute-env

# Test 11: Check job queue status
aws batch describe-job-queues --job-queues optimo-job-queue

# Test 12: Verify ECS cluster has running instances
aws ecs describe-clusters --clusters $(aws batch describe-compute-environments \
  --compute-environments optimo-compute-env \
  --query 'computeEnvironments[0].ecsClusterArn' --output text)
```

### Phase 3: File Upload and S3 Access

#### 3.1 S3 Bucket Verification
```bash
# Test 13: Check S3 bucket exists and is accessible
aws s3 ls s3://optimo-input-files-v2/

# Test 14: Verify uploaded files
JOB_ID="71e33b45-8b4a-4897-a2c8-728a9299a1b4"
aws s3 ls s3://optimo-input-files-v2/71e33b45-8b4a-4897-a2c8-728a9299a1b4/

# Test 15: Download and validate file format
aws s3 cp s3://optimo-input-files-v2/$JOB_ID/Period.csv /tmp/
head -5 /tmp/Period.csv
```

#### 3.2 IAM Permissions
```bash
# Test 16: Verify task execution role has S3 access
TASK_ROLE=$(aws batch describe-job-definitions --job-definition-name optimo-job-def \
  --status ACTIVE --query 'jobDefinitions[0].containerProperties.taskRoleArn' --output text)
aws iam get-role-policy --role-name $(basename $TASK_ROLE) --policy-name S3Access

# Test 17: Check execution role permissions
EXEC_ROLE=$(aws batch describe-job-definitions --job-definition-name optimo-job-def \
  --status ACTIVE --query 'jobDefinitions[0].containerProperties.executionRoleArn' --output text)
aws iam list-attached-role-policies --role-name $(basename $EXEC_ROLE)
```

### Phase 4: Script Execution Testing

#### 4.1 Entry Point Verification
```bash
# Test 18: Check if batch_wrapper.py exists in container
docker run --rm optimo-test ls -la /app/scripts/batch_wrapper.py

# Test 19: Test batch_wrapper.py imports
docker run --rm optimo-test python -c "
import sys
sys.path.append('/app')
from scripts.batch_wrapper import main
print('batch_wrapper imports successfully')
"

# Test 20: Check run_batch_job_updated.py
docker run --rm optimo-test ls -la /app/scripts/run_batch_job_updated.py
docker run --rm optimo-test python /app/scripts/run_batch_job_updated.py --help
```

#### 4.2 Pipeline Component Testing
```bash
# Test 21: Test pipeline imports
docker run --rm optimo-test python -c "
import sys
sys.path.append('/app')
from src.pipeline.runner import PipelineRunner
from src.core.load import DataLoader
from src.optimization.utilization_analyzer import UtilizationAnalyzer
print('All pipeline components import successfully')
"

# Test 22: Test with minimal data
docker run --rm -v $(pwd)/data/base:/data optimo-test python -c "
import sys
sys.path.append('/app')
from src.core.load import DataLoader
loader = DataLoader()
data = loader.load_all('/data')
print(f'Loaded {len(data)} data files')
"
```

### Phase 5: CloudWatch Logs Analysis

#### 5.1 Log Retrieval
```bash
# Test 23: Get failed task logs
TASK_ARN="1dbcbd02-ed4e-467e-819e-dba96758b3d8"
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/batch/job \
  --log-stream-name-prefix "optimo-job-def/default/$TASK_ARN" \
  --query 'logStreams[0].logStreamName' --output text)

# Test 24: Retrieve actual error messages
aws logs get-log-events \
  --log-group-name /aws/batch/job \
  --log-stream-name $LOG_STREAM \
  --start-from-head \
  --output text
```

### Phase 6: Common Failure Points

#### 6.1 Memory Issues
```bash
# Test 25: Monitor memory usage during local run
docker stats --no-stream optimo-test

# Test 26: Check if OOM killer was triggered
dmesg | grep -i "killed process"
```

#### 6.2 Timeout Issues
```bash
# Test 27: Check job timeout settings
aws batch describe-job-definitions --job-definition-name optimo-job-def \
  --query 'jobDefinitions[0].timeout'
```

#### 6.3 Network Connectivity
```bash
# Test 28: Test network access from container
docker run --rm optimo-test python -c "
import urllib.request
try:
    urllib.request.urlopen('https://s3.amazonaws.com')
    print('S3 connectivity: OK')
except Exception as e:
    print(f'S3 connectivity: FAILED - {e}')

try:
    urllib.request.urlopen('https://generativelanguage.googleapis.com')
    print('Gemini API connectivity: OK')
except Exception as e:
    print(f'Gemini API connectivity: FAILED - {e}')
"
```

### Phase 7: Specific Error Scenarios

#### 7.1 Missing Files
```python
# Test 29: Create test script to verify all required files
cat > test_file_structure.py << 'EOF'
import os
import sys

required_files = [
    '/app/scripts/batch_wrapper.py',
    '/app/scripts/run_batch_job_updated.py',
    '/app/src/pipeline/runner.py',
    '/app/src/core/load.py',
    '/app/src/core/milp_wrapper.py',
    '/app/src/optimization/utilization_analyzer.py',
    '/app/src/optimization/registrar_agent_gemini.py',
    '/app/config/settings.yaml',
    '/app/config/prompts/registrar_simple.txt'
]

missing_files = []
for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)

if missing_files:
    print("MISSING FILES:")
    for f in missing_files:
        print(f"  - {f}")
else:
    print("All required files present")
EOF

docker run --rm -v $(pwd)/test_file_structure.py:/test_file_structure.py \
  optimo-test python /test_file_structure.py
```

#### 7.2 Permission Issues
```bash
# Test 30: Check file permissions
docker run --rm optimo-test find /app -type f -name "*.py" ! -perm -644 -ls
```

### Phase 8: Integration Testing

#### 8.1 End-to-End Test with Mock Data
```bash
# Test 31: Run complete pipeline with test data
docker run --rm \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  -e GRB_LICENSE_FILE="/opt/gurobi/gurobi.lic" \
  -e JOB_ID="test-job-123" \
  -e S3_BUCKET="optimo-input-files-v2" \
  -v $(pwd)/data/base:/data \
  -v $(pwd)/gurobi.lic:/opt/gurobi/gurobi.lic:ro \
  optimo-test python /app/scripts/run_batch_job_updated.py \
    --job-id test-job-123 \
    --s3-bucket optimo-input-files-v2 \
    --local-test /data
```

### Phase 9: Debugging Checklist

Before testing via frontend, verify:

- [ ] Docker image builds without errors
- [ ] All Python dependencies import successfully
- [ ] Gurobi license file is present and valid
- [ ] Environment variables are set correctly
- [ ] AWS credentials are configured
- [ ] S3 bucket is accessible
- [ ] IAM roles have necessary permissions
- [ ] Container has sufficient memory (at least 8GB)
- [ ] Network connectivity to S3 and Gemini API
- [ ] All required Python scripts exist in container
- [ ] File permissions are correct
- [ ] CloudWatch logs are being created
- [ ] No syntax errors in Python scripts
- [ ] Data files are in correct format

### Phase 10: Quick Diagnostic Script

Create this script to run all basic checks:

```bash
#!/bin/bash
# save as diagnose_optimo.sh

echo "=== OptimoV2 Diagnostic Tool ==="
echo

# Check Docker
echo "1. Checking Docker image..."
if docker images | grep -q "optimo"; then
    echo "✓ Docker image found"
else
    echo "✗ Docker image not found"
fi

# Check AWS CLI
echo "2. Checking AWS configuration..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✓ AWS credentials configured"
else
    echo "✗ AWS credentials not configured"
fi

# Check S3 bucket
echo "3. Checking S3 bucket..."
if aws s3 ls s3://optimo-input-files-v2/ > /dev/null 2>&1; then
    echo "✓ S3 bucket accessible"
else
    echo "✗ S3 bucket not accessible"
fi

# Check Batch job definition
echo "4. Checking Batch job definition..."
if aws batch describe-job-definitions --job-definition-name optimo-job-def --status ACTIVE > /dev/null 2>&1; then
    echo "✓ Job definition exists"
else
    echo "✗ Job definition not found"
fi

# Check compute environment
echo "5. Checking compute environment..."
STATUS=$(aws batch describe-compute-environments --compute-environments optimo-compute-env --query 'computeEnvironments[0].state' --output text 2>/dev/null)
if [ "$STATUS" = "ENABLED" ]; then
    echo "✓ Compute environment enabled"
else
    echo "✗ Compute environment not enabled (Status: $STATUS)"
fi

echo
echo "=== Diagnostic complete ==="
```

## Next Steps

1. Run through each test phase systematically
2. Document any failures with exact error messages
3. Check CloudWatch logs for the specific failed job
4. Compare working local execution vs. Batch execution
5. Focus on the first error that appears in the logs

## Most Common Causes

Based on the 3-minute runtime before failure:

1. **Missing Environment Variables** - Gemini API key or Gurobi license
2. **File Access Issues** - Can't read from S3 or write results
3. **Memory Exhaustion** - Container runs out of memory during optimization
4. **Script Errors** - Python script crashes due to missing imports or syntax errors
5. **Network Timeouts** - Can't connect to Gemini API or S3

Start with Phase 1 and work through systematically until you find the root cause.