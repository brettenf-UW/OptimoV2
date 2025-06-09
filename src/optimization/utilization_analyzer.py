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
    
    def __init__(self, min_target: float = 0.70, max_target: float = 1.10):
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
            
        # Find min and max utilization sections
        if utilization_data:
            min_section = min(utilization_data, key=lambda x: x['utilization'])
            max_section = max(utilization_data, key=lambda x: x['utilization'])
        else:
            min_section = max_section = None
            
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
            'teacher_load_summary': teacher_loads,
            'min_utilization': min_section,
            'max_utilization': max_section
        }
        
        return summary
        
    def _categorize_utilization(self, utilization_data: List[Dict]) -> Dict:
        """Categorize sections by utilization level"""
        
        categories = {
            'severely_under': [],  # < 50%
            'under': [],          # 50-70%
            'optimal': [],        # 70-110%
            'over': [],           # 110-150%
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
        
        # Group all sections by course for context
        sections_df = pd.read_csv(output_dir.parent / 'input' / 'Sections_Information.csv')
        student_assignments = pd.read_csv(output_dir / 'Student_Assignments.csv')
        enrollment_counts = student_assignments['Section ID'].value_counts().to_dict()
        
        course_sections = {}
        for _, section in sections_df.iterrows():
            course = section['Course ID']
            section_id = section['Section ID']
            capacity = section['# of Seats Available']
            enrolled = enrollment_counts.get(section_id, 0)
            utilization = enrolled / capacity if capacity > 0 else 0
            
            if course not in course_sections:
                course_sections[course] = []
            
            course_sections[course].append({
                'section_id': section_id,
                'utilization': f"{utilization:.1%}",
                'enrollment': f"{enrolled}/{capacity}"
            })
        
        # Add teacher load analysis with department info
        teacher_df = pd.read_csv(output_dir / 'Teacher_Schedule.csv')
        teacher_info_df = pd.read_csv(output_dir.parent / 'input' / 'Teacher_Info.csv')
        teacher_loads = {}
        max_sections = 6  # From config
        
        # Group teachers by department
        dept_teachers = {}
        for _, teacher in teacher_info_df.iterrows():
            teacher_id = teacher['Teacher ID']
            dept = teacher.get('Department', 'Unknown')
            
            if dept not in dept_teachers:
                dept_teachers[dept] = []
            
            sections_taught = len(teacher_df[teacher_df['Teacher ID'] == teacher_id])
            available_slots = max_sections - sections_taught
            
            teacher_info = {
                'id': teacher_id,
                'current_load': sections_taught,
                'max_load': max_sections,
                'available_slots': available_slots,
                'utilization': f"{(sections_taught/max_sections)*100:.0f}%"
            }
            
            teacher_loads[teacher_id] = teacher_info
            dept_teachers[dept].append(teacher_info)
        
        # Analyze course capacity vs demand with more detail
        course_analysis = {}
        for course, sections in course_sections.items():
            total_capacity = sum(int(s['enrollment'].split('/')[1]) for s in sections)
            total_enrolled = sum(int(s['enrollment'].split('/')[0]) for s in sections)
            avg_utilization = total_enrolled / total_capacity if total_capacity > 0 else 0
            
            # Get teacher info for this course
            course_teachers = []
            for s in sections:
                section_data = sections_df[sections_df['Section ID'] == s['section_id']].iloc[0]
                teacher_id = section_data['Teacher Assigned']
                course_teachers.append(teacher_id)
            
            # Count sections by utilization range
            util_ranges = {
                'critical_low': len([s for s in sections if float(s['utilization'].rstrip('%')) < 65]),
                'low': len([s for s in sections if 65 <= float(s['utilization'].rstrip('%')) < 70]),
                'optimal': len([s for s in sections if 70 <= float(s['utilization'].rstrip('%')) <= 110]),
                'high': len([s for s in sections if 110 < float(s['utilization'].rstrip('%')) <= 130]),
                'critical_high': len([s for s in sections if float(s['utilization'].rstrip('%')) > 130])
            }
            
            course_analysis[course] = {
                'sections': sections,
                'section_count': len(sections),
                'total_capacity': total_capacity,
                'total_enrolled': total_enrolled,
                'average_utilization': f"{avg_utilization:.1%}",
                'capacity_buffer': total_capacity - total_enrolled,
                'utilization_distribution': util_ranges,
                'teachers_assigned': list(set(course_teachers)),
                'can_add_section': total_capacity - total_enrolled < 0  # Negative buffer means over capacity
            }
        
        # Add department summary for better visibility
        dept_summary = {}
        for dept, teachers in dept_teachers.items():
            total_teachers = len(teachers)
            total_available_slots = sum(t['available_slots'] for t in teachers)
            avg_load = sum(t['current_load'] for t in teachers) / total_teachers if total_teachers > 0 else 0
            
            dept_summary[dept] = {
                'total_teachers': total_teachers,
                'total_available_slots': total_available_slots,
                'average_load': f"{avg_load:.1f}",
                'teachers_at_capacity': len([t for t in teachers if t['available_slots'] == 0]),
                'teachers_with_availability': len([t for t in teachers if t['available_slots'] > 0])
            }
        
        # Add system-wide metrics
        system_metrics = {
            'total_sections': analysis['total_sections'],
            'total_students': analysis['total_students_assigned'],
            'sections_needing_action': (
                analysis['utilization_summary']['under_target'] + 
                analysis['utilization_summary']['over_target']
            ),
            'average_utilization': analysis['utilization_summary']['average_utilization'],
            'sections_under_target': analysis['utilization_summary']['under_target'],
            'sections_optimal': analysis['utilization_summary']['optimal_range'],
            'sections_over_target': analysis['utilization_summary']['over_target']
        }
        
        # Format for AI consumption
        registrar_summary = {
            'summary_stats': system_metrics,
            'problem_sections': [],
            'course_context': course_analysis,  # Enhanced course context
            'teacher_loads': teacher_loads,     # Individual teacher info
            'department_summary': dept_summary  # Department-level summary
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
        
        # Need optimization if ANY sections are outside target range
        outside_target = (
            analysis['utilization_summary']['under_target'] + 
            analysis['utilization_summary']['over_target']
        )
        
        # Continue optimizing until ALL sections are within 75%-110%
        return outside_target > 0