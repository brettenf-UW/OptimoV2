"""
Iteration Manager - Handles clean workspace management for each pipeline iteration
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class IterationManager:
    """Manages iteration workspaces to prevent file conflicts"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.data_dir = self.base_path / 'data'
        self.base_data_dir = self.data_dir / 'base'
        self.runs_dir = self.data_dir / 'runs'
        
        # Create directories if they don't exist
        self.base_data_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_run = None
        self.current_iteration = -1
        
    def start_new_run(self) -> Path:
        """Start a new optimization run with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"run_{timestamp}"
        self.current_run = self.runs_dir / run_name
        self.current_run.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.current_run / 'iterations').mkdir(exist_ok=True)
        (self.current_run / 'logs').mkdir(exist_ok=True)
        (self.current_run / 'final').mkdir(exist_ok=True)
        
        # Save run metadata
        metadata = {
            'run_id': run_name,
            'start_time': datetime.now().isoformat(),
            'status': 'started'
        }
        with open(self.current_run / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Started new run: {run_name}")
        return self.current_run
        
    def prepare_iteration(self, iteration_num: int, 
                         modified_sections_path: Optional[Path] = None) -> Dict[str, Path]:
        """Prepare a clean workspace for an iteration"""
        
        if self.current_run is None:
            raise RuntimeError("No active run. Call start_new_run() first.")
            
        self.current_iteration = iteration_num
        iter_dir = self.current_run / 'iterations' / f'iter_{iteration_num}'
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        # Create input/output directories
        input_dir = iter_dir / 'input'
        output_dir = iter_dir / 'output'
        input_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        
        # Copy base data files (except sections if we have modified ones)
        base_files = [
            'Student_Info.csv',
            'Student_Preference_Info.csv', 
            'Teacher_Info.csv',
            'Teacher_unavailability.csv',
            'Period.csv'
        ]
        
        for file_name in base_files:
            src = self.base_data_dir / file_name
            if src.exists():
                shutil.copy2(src, input_dir / file_name)
                
        # Handle sections file
        if modified_sections_path and modified_sections_path.exists():
            # Use modified sections from previous iteration
            shutil.copy2(modified_sections_path, input_dir / 'Sections_Information.csv')
            print(f"Using modified sections from: {modified_sections_path}")
        else:
            # Use original sections
            src = self.base_data_dir / 'Sections_Information.csv'
            if src.exists():
                shutil.copy2(src, input_dir / 'Sections_Information.csv')
                print("Using original base sections")
                
        # Save iteration metadata
        iter_metadata = {
            'iteration': iteration_num,
            'start_time': datetime.now().isoformat(),
            'modified_sections': str(modified_sections_path) if modified_sections_path else None
        }
        with open(iter_dir / 'metadata.json', 'w') as f:
            json.dump(iter_metadata, f, indent=2)
            
        return {
            'iter_dir': iter_dir,
            'input_dir': input_dir,
            'output_dir': output_dir,
            'logs_dir': self.current_run / 'logs'
        }
        
    def save_iteration_results(self, metrics: dict, status: str = 'completed'):
        """Save iteration results and metrics"""
        
        if self.current_iteration < 0:
            raise RuntimeError("No active iteration")
            
        iter_dir = self.current_run / 'iterations' / f'iter_{self.current_iteration}'
        
        # Update iteration metadata
        metadata_file = iter_dir / 'metadata.json'
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            
        metadata.update({
            'end_time': datetime.now().isoformat(),
            'status': status,
            'metrics': metrics
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Save detailed metrics
        with open(iter_dir / 'metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
            
    def get_iteration_output(self, iteration_num: int) -> Path:
        """Get the output directory for a specific iteration"""
        
        if self.current_run is None:
            raise RuntimeError("No active run")
            
        return self.current_run / 'iterations' / f'iter_{iteration_num}' / 'output'
        
    def finalize_run(self, best_iteration: int):
        """Copy the best iteration results to final output"""
        
        if self.current_run is None:
            raise RuntimeError("No active run")
            
        # Copy best iteration output to final
        best_output = self.get_iteration_output(best_iteration)
        final_dir = self.current_run / 'final'
        
        if best_output.exists():
            for file in best_output.glob('*.csv'):
                shutil.copy2(file, final_dir / file.name)
                
        # Update run metadata
        metadata_file = self.current_run / 'metadata.json'
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            
        metadata.update({
            'end_time': datetime.now().isoformat(),
            'status': 'completed',
            'best_iteration': best_iteration,
            'total_iterations': self.current_iteration + 1
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Run completed. Best results from iteration {best_iteration}")
        print(f"Final output saved to: {final_dir}")
        
    def get_run_summary(self) -> dict:
        """Get summary of the current run"""
        
        if self.current_run is None:
            return {"error": "No active run"}
            
        summary = {
            'run_path': str(self.current_run),
            'iterations': []
        }
        
        # Collect iteration summaries
        iter_dir = self.current_run / 'iterations'
        for iter_path in sorted(iter_dir.glob('iter_*')):
            metrics_file = iter_path / 'metrics.json'
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    summary['iterations'].append({
                        'iteration': iter_path.name,
                        'metrics': metrics
                    })
                    
        return summary