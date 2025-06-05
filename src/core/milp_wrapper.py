"""
MILP Wrapper - Adapts the existing milp_soft.py to work with OptimoV2 pipeline
"""

import os
import sys
from pathlib import Path

# This wrapper ensures milp_soft.py uses the correct input/output directories
# from environment variables set by the pipeline

def setup_milp_environment():
    """Setup environment for MILP to use pipeline directories"""
    
    # Get directories from environment
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    
    if not input_dir or not output_dir:
        # Fallback to default if not in pipeline
        input_dir = 'input'
        output_dir = 'output'
        
    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Temporarily change working directory for imports
    original_cwd = os.getcwd()
    milp_dir = Path(__file__).parent
    
    # Update sys.path to find load and greedy modules
    sys.path.insert(0, str(milp_dir))
    
    # Change to input directory for file loading
    os.chdir(input_dir)
    
    return original_cwd, input_dir, output_dir


# Run the setup before importing milp_soft
original_cwd, input_dir, output_dir = setup_milp_environment()

# Now import and run the original milp_soft
try:
    # Import the original milp_soft module
    import milp_soft
    
    # The milp_soft module runs automatically on import
    # No need to call anything else
    
finally:
    # Restore original working directory
    os.chdir(original_cwd)