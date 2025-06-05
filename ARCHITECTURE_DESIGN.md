# OptimoV2 - Architecture Design Document

## Project Overview

OptimoV2 is a complete redesign of the school scheduling system with focus on:
- Clear, actionable optimization decisions
- Clean iteration management
- Percentage-based utilization targeting (75%-115%)
- Modular, maintainable architecture

## Directory Structure & Component Design

```
OptimoV2/
├── src/                           # All source code
│   ├── core/                      # Core business logic
│   │   ├── models/                # Data models & validation
│   │   │   ├── student.py         # Student data model
│   │   │   ├── teacher.py         # Teacher data model
│   │   │   ├── section.py         # Section data model
│   │   │   ├── schedule.py        # Schedule data model
│   │   │   └── constraints.py     # Constraint definitions
│   │   │
│   │   ├── algorithms/            # Core algorithms
│   │   │   ├── milp_solver.py     # MILP optimization engine
│   │   │   ├── greedy_solver.py   # Initial solution generator
│   │   │   └── solver_base.py     # Base solver interface
│   │   │
│   │   └── analysis/              # Analysis utilities
│   │       ├── utilization.py     # Utilization calculator
│   │       ├── conflicts.py       # Conflict detector
│   │       └── metrics.py         # Performance metrics
│   │
│   ├── optimization/              # Optimization layer
│   │   ├── registrar/             # AI-powered optimizer
│   │   │   ├── agent.py           # Registrar agent main class
│   │   │   ├── prompts.py         # Prompt templates
│   │   │   └── actions.py         # Action definitions
│   │   │
│   │   ├── actions/               # Action implementations
│   │   │   ├── split.py           # Split section logic
│   │   │   ├── merge.py           # Merge sections logic
│   │   │   ├── add.py             # Add section logic
│   │   │   ├── remove.py          # Remove section logic
│   │   │   └── base.py            # Base action interface
│   │   │
│   │   └── strategies/            # Optimization strategies
│   │       ├── utilization.py     # Utilization-based strategy
│   │       └── balanced.py        # Balanced load strategy
│   │
│   ├── pipeline/                  # Pipeline orchestration
│   │   ├── runner.py              # Main pipeline runner
│   │   ├── iteration_manager.py   # Iteration state management
│   │   ├── state_store.py         # Persistent state storage
│   │   └── config_loader.py       # Configuration management
│   │
│   ├── io/                        # Input/Output handling
│   │   ├── readers/               # Data readers
│   │   │   ├── csv_reader.py      # CSV file reader
│   │   │   └── validator.py       # Input validation
│   │   │
│   │   ├── writers/               # Data writers
│   │   │   ├── csv_writer.py      # CSV file writer
│   │   │   └── report_writer.py   # Report generator
│   │   │
│   │   └── schemas/               # Data schemas
│   │       ├── input_schemas.py   # Input file schemas
│   │       └── output_schemas.py  # Output file schemas
│   │
│   └── interfaces/                # User interfaces
│       ├── cli/                   # Command line interface
│       │   ├── main.py            # CLI entry point
│       │   └── commands.py        # CLI commands
│       │
│       └── web/                   # Web interface
│           ├── app.py             # Gradio web app
│           └── components.py      # UI components
│
├── data/                          # Data storage (git-ignored)
│   ├── base/                      # Original input files (immutable)
│   ├── runs/                      # Execution runs
│   │   └── run_YYYYMMDD_HHMMSS/  # Timestamped run folders
│   │       ├── iterations/        # Iteration snapshots
│   │       │   ├── iter_0/        # Initial state
│   │       │   ├── iter_1/        # After first optimization
│   │       │   └── iter_2/        # Final iteration
│   │       ├── logs/              # Execution logs
│   │       └── final/             # Final output
│   └── cache/                     # Temporary cache files
│
├── config/                        # Configuration files
│   ├── settings.yaml              # Main settings
│   ├── constraints.yaml           # Constraint definitions
│   ├── prompts/                   # AI prompt templates
│   │   ├── registrar_base.txt     # Base registrar prompt
│   │   ├── action_split.txt       # Split action prompt
│   │   ├── action_merge.txt       # Merge action prompt
│   │   └── action_review.txt      # Review changes prompt
│   └── logging.yaml               # Logging configuration
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── fixtures/                  # Test data
│
├── docs/                          # Documentation
│   ├── user_guide.md              # User documentation
│   ├── api_reference.md           # API documentation
│   ├── architecture.md            # Architecture details
│   └── troubleshooting.md         # Common issues
│
├── scripts/                       # Utility scripts
│   ├── setup.py                   # Installation script
│   ├── validate_data.py           # Data validation
│   └── migrate_v1_data.py         # Migration from old version
│
├── docker/                        # Docker configuration
│   ├── Dockerfile                 # Docker image
│   └── docker-compose.yml         # Multi-container setup
│
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── README.md                      # Project readme
└── .gitignore                     # Git ignore rules
```

