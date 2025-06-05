"""
Utilization Analyzer - Creates summary statistics for the registrar AI
NO student personal data is exposed, only aggregate statistics
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import json


class UtilizationAnalyzer:
    """Analyzes section utilization and creates privacy-safe summaries"""
    
    def __init__(self, min_target: float = 0.75, max_target: float = 1.15):
        self.min_target = min_target
        self.max_target = max_target
        
    def analyze_schedule(self, output_dir: Path) -> Dict:
        """Analyze schedule output and create summary statistics"""
        
        # Load necessary files
        sections_df = pd.read_csv(output_dir.parent / 'input' / 'Sections_Information.csv')
        student_assignments = pd.read_csv(output_dir / 'Student_Assignments.csv')
        teacher_schedule = pd.read_csv(output_dir / 'Teacher_Schedule.csv')
        
        # Count enrollments per section
        enrollment_counts = student_assignments['Section ID'].value_counts().to_dict()
        
        # Calculate utilization for each section
        utilization_data = []
        problem_sections = []
        
        for _, section in sections_df.iterrows():
            section_id = section['Section ID']
            capacity = section['# of Seats Available']
            enrolled = enrollment_counts.get(section_id, 0)
            utilization = enrolled / capacity if capacity > 0 else 0
            
            section_info = {
                'section_id': section_id,
                'course': section['Course ID'],
                'capacity': capacity,
                'enrolled': enrolled,
                'utilization': utilization,
                'utilization_pct': f"{utilization:.1%}"
            }
            
            utilization_data.append(section_info)
            
            # Identify problem sections
            if utilization < self.min_target or utilization > self.max_target:
                problem_sections.append(section_info)
                
        # Calculate teacher loads (privacy-safe)
        teacher_loads = {}
        for teacher_id in sections_df['Teacher Assigned'].unique():
            sections_taught = len(sections_df[sections_df['Teacher Assigned'] == teacher_id])
            teacher_loads[teacher_id] = f"{sections_taught}/6 sections"
            
        # Create summary statistics
        summary = {
            'total_sections': len(sections_df),
            'total_students_assigned': len(student_assignments),
            'utilization_summary': {
                'under_target': sum(1 for d in utilization_data if d['utilization'] < self.min_target),
                'optimal_range': sum(1 for d in utilization_data if self.min_target <= d['utilization'] <= self.max_target),
                'over_target': sum(1 for d in utilization_data if d['utilization'] > self.max_target),
                'average_utilization': f"{sum(d['utilization'] for d in utilization_data) / len(utilization_data):.1%}"
            },
            'sections_by_utilization': self._categorize_utilization(utilization_data),
            'problem_sections': problem_sections,
            'teacher_load_summary': teacher_loads
        }
        
        return summary
        
    def _categorize_utilization(self, utilization_data: List[Dict]) -> Dict:
        """Categorize sections by utilization level"""
        
        categories = {
            'severely_under': [],  # < 50%
            'under': [],          # 50-75%
            'optimal': [],        # 75-115%
            'over': [],           # 115-150%
            'severely_over': []   # > 150%
        }
        
        for section in utilization_data:
            util = section['utilization']
            
            if util < 0.50:
                categories['severely_under'].append(section['section_id'])
            elif util < self.min_target:
                categories['under'].append(section['section_id'])
            elif util <= self.max_target:
                categories['optimal'].append(section['section_id'])
            elif util <= 1.50:
                categories['over'].append(section['section_id'])
            else:
                categories['severely_over'].append(section['section_id'])
                
        return {k: len(v) for k, v in categories.items()}
        
    def create_registrar_summary(self, output_dir: Path) -> Dict:
        """Create a privacy-safe summary for the registrar AI"""
        
        analysis = self.analyze_schedule(output_dir)
        
        # Format for AI consumption
        registrar_summary = {
            'summary_stats': {
                'total_sections': analysis['total_sections'],
                'sections_needing_action': (
                    analysis['utilization_summary']['under_target'] + 
                    analysis['utilization_summary']['over_target']
                ),
                'average_utilization': analysis['utilization_summary']['average_utilization']
            },
            'problem_sections': []
        }
        
        # Add problem sections with anonymized data
        for section in analysis['problem_sections']:
            registrar_summary['problem_sections'].append({
                'section_id': section['section_id'],
                'course': section['course'],
                'utilization': section['utilization_pct'],
                'enrollment_vs_capacity': f"{section['enrolled']}/{section['capacity']}"
            })
            
        return registrar_summary
        
    def calculate_optimization_score(self, analysis: Dict) -> float:
        """Calculate a score for the current schedule (lower is better)"""
        
        # Penalize sections outside target range
        under_penalty = analysis['utilization_summary']['under_target'] * 2
        over_penalty = analysis['utilization_summary']['over_target'] * 3  # Over-capacity is worse
        
        # Bonus for sections in optimal range
        optimal_bonus = analysis['utilization_summary']['optimal_range'] * -0.5
        
        return under_penalty + over_penalty + optimal_bonus
        
    def save_analysis(self, analysis: Dict, output_path: Path):
        """Save analysis results to file"""
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
            
    def needs_optimization(self, analysis: Dict) -> bool:
        """Determine if the schedule needs further optimization"""
        
        # Need optimization if more than 5% of sections are outside target range
        total = analysis['total_sections']
        outside_target = (
            analysis['utilization_summary']['under_target'] + 
            analysis['utilization_summary']['over_target']
        )
        
        return (outside_target / total) > 0.05 if total > 0 else False