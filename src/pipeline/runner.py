"""
Pipeline Runner - Main orchestrator for the optimization pipeline
"""

import os
import sys
import subprocess
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.iteration_manager import IterationManager
from src.optimization.utilization_analyzer import UtilizationAnalyzer
from src.optimization.registrar_agent_gemini import RegistrarAgentGemini
from src.optimization.action_processor import ActionProcessor
from src.utils.logger import setup_logger


class PipelineRunner:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_path: Path, api_key: str):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Initialize components
        self.iteration_manager = IterationManager(config_path.parent.parent)
        self.analyzer = UtilizationAnalyzer(
            min_target=self.config['optimization']['utilization']['min_target'],
            max_target=self.config['optimization']['utilization']['max_target']
        )
        
        # Initialize Gemini AI agent
        self.registrar = RegistrarAgentGemini(api_key, self.config)
            
        self.action_processor = ActionProcessor(self.config)
        
        # Setup logging
        self.logger = setup_logger('pipeline', self.config)
        
        # Load prompt template
        prompt_path = config_path.parent / 'prompts' / 'registrar_simple.txt'
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
            
    def run(self) -> Dict:
        """Run the complete optimization pipeline"""
        
        self.logger.info("="*60)
        self.logger.info("Starting OptimoV2 Pipeline")
        self.logger.info("="*60)
        
        # Start new run
        run_path = self.iteration_manager.start_new_run()
        self.logger.info(f"Run path: {run_path}")
        
        # Track best result
        best_iteration = 0
        best_score = float('inf')
        results = []
        
        # Early stopping tracking
        consecutive_no_change = 0
        max_no_change = 1  # Stop immediately when no changes can be made
        
        max_iterations = self.config['pipeline']['max_iterations']
        
        for i in range(max_iterations):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ITERATION {i}")
            self.logger.info(f"{'='*60}")
            
            # Prepare iteration workspace
            if i == 0:
                # First iteration - use base data
                workspace = self.iteration_manager.prepare_iteration(i)
            else:
                # Subsequent iterations - use modified sections
                prev_output = self.iteration_manager.get_iteration_output(i-1)
                modified_sections_path = prev_output.parent / 'modified_sections.csv'
                workspace = self.iteration_manager.prepare_iteration(i, modified_sections_path)
                
            # Run MILP optimization
            self.logger.info("Running MILP optimization...")
            milp_success = self._run_milp(workspace)
            
            if not milp_success:
                self.logger.error("MILP optimization failed")
                break
                
            # Analyze utilization
            self.logger.info("Analyzing utilization...")
            analysis = self.analyzer.analyze_schedule(workspace['output_dir'])
            
            # Save analysis
            self.analyzer.save_analysis(
                analysis, 
                workspace['iter_dir'] / 'utilization_analysis.json'
            )
            
            # Calculate score
            score = self.analyzer.calculate_optimization_score(analysis)
            self.logger.info(f"Iteration score: {score:.2f}")
            
            # Track best result
            if score < best_score:
                best_score = score
                best_iteration = i
                
            # Save iteration metrics
            metrics = {
                'score': score,
                'utilization_summary': analysis['utilization_summary'],
                'sections_by_utilization': analysis['sections_by_utilization']
            }
            self.iteration_manager.save_iteration_results(metrics)
            results.append(metrics)
            
            # Check if optimization is needed
            if not self.analyzer.needs_optimization(analysis):
                self.logger.info("✓ Schedule is optimized! All sections within target range.")
                break
                
            # Run registrar optimization (except on last iteration)
            if i < max_iterations - 1:
                self.logger.info("Running registrar optimization...")
                
                # Get registrar decisions
                registrar_summary = self.analyzer.create_registrar_summary(workspace['output_dir'])
                actions = self.registrar.decide_actions(registrar_summary, self.prompt_template)
                
                # Save actions
                with open(workspace['iter_dir'] / 'registrar_actions.json', 'w') as f:
                    json.dump(actions, f, indent=2)
                    
                if actions:
                    # Apply actions
                    self.logger.info(f"Applying {len(actions)} actions...")
                    sections_df = pd.read_csv(workspace['input_dir'] / 'Sections_Information.csv')
                    
                    modified_sections, changes_log = self.action_processor.apply_actions(
                        sections_df, actions, workspace['output_dir']
                    )
                    
                    # Save modified sections for next iteration
                    modified_sections_path = workspace['iter_dir'] / 'modified_sections.csv'
                    modified_sections.to_csv(modified_sections_path, index=False)
                    
                    # Save changes log
                    self.action_processor.save_changes_log(
                        changes_log,
                        workspace['iter_dir'] / 'changes_log.json'
                    )
                    
                    self.logger.info(f"Applied {changes_log['actions_applied']} actions successfully")
                    
                    # Check for early stopping
                    if changes_log['actions_applied'] == 0:
                        consecutive_no_change += 1
                        self.logger.info(f"No actions applied this iteration (consecutive: {consecutive_no_change})")
                        
                        if consecutive_no_change >= max_no_change:
                            self.logger.info(f"Stopping early - no progress in {max_no_change} consecutive iterations")
                            break
                    else:
                        consecutive_no_change = 0  # Reset counter
                        
                else:
                    self.logger.info("No actions suggested by registrar")
                    consecutive_no_change += 1
                    
                    if consecutive_no_change >= max_no_change:
                        self.logger.info(f"Stopping early - no actions suggested for {max_no_change} consecutive iterations")
                        break
                    
        # Get final analysis for the best iteration
        best_output_dir = self.iteration_manager.get_iteration_output(best_iteration)
        final_analysis = self.analyzer.analyze_schedule(best_output_dir)
        
        # Finalize run with best iteration
        self.logger.info(f"\nOptimization complete! Best result from iteration {best_iteration}")
        self.iteration_manager.finalize_run(best_iteration)
        
        # Return summary with final analysis
        return {
            'status': 'completed',
            'best_iteration': best_iteration,
            'best_score': best_score,
            'total_iterations': len(results),
            'final_path': str(run_path / 'final'),
            'results': results,
            'final_analysis': final_analysis
        }
        
    def _run_milp(self, workspace: Dict) -> bool:
        """Run the MILP optimization engine"""
        
        try:
            # Get paths
            milp_path = Path(__file__).parent.parent / 'core' / 'milp_soft.py'
            
            # Set environment variables for paths
            env = os.environ.copy()
            env['INPUT_DIR'] = str(workspace['input_dir'])
            env['OUTPUT_DIR'] = str(workspace['output_dir'])
            
            # Run MILP with UTF-8 encoding to avoid Windows decode errors
            result = subprocess.run(
                [sys.executable, str(milp_path)],
                env=env,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=workspace['input_dir']
            )
            
            if result.returncode != 0:
                self.logger.error(f"MILP failed with return code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return False
                
            # Check that output files were created
            expected_files = [
                'Master_Schedule.csv',
                'Student_Assignments.csv',
                'Teacher_Schedule.csv',
                'Constraint_Violations.csv'
            ]
            
            for file_name in expected_files:
                if not (workspace['output_dir'] / file_name).exists():
                    self.logger.error(f"Expected output file {file_name} not found")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error running MILP: {str(e)}")
            return False


# Import pandas here to avoid circular imports
import pandas as pd