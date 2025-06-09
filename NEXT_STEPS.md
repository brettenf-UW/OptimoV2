# OptimoV2 - Next Steps After Moving Project

## 1. Move and Clean Project Path

### Step 1.1: Move the Project
```powershell
# Create new directory
New-Item -ItemType Directory -Path "C:\OptimoV2" -Force

# Copy the entire project (this preserves the structure)
robocopy "C:\Users\brett\OneDrive - UW\Desktop\UW\Jobs 🧑‍💼\Interworks\Analystics Consultant\Final Presentation\Demo-3\OptimoV2" "C:\OptimoV2" /E /COPYALL

# Navigate to new location
cd C:\OptimoV2
```

### Step 1.2: Clean Up Generated Files
```powershell
# Remove any generated files from failed runs
Remove-Item -Recurse -Force data\runs\* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force debug\* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force src\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force src\*\__pycache__ -ErrorAction SilentlyContinue
```

## 2. Test Core OptimoV2 System

### Step 2.1: Verify Environment Setup
```powershell
# Check Python version (should be 3.8+)
python --version

# Verify .env file exists and has your API key
type .env

# Ensure Gurobi license is accessible
Test-Path "C:\dev\gurobi.lic"
```

### Step 2.2: Run Core System Test
```powershell
# Test with small dataset
python scripts/run_pipeline.py --generate-test-data small

# Expected output:
# - Generates test data in data/base/
# - Runs MILP optimization
# - Shows utilization analysis
# - Runs Gemini AI for optimization suggestions
# - Creates output in data/runs/run_[timestamp]/
```

### Step 2.3: Verify Results
```powershell
# Check the latest run directory
$latestRun = Get-ChildItem data\runs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Latest run: $($latestRun.Name)"

# View final results
Get-ChildItem "data\runs\$($latestRun.Name)\final"

# Should see:
# - Master_Schedule.csv
# - Student_Assignments.csv  
# - Teacher_Schedule.csv
# - Constraint_Violations.csv
```

## 3. Test Frontend Application

### Step 3.1: Install Frontend Dependencies
```powershell
cd optimo-frontend
npm install

# Install mock server dependencies
npm install express multer cors uuid concurrently --save-dev
```

### Step 3.2: Run Frontend with Mock Backend
```powershell
# This runs both mock API (port 5000) and React app (port 3000)
npm run dev

# Or run them separately:
# Terminal 1:
node mock-server.js

# Terminal 2:
npm start
```

### Step 3.3: Test Frontend Features
1. Open http://localhost:3000 in your browser
2. Test file upload:
   - Drag and drop CSV files from `C:\OptimoV2\data\base\`
   - Or use the file picker
3. Submit a job and watch progress
4. Download results when complete

## 4. Validate Full Integration

### Step 4.1: Test Different Scenarios
```powershell
# Test with medium dataset
python scripts/run_pipeline.py --generate-test-data medium

# Test with large dataset
python scripts/run_pipeline.py --generate-test-data large

# Test with your own data
python scripts/run_pipeline.py --input-dir "path\to\your\csv\files"
```

### Step 4.2: Monitor Performance
- Small dataset: Should complete in 1-2 minutes
- Medium dataset: Should complete in 5-10 minutes  
- Large dataset: May take 30+ minutes depending on your system

## 5. Prepare for AWS Deployment

### Step 5.1: Test Docker Build (Optional)
```powershell
# Build Docker image
docker build -t optimo-scheduler .

# Run container locally
docker run --rm `
  -v "${PWD}/data/base:/app/input" `
  -v "${PWD}/output:/app/output" `
  -e GEMINI_API_KEY=$env:GEMINI_API_KEY `
  -e GRB_LICENSE_FILE="/app/gurobi.lic" `
  -v "C:/dev/gurobi.lic:/app/gurobi.lic" `
  optimo-scheduler
```

### Step 5.2: Prepare for GitHub Pages
```powershell
cd optimo-frontend

# Update homepage in package.json with your GitHub username
# Edit: "homepage": "https://YOUR_USERNAME.github.io/OptimoV2"

# Build and test production build
npm run build
npx serve -s build

# Deploy to GitHub Pages
npm run deploy
```

## 6. Common Issues and Solutions

### Issue: Gurobi License Error
```powershell
# Set license path explicitly
$env:GRB_LICENSE_FILE = "C:\dev\gurobi.lic"

# Verify license
python -c "import gurobipy; print('Gurobi OK')"
```

### Issue: MILP Takes Too Long
- Reduce time limit in `config/settings.yaml`:
  ```yaml
  milp:
    time_limit: 300  # 5 minutes for testing
  ```

### Issue: API Key Not Found
```powershell
# Check environment variable
echo $env:GEMINI_API_KEY

# Or add to .env file
echo "GEMINI_API_KEY=your-key-here" > .env
```

## 7. Next Development Steps

### Phase 2: AWS Infrastructure
- [ ] Set up S3 buckets for file storage
- [ ] Create Lambda functions for job handling
- [ ] Configure API Gateway
- [ ] Set up AWS Batch for MILP processing

### Phase 3: Production Features
- [ ] Add user authentication
- [ ] Implement job queue management
- [ ] Add email notifications
- [ ] Create admin dashboard

### Phase 4: Optimization
- [ ] Fine-tune Gemini prompts for better suggestions
- [ ] Add more sophisticated scheduling constraints
- [ ] Implement multi-school support
- [ ] Add scheduling conflict resolution

## 8. Success Criteria

✅ **Core System Working** when:
- Test data generates without errors
- MILP optimization completes successfully
- Gemini AI provides optimization suggestions
- Output files are created in correct format

✅ **Frontend Working** when:
- File upload accepts all CSV types
- Job submission returns job ID
- Progress updates in real-time
- Results can be downloaded

✅ **Ready for Production** when:
- All tests pass with different data sizes
- System handles errors gracefully
- Documentation is complete
- AWS deployment plan is tested

---

## Quick Test Commands

```powershell
# Full test in new location
cd C:\OptimoV2
python scripts/run_pipeline.py --generate-test-data small

# Frontend test
cd optimo-frontend
npm run dev

# Open browser to http://localhost:3000
```

Remember: The move to `C:\OptimoV2` will eliminate all Unicode/emoji issues!