#!/usr/bin/env python3
"""
Main entry point for OptimoV2 pipeline
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.runner import PipelineRunner


def main():
    """Main entry point"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='OptimoV2 School Schedule Optimizer')
    parser.add_argument('--config', type=str, 
                       default='config/settings.yaml',
                       help='Path to configuration file')
    parser.add_argument('--api-key', type=str,
                       help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--input-dir', type=str,
                       help='Override input directory')
    parser.add_argument('--generate-test-data', type=str, 
                       choices=['small', 'medium', 'large'],
                       help='Generate synthetic test data before running')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get base directory
    base_dir = Path(__file__).parent.parent
    
    # Generate test data if requested
    if args.generate_test_data:
        print(f"\nGenerating {args.generate_test_data} test data...")
        print("="*60)
        
        # Run the synthetic data generator
        generate_script = base_dir / 'scripts' / 'generate_synthetic_data.py'
        result = subprocess.run([
            sys.executable, str(generate_script), 
            '--size', args.generate_test_data
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error generating test data: {result.stderr}")
            sys.exit(1)
        else:
            print(result.stdout)
            print("\nTest data generated successfully!")
            print("="*60)
    
    # Load config to determine AI provider
    config_path = base_dir / args.config
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Always use Gemini as AI provider
    ai_provider = 'gemini'
    
    # Get Gemini API key
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: Gemini API key not provided")
        print("Set GEMINI_API_KEY environment variable or use --api-key")
        sys.exit(1)
        
        
    # Copy input files if specified
    if args.input_dir:
        input_path = Path(args.input_dir)
        if not input_path.exists():
            print(f"Error: Input directory not found: {input_path}")
            sys.exit(1)
            
        # Copy to base data directory
        base_data_dir = base_dir / 'data' / 'base'
        base_data_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Copying input files from {input_path} to {base_data_dir}")
        
        required_files = [
            'Student_Info.csv',
            'Student_Preference_Info.csv',
            'Teacher_Info.csv', 
            'Teacher_unavailability.csv',
            'Sections_Information.csv'
        ]
        
        optional_files = ['Period.csv']
        
        # Copy required files
        for file_name in required_files:
            src = input_path / file_name
            if not src.exists():
                print(f"Error: Required file not found: {src}")
                sys.exit(1)
            dst = base_data_dir / file_name
            import shutil
            shutil.copy2(src, dst)
            print(f"  Copied {file_name}")
            
        # Copy optional files if they exist
        for file_name in optional_files:
            src = input_path / file_name
            if src.exists():
                dst = base_data_dir / file_name
                shutil.copy2(src, dst)
                print(f"  Copied {file_name}")
    
    # Check that we have data to process
    base_data_dir = base_dir / 'data' / 'base'
    if not base_data_dir.exists() or not any(base_data_dir.iterdir()):
        print("\nError: No input data found in data/base/")
        print("Either:")
        print("  1. Use --input-dir to specify your data location")
        print("  2. Use --generate-test-data to create synthetic data")
        print("  3. Copy your CSV files to data/base/")
        sys.exit(1)
                
    # Run pipeline
    try:
        print("\nStarting OptimoV2 Pipeline...")
        print("Using AI provider: GEMINI")
        print("="*60)
        
        runner = PipelineRunner(config_path, api_key)
        results = runner.run()
        
        print("\n" + "="*60)
        print("Pipeline completed successfully!")
        print(f"Best iteration: {results['best_iteration']}")
        print(f"Final score: {results['best_score']:.2f}")
        print(f"Output saved to: {results['final_path']}")
        
        # Display utilization range
        if 'final_analysis' in results:
            print("\n" + "="*60)
            print("UTILIZATION SUMMARY:")
            print("="*60)
            
            min_util = results['final_analysis'].get('min_utilization')
            max_util = results['final_analysis'].get('max_utilization')
            
            if min_util:
                print(f"\nLowest Utilization Section:")
                print(f"  Section: {min_util['section_id']} ({min_util['course']})")
                print(f"  Utilization: {min_util['utilization_pct']} ({min_util['enrolled']}/{min_util['capacity']} students)")
                
            if max_util:
                print(f"\nHighest Utilization Section:")
                print(f"  Section: {max_util['section_id']} ({max_util['course']})")
                print(f"  Utilization: {max_util['utilization_pct']} ({max_util['enrolled']}/{max_util['capacity']} students)")
                
            # Show target range
            print(f"\nTarget Range: 70%-110%")
            
            # Show sections within range
            util_summary = results['final_analysis']['utilization_summary']
            total_sections = results['final_analysis']['total_sections']
            in_range = util_summary['optimal_range']
            
            print(f"Sections in target range: {in_range}/{total_sections} ({in_range/total_sections:.1%})")
            print(f"Average utilization: {util_summary['average_utilization']}")
        
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if args.debug or True:  # Always show traceback for debugging
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()