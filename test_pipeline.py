#!/usr/bin/env python3
"""
Simple test script for OptimoV2 pipeline
"""

import os
import sys
from pathlib import Path

# Set console encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Import and run
try:
    # First generate test data
    print("Generating test data...")
    from scripts import generate_synthetic_data
    
    # Set up output path
    output_path = Path(__file__).parent / 'data' / 'base'
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate small dataset
    generate_synthetic_data.generate_synthetic_data(str(output_path), students_per_grade=25)
    
    print("\nRunning optimization pipeline...")
    
    # Now run the pipeline
    from scripts import run_pipeline
    
    # Simulate command line args
    class Args:
        config = 'config/settings.yaml'
        api_key = None
        input_dir = None
        generate_test_data = None
        debug = False
        ai_provider = 'gemini'
    
    sys.argv = ['test_pipeline.py']  # Reset argv
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment")
        sys.exit(1)
    
    # Run pipeline
    from src.pipeline.runner import PipelineRunner
    
    config_path = Path(__file__).parent / 'config' / 'settings.yaml'
    runner = PipelineRunner(config_path, api_key)
    results = runner.run()
    
    print("\nPipeline completed successfully!")
    print(f"Best iteration: {results['best_iteration']}")
    print(f"Final score: {results['best_score']:.2f}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()