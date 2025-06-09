# OptimoV2 - Revised Architecture (Preserving Gurobi Engine)

## Critical Clarifications

1. **Gurobi MILP Engine (milp_soft.py)**: UNCHANGED - This is the core that works well
2. **Greedy Algorithm**: UNCHANGED - Still provides initial solution to Gurobi
3. **Data Models**: Just Python classes for data validation/passing, NOT optimization models
4. **Registrar AI**: Gemini-based agent that only sees summary statistics, NO student personal data

## What We're Actually Building

We're creating a **wrapper/pipeline** around your existing Gurobi engine that:
- Manages iterations cleanly
- Provides better prompts to the AI registrar
- Focuses on percentage-based utilization
- Prevents file corruption between iterations

## Simplified Architecture

```
OptimoV2/
├── src/
│   ├── core/                      # Your existing algorithms (minimal changes)
│   │   ├── milp_soft.py          # YOUR EXISTING GUROBI ENGINE (preserved)
│   │   ├── greedy.py             # YOUR EXISTING GREEDY ALGORITHM (preserved)
│   │   └── load.py               # YOUR EXISTING DATA LOADER (enhanced)
│   │
│   ├── pipeline/                  # NEW - Clean iteration management
│   │   ├── runner.py             # Orchestrates the pipeline
│   │   ├── iteration_manager.py  # Manages iteration folders
│   │   └── state_tracker.py      # Tracks what changed between iterations
│   │
│   ├── optimization/              # NEW - Improved registrar agent
│   │   ├── registrar_agent_gemini.py # Gemini AI agent for section optimization
│   │   ├── utilization_analyzer.py # Creates summary stats for AI
│   │   └── action_processor.py   # Applies SPLIT/MERGE/ADD/REMOVE actions
│   │
│   ├── utils/                     # Utilities
│   │   ├── file_manager.py      # Safe file operations
│   │   ├── validators.py        # Input validation
│   │   └── logger.py            # Centralized logging
│   │
│   └── interfaces/               # User interfaces
│       ├── cli.py               # Command line interface
│       └── web_app.py           # Gradio interface
│
├── data/                         # Data management
│   ├── base/                    # Original input (never modified)
│   └── runs/                    # Pipeline runs
│       └── run_[timestamp]/
│           ├── iterations/
│           │   ├── iter_0/      # Each iteration isolated
│           │   ├── iter_1/
│           │   └── iter_2/
│           └── logs/
│
├── config/
│   ├── settings.yaml            # Pipeline settings
│   └── prompts/                 # AI prompts
│       └── registrar_simple.txt # Clear, action-focused prompt
│
└── scripts/
    ├── run_pipeline.py          # Main entry point
    └── migrate_data.py          # Import from old system
```

## How It ACTUALLY Works

### 1. Pipeline Flow (What's New)

```
1. Copy input files to iteration folder
2. Run YOUR milp_soft.py (unchanged)
3. Analyze utilization (new)
4. If needed, run registrar AI (improved)
5. Apply section changes
6. Loop back to step 2 (with modified sections)
```

### 2. What the Registrar AI Sees (Privacy-Focused)

```python
# Example of what we send to AI (NO personal data):
{
    "sections": [
        {
            "section_id": "S001",
            "course": "Biology",
            "capacity": 25,
            "enrolled": 30,
            "utilization": "120%",
            "teacher_load": "4/6 sections"
        },
        {
            "section_id": "S002", 
            "course": "Biology",
            "capacity": 25,
            "enrolled": 12,
            "utilization": "48%",
            "teacher_load": "3/6 sections"
        }
    ],
    "summary": {
        "total_sections": 129,
        "under_75_percent": 45,
        "over_115_percent": 15,
        "optimal_range": 69
    }
}
```

### 3. Integration with Existing Code

**milp_soft.py** - NO CHANGES except:
- Output paths use iteration manager
- Logs go to iteration-specific folder

**greedy.py** - NO CHANGES
- Still provides initial solution to Gurobi
- Works exactly as before

**New Wrapper Example**:
```python
class PipelineRunner:
    def run_iteration(self, iteration_num):
        # 1. Prepare clean workspace
        iter_path = self.prepare_iteration(iteration_num)
        
        # 2. Run YOUR existing MILP
        subprocess.run([
            "python", "src/core/milp_soft.py",
            "--input", iter_path.input,
            "--output", iter_path.output
        ])
        
        # 3. Analyze results (new)
        stats = self.analyze_utilization(iter_path.output)
        
        # 4. Run registrar if needed (new)
        if stats.needs_optimization:
            actions = self.registrar.decide(stats)
            self.apply_actions(actions)
```

## Key Differences from Original Plan

1. **NO new optimization models** - Using your existing Gurobi setup
2. **NO touching core algorithms** - milp_soft.py and greedy.py preserved
3. **NO student data to AI** - Only summary statistics
4. **Focus on pipeline** - Clean iteration management and better prompts

## What We're Actually Improving

### 1. Registrar Agent
- Clear prompts focused on 4 actions
- Only sees utilization percentages
- No access to personal data
- Better decision logic

### 2. Iteration Management  
- No more file overwrites
- Clean workspace for each iteration
- Full audit trail
- Easy rollback if needed

### 3. Action Processing
- SPLIT: Divide over-capacity sections (>115%)
- MERGE: Combine under-utilized sections (<75%)
- ADD: New sections for high-demand courses
- REMOVE: Delete very low enrollment sections

### 4. Summary Statistics for AI
- Section utilization percentages
- Teacher load summaries
- Course demand indicators
- NO individual student/teacher identities

## Benefits

1. **Your Gurobi engine unchanged** - Core optimization preserved
2. **Privacy preserved** - AI never sees personal data
3. **Clean iterations** - No more file corruption
4. **Better decisions** - Clearer prompts to AI
5. **Easy debugging** - Each iteration saved separately

This approach wraps your working Gurobi engine with better iteration management and an improved registrar agent, without disrupting the core optimization logic you've already built.