## How Components Work Together

### 1. Data Flow Architecture

```
Input Files → Validators → Data Models → MILP Solver → Initial Schedule
                                             ↓
                                    Utilization Analyzer
                                             ↓
                                    Registrar Agent
                                             ↓
                                    Action Processor
                                             ↓
                                    Updated Schedule → MILP Solver
                                             ↓
                                        Final Output
```

### 2. Core Components Interaction

**Data Models (core/models/)**
- Define structured data with validation
- Ensure data integrity throughout pipeline
- Provide consistent interfaces for all components

**MILP Solver (core/algorithms/)**
- Takes validated data models as input
- Produces initial schedule respecting hard constraints
- Outputs schedule with utilization metrics

**Utilization Analyzer (core/analysis/)**
- Calculates exact utilization percentages
- Identifies sections outside 75%-115% range
- Provides actionable insights for registrar

**Registrar Agent (optimization/registrar/)**
- Receives utilization analysis
- Makes decisions based on clear rules
- Outputs specific actions (SPLIT/MERGE/ADD/REMOVE)

**Action Processor (optimization/actions/)**
- Takes registrar decisions
- Applies changes to section data
- Validates changes maintain feasibility

**Iteration Manager (pipeline/)**
- Manages clean workspace for each iteration
- Prevents file conflicts
- Tracks all changes with full audit trail

### 3. Key Design Principles

**Immutability**
- Base input data is never modified
- Each iteration works on copies
- All changes tracked and reversible

**Separation of Concerns**
- Each component has single responsibility
- Clear interfaces between components
- Easy to test and maintain

**Percentage-Based Logic**
- All decisions based on utilization percentages
- No hard-coded capacity limits
- Consistent 75%-115% target throughout

**Action Clarity**
- Only 4 possible actions
- Each action has clear criteria
- No ambiguous optimization goals

### 4. Iteration Management Strategy

**Run Structure**
```
runs/run_20240305_143022/
├── config.yaml              # Configuration for this run
├── iterations/
│   ├── iter_0/
│   │   ├── input/          # Input data for iteration
│   │   ├── output/         # MILP output
│   │   ├── analysis.json   # Utilization analysis
│   │   └── actions.json    # Registrar decisions
│   ├── iter_1/
│   │   ├── input/          # Modified sections from iter_0
│   │   ├── output/         # New MILP output
│   │   ├── analysis.json   # Updated analysis
│   │   └── actions.json    # New decisions
│   └── iter_2/             # Final iteration
├── logs/
│   ├── pipeline.log        # Main execution log
│   ├── milp.log           # MILP solver log
│   └── registrar.log      # Registrar agent log
└── final/                  # Best result from all iterations
```

### 5. Configuration Management

**settings.yaml**
- Utilization targets (min: 75%, max: 115%)
- Maximum iterations
- Algorithm parameters
- Resource limits

**constraints.yaml**
- Special course rules
- Teacher limits
- Room capacities
- Period restrictions

**Prompt Templates**
- Separate files for clarity
- Variable substitution supported
- Easy to modify without code changes

### 6. Error Handling & Recovery

**Validation at Every Step**
- Input validation before processing
- Action validation before applying
- Output validation before saving

**Graceful Degradation**
- If registrar fails, use heuristic rules
- If iteration fails, use previous best
- Always produce some output

**Comprehensive Logging**
- Structured logs for each component
- Debug mode for detailed tracing
- Performance metrics tracking

## Benefits of This Architecture

1. **Maintainability**: Clear structure, easy to find and fix issues
2. **Testability**: Each component can be tested independently
3. **Scalability**: Can handle larger datasets by optimizing components
4. **Debuggability**: Full audit trail, clear logs, iteration snapshots
5. **Flexibility**: Easy to swap algorithms or add new strategies
6. **Reliability**: No file conflicts, clean error handling

This architecture ensures that OptimoV2 will be robust, maintainable, and actually achieve the utilization targets while being much easier to understand and debug than the current system.