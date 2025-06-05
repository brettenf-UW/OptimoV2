# OptimoV2 Quick Start Guide

## 1. Generate Test Data and Run Pipeline

The easiest way to test OptimoV2:

```bash
# Generate small test data (100 students) and run pipeline
python scripts/run_pipeline.py --generate-test-data small

# Generate medium test data (500 students) and run pipeline  
python scripts/run_pipeline.py --generate-test-data medium

# Generate large test data (2000 students) and run pipeline
python scripts/run_pipeline.py --generate-test-data large
```

## 2. Use Your Own Data

```bash
# Copy your data and run
python scripts/run_pipeline.py --input-dir /path/to/your/csv/files
```

## 3. Just Generate Test Data

```bash
# Generate test data without running pipeline
python scripts/generate_synthetic_data.py --size medium

# Generate with specific student count per grade
python scripts/generate_synthetic_data.py --students-per-grade 150

# Generate with seed for reproducibility
python scripts/generate_synthetic_data.py --size small --seed 42
```

## 4. View Results

After running, check:
- `data/runs/run_[timestamp]/final/` - Final optimized schedules
- `data/runs/run_[timestamp]/iterations/` - Each iteration's details
- `data/runs/run_[timestamp]/logs/` - Execution logs

## Required Files

Your input directory must contain:
- `Student_Info.csv`
- `Student_Preference_Info.csv`
- `Teacher_Info.csv`
- `Teacher_unavailability.csv`
- `Sections_Information.csv`
- `Period.csv` (optional - will use default 8 periods)

## Environment Setup

```bash
# Set API key (required)
export ANTHROPIC_API_KEY="your-api-key-here"

# Install dependencies
pip install -r requirements.txt
```

## Example Output

```
Generating medium test data (125 students per grade)...
============================================================

Generated synthetic data:
  Students: 500 (125 per grade)
  Teachers: 25
  Sections: 89
  Courses: 24
  SPED Students: 75
  Special Course Students: ~150

Files saved to: OptimoV2/data/base

Test data generated successfully!
============================================================

Starting OptimoV2 Pipeline...
============================================================
Started new run: run_20240305_143022

============================================================
ITERATION 0
============================================================
Running MILP optimization...
Analyzing utilization...
Sections needing action: 23/89
Running registrar optimization...
Applying 8 actions...

============================================================
ITERATION 1
============================================================
Running MILP optimization...
Analyzing utilization...
✓ Schedule is optimized! All sections within target range.

============================================================
Pipeline completed successfully!
Best iteration: 1
Final score: -42.50
Output saved to: OptimoV2/data/runs/run_20240305_143022/final
```