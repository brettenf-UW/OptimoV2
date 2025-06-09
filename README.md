# OptimoV2 - School Schedule Optimizer

A next-generation school scheduling system that uses MILP optimization and AI-powered refinement to create optimal class schedules with 75%-115% section utilization.

## Key Features

- **Preserved Core**: Uses your existing Gurobi MILP engine unchanged
- **Clean Iterations**: No file conflicts or data corruption
- **AI Registrar**: Gemini-powered optimization with clear, action-based decisions
- **Privacy-First**: AI only sees utilization statistics, no personal data
- **Full Audit Trail**: Every change tracked and reversible

## Architecture Overview

```
OptimoV2/
├── src/
│   ├── core/           # Your existing MILP & greedy algorithms
│   ├── pipeline/       # Clean iteration management
│   ├── optimization/   # AI registrar & action processing
│   └── utils/          # Logging and helpers
├── data/
│   ├── base/          # Original input files (never modified)
│   └── runs/          # Timestamped execution runs
└── config/            # Settings and prompts
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Configuration

1. Copy your Gurobi license file to the project root
2. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### 3. Prepare Input Data

Place your input CSV files in a directory:
- `Student_Info.csv`
- `Student_Preference_Info.csv`
- `Teacher_Info.csv`
- `Teacher_unavailability.csv`
- `Sections_Information.csv`
- `Period.csv` (optional)

### 4. Run the Pipeline

```bash
python scripts/run_pipeline.py --input-dir /path/to/your/input/files
```

## How It Works

1. **MILP Optimization**: Runs your existing Gurobi engine to create initial schedule
2. **Utilization Analysis**: Calculates section utilization percentages
3. **AI Registrar**: Decides on actions (SPLIT/MERGE/ADD/REMOVE) based on utilization
4. **Action Processing**: Applies changes to section data
5. **Iteration**: Repeats until 95% of sections are within 75%-115% utilization

## Key Improvements Over V1

### Clean Iteration Management
- Each iteration gets its own workspace
- No file overwrites between iterations
- Full snapshots for debugging
- Easy rollback if needed

### Clear AI Decisions
- Only 4 possible actions
- Percentage-based logic (no hard limits)
- Simple prompts that work
- Fallback heuristics if AI fails

### Privacy Protection
- AI never sees student/teacher names
- Only aggregate statistics provided
- Compliance-friendly design

## Configuration

Edit `config/settings.yaml` to adjust:
- Utilization targets (default: 75%-115%)
- Maximum iterations (default: 3)
- AI model settings
- Resource limits

## Output Structure

Each run creates a timestamped folder:
```
data/runs/run_20240305_143022/
├── iterations/          # Each iteration's data
├── logs/               # Detailed logs
└── final/              # Best results
```

Final output includes:
- `Master_Schedule.csv` - Section to period mapping
- `Student_Assignments.csv` - Student to section mapping
- `Teacher_Schedule.csv` - Teacher assignments
- `Constraint_Violations.csv` - Optimization metrics

## Monitoring Progress

The pipeline provides clear progress updates:
```
ITERATION 0
Running MILP optimization...
Analyzing utilization...
Sections needing action: 45/129
Running registrar optimization...
Applying 8 actions...

ITERATION 1
Running MILP optimization...
Analyzing utilization...
Sections needing action: 12/129
...
```

## Troubleshooting

### MILP Fails
- Check Gurobi license is valid
- Ensure input files are properly formatted
- Check logs in `data/runs/[latest]/logs/`

### AI Registrar Issues
- Verify API key is set correctly
- Check `registrar_actions.json` in iteration folder
- Falls back to heuristic rules automatically

### Poor Utilization
- Adjust targets in `config/settings.yaml`
- Increase max iterations
- Check if sections have reasonable capacities

## Future UI

A Gradio-based web interface is planned for easier use. The architecture is designed to support this with minimal changes.

## Support

For issues or questions, check the logs in your run directory first. Each iteration saves comprehensive debugging information.