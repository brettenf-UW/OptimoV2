"""
Action Processor - Implements SPLIT, MERGE, ADD, REMOVE actions on sections
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import json


class ActionProcessor:
    """Processes optimization actions on section data"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.constraints = config.get('constraints', {})
        
    def apply_actions(self, sections_df: pd.DataFrame, actions: List[Dict], 
                     output_dir: Path) -> Tuple[pd.DataFrame, Dict]:
        """Apply registrar actions to sections dataframe"""
        
        # Make a copy to avoid modifying original
        modified_sections = sections_df.copy()
        
        # Track what we did
        changes_log = {
            'actions_requested': len(actions),
            'actions_applied': 0,
            'actions_failed': 0,
            'details': []
        }
        
        # Get current enrollment data for validation
        student_assignments = pd.read_csv(output_dir / 'Student_Assignments.csv')
        enrollment_counts = student_assignments['Section ID'].value_counts().to_dict()
        
        # Process each action
        for action in actions:
            action_type = action.get('action')
            
            try:
                if action_type == 'SPLIT':
                    modified_sections, success = self._split_section(
                        modified_sections, action, enrollment_counts
                    )
                elif action_type == 'MERGE':
                    modified_sections, success = self._merge_sections(
                        modified_sections, action, enrollment_counts
                    )
                elif action_type == 'ADD':
                    modified_sections, success = self._add_section(
                        modified_sections, action
                    )
                elif action_type == 'REMOVE':
                    modified_sections, success = self._remove_section(
                        modified_sections, action, enrollment_counts
                    )
                else:
                    success = False
                    
                if success:
                    changes_log['actions_applied'] += 1
                    changes_log['details'].append({
                        'action': action,
                        'status': 'success'
                    })
                else:
                    changes_log['actions_failed'] += 1
                    changes_log['details'].append({
                        'action': action,
                        'status': 'failed'
                    })
                    
            except Exception as e:
                changes_log['actions_failed'] += 1
                changes_log['details'].append({
                    'action': action,
                    'status': 'error',
                    'error': str(e)
                })
                
        return modified_sections, changes_log
        
    def _split_section(self, sections_df: pd.DataFrame, action: Dict, 
                      enrollment_counts: Dict) -> Tuple[pd.DataFrame, bool]:
        """Split an over-capacity section into two"""
        
        section_id = action['section_id']
        
        # Find the section
        section_mask = sections_df['Section ID'] == section_id
        if not section_mask.any():
            print(f"Section {section_id} not found")
            return sections_df, False
            
        section = sections_df[section_mask].iloc[0]
        enrolled = enrollment_counts.get(section_id, 0)
        
        # Calculate new capacities (split evenly)
        original_capacity = section['# of Seats Available']
        new_capacity_1 = original_capacity // 2
        new_capacity_2 = original_capacity - new_capacity_1
        
        # Update original section
        sections_df.loc[section_mask, '# of Seats Available'] = new_capacity_1
        
        # Create new section
        new_section = section.copy()
        new_section['Section ID'] = f"{section_id}_B"
        new_section['# of Seats Available'] = new_capacity_2
        
        # Add new section
        sections_df = pd.concat([sections_df, pd.DataFrame([new_section])], ignore_index=True)
        
        print(f"Split section {section_id} into two sections with capacities {new_capacity_1} and {new_capacity_2}")
        return sections_df, True
        
    def _merge_sections(self, sections_df: pd.DataFrame, action: Dict,
                       enrollment_counts: Dict) -> Tuple[pd.DataFrame, bool]:
        """Merge two under-utilized sections"""
        
        section_ids = action['section_ids']
        if len(section_ids) != 2:
            print(f"Merge requires exactly 2 sections, got {len(section_ids)}")
            return sections_df, False
            
        # Find both sections
        section1_mask = sections_df['Section ID'] == section_ids[0]
        section2_mask = sections_df['Section ID'] == section_ids[1]
        
        if not (section1_mask.any() and section2_mask.any()):
            print(f"One or both sections not found")
            return sections_df, False
            
        section1 = sections_df[section1_mask].iloc[0]
        section2 = sections_df[section2_mask].iloc[0]
        
        # Verify same course
        if section1['Course ID'] != section2['Course ID']:
            print(f"Cannot merge different courses")
            return sections_df, False
            
        # Calculate combined enrollment
        enrolled1 = enrollment_counts.get(section_ids[0], 0)
        enrolled2 = enrollment_counts.get(section_ids[1], 0)
        combined_enrollment = enrolled1 + enrolled2
        
        # Use larger capacity or sum if needed
        new_capacity = max(
            section1['# of Seats Available'],
            section2['# of Seats Available'],
            combined_enrollment + 5  # Buffer of 5 seats
        )
        
        # Update first section with combined capacity
        sections_df.loc[section1_mask, '# of Seats Available'] = new_capacity
        
        # Remove second section
        sections_df = sections_df[~section2_mask]
        
        print(f"Merged sections {section_ids[0]} and {section_ids[1]} with combined capacity {new_capacity}")
        return sections_df, True
        
    def _add_section(self, sections_df: pd.DataFrame, action: Dict) -> Tuple[pd.DataFrame, bool]:
        """Add a new section for a high-demand course"""
        
        course_id = action['course']
        
        # Find existing sections for this course
        course_sections = sections_df[sections_df['Course ID'] == course_id]
        if course_sections.empty:
            print(f"No existing sections found for course {course_id}")
            return sections_df, False
            
        # Use first section as template
        template = course_sections.iloc[0].copy()
        
        # Generate new section ID
        existing_ids = sections_df['Section ID'].tolist()
        new_id = f"S{len(sections_df) + 1:03d}"
        while new_id in existing_ids:
            new_id = f"S{len(sections_df) + len(existing_ids) + 1:03d}"
            
        # Create new section
        template['Section ID'] = new_id
        
        # Add to dataframe
        sections_df = pd.concat([sections_df, pd.DataFrame([template])], ignore_index=True)
        
        print(f"Added new section {new_id} for course {course_id}")
        return sections_df, True
        
    def _remove_section(self, sections_df: pd.DataFrame, action: Dict,
                       enrollment_counts: Dict) -> Tuple[pd.DataFrame, bool]:
        """Remove a very low enrollment section"""
        
        section_id = action['section_id']
        enrolled = enrollment_counts.get(section_id, 0)
        
        # Safety check - don't remove if too many students
        min_enrollment = self.config.get('optimization', {}).get('actions', {}).get('min_enrollment_to_keep', 5)
        if enrolled >= min_enrollment:
            print(f"Section {section_id} has {enrolled} students, too many to remove")
            return sections_df, False
            
        # Remove the section
        sections_df = sections_df[sections_df['Section ID'] != section_id]
        
        print(f"Removed section {section_id} with {enrolled} students")
        return sections_df, True
        
    def save_changes_log(self, changes_log: Dict, output_path: Path):
        """Save the changes log for audit trail"""
        
        with open(output_path, 'w') as f:
            json.dump(changes_log, f, indent=2)