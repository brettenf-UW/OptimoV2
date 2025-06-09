"""
Registrar Agent - AI-powered section optimization
Uses Claude to make decisions based on utilization statistics only
"""

import json
import anthropic
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class RegistrarAgent:
    """AI agent that decides section optimization actions"""
    
    def __init__(self, api_key: str, config: Dict):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.config = config
        self.model = config.get('registrar', {}).get('model', 'claude-3-opus-20240229')
        self.max_changes = config.get('optimization', {}).get('actions', {}).get('max_changes_per_iteration', 10)
        
    def decide_actions(self, summary_stats: Dict, prompt_template: str) -> List[Dict]:
        """Get optimization decisions from Claude based on summary statistics"""
        
        # Format the prompt with actual data
        prompt = self._format_prompt(prompt_template, summary_stats)
        
        try:
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config.get('registrar', {}).get('max_tokens', 2000),
                temperature=self.config.get('registrar', {}).get('temperature', 0.1),
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract and parse response
            response_text = response.content[0].text.strip()
            
            # Try to extract JSON from response
            actions = self._parse_actions(response_text)
            
            print(f"Registrar suggested {len(actions)} actions")
            return actions
            
        except Exception as e:
            print(f"Error getting registrar decisions: {str(e)}")
            print("Please check your API key and try again.")
            raise e  # Don't fall back to heuristics
            
    def _format_prompt(self, template: str, summary_stats: Dict) -> str:
        """Format the prompt template with actual data"""
        
        # Create formatted sections list
        problem_sections_str = json.dumps(summary_stats['problem_sections'], indent=2)
        summary_stats_str = json.dumps(summary_stats['summary_stats'], indent=2)
        course_context_str = json.dumps(summary_stats.get('course_context', {}), indent=2)
        teacher_loads_str = json.dumps(summary_stats.get('teacher_loads', {}), indent=2)
        department_summary_str = json.dumps(summary_stats.get('department_summary', {}), indent=2)
        
        # Replace template variables
        prompt = template.format(
            summary_stats=summary_stats_str,
            problem_sections=problem_sections_str,
            course_context=course_context_str,
            teacher_loads=teacher_loads_str,
            department_summary=department_summary_str,
            max_teacher_sections=self.config.get('constraints', {}).get('max_teacher_sections', 6),
            max_changes=self.max_changes
        )
        
        return prompt
        
    def _parse_actions(self, response_text: str) -> List[Dict]:
        """Parse JSON actions from Claude's response"""
        
        try:
            # Look for JSON in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                actions = json.loads(json_str)
                
                # Validate actions
                validated_actions = []
                for action in actions:
                    if self._validate_action(action):
                        validated_actions.append(action)
                        
                return validated_actions[:self.max_changes]  # Limit to max changes
            else:
                print("No JSON found in response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from response: {e}")
            return []
            
    def _validate_action(self, action: Dict) -> bool:
        """Validate that an action has required fields"""
        
        required_fields = {
            'SPLIT': ['action', 'section_id', 'reason'],
            'MERGE': ['action', 'section_ids', 'reason'],
            'ADD': ['action', 'course', 'reason'],
            'REMOVE': ['action', 'section_id', 'reason']
        }
        
        action_type = action.get('action')
        if action_type not in required_fields:
            return False
            
        for field in required_fields[action_type]:
            if field not in action:
                return False
                
        # Additional validation for MERGE - must have exactly 2 section IDs
        if action_type == 'MERGE':
            section_ids = action.get('section_ids', [])
            if not isinstance(section_ids, list) or len(section_ids) != 2:
                print(f"MERGE action must have exactly 2 section_ids, got {len(section_ids)}")
                return False
                
        return True
        
    def _heuristic_decisions(self, summary_stats: Dict) -> List[Dict]:
        """Fallback heuristic rules if AI fails - respects one action per course"""
        
        actions = []
        problem_sections = summary_stats.get('problem_sections', [])
        course_actions = {}  # Track one action per course
        
        # Group by course for merge opportunities
        course_sections = {}
        for section in problem_sections:
            course = section['course']
            if course not in course_sections:
                course_sections[course] = []
            course_sections[course].append(section)
            
        # Apply simple rules - ONE ACTION PER COURSE
        for section in problem_sections:
            course = section['course']
            
            # Skip if we already have an action for this course
            if course in course_actions:
                continue
                
            util_str = section['utilization']
            util_pct = float(util_str.rstrip('%')) / 100
            enrollment_info = section.get('enrollment_vs_capacity', '0/0')
            enrolled = int(enrollment_info.split('/')[0])
            capacity = int(enrollment_info.split('/')[1])
            
            # Over capacity - split or add (>110%)
            if util_pct > 1.10 and len(actions) < self.max_changes:
                if util_pct > 1.30:  # Severely over capacity
                    action = {
                        'action': 'ADD',
                        'course': section['course'],
                        'reason': f"Severe overcrowding at {section['utilization']} - need additional section"
                    }
                    actions.append(action)
                    course_actions[course] = action
                elif util_pct > 1.20:  # Moderately over, try split
                    action = {
                        'action': 'SPLIT',
                        'section_id': section['section_id'],
                        'reason': f"{section['utilization']} utilization with {enrolled} students"
                    }
                    actions.append(action)
                    course_actions[course] = action
                
            # Under capacity - try to merge (<70%)
            elif util_pct < 0.70 and len(actions) < self.max_changes:
                # Look for merge partner
                course = section['course']
                partners = [s for s in course_sections[course] 
                           if s['section_id'] != section['section_id'] 
                           and float(s['utilization'].rstrip('%')) / 100 < 0.70]
                
                if partners:
                    # Find best merge partner
                    for partner in partners:
                        partner_info = partner.get('enrollment_vs_capacity', '0/0')
                        partner_enrolled = int(partner_info.split('/')[0])
                        combined_enrollment = enrolled + partner_enrolled
                        
                        # Check if combined would be in target range
                        avg_capacity = (capacity + int(partner_info.split('/')[1])) / 2
                        combined_util = combined_enrollment / avg_capacity
                        
                        if 0.70 <= combined_util <= 1.10:
                            action = {
                                'action': 'MERGE',
                                'section_ids': [section['section_id'], partner['section_id']],
                                'reason': f"Both under 70% utilization, combined would be {combined_util:.0%}"
                            }
                            actions.append(action)
                            course_actions[course] = action
                            break
                
                # If no merge partner found, consider removal
                elif util_pct < 0.70:
                    is_only_section = len(course_sections[course]) == 1
                    if util_pct < 0.65 or is_only_section:
                        action = {
                            'action': 'REMOVE',
                            'section_id': section['section_id'],
                            'reason': f"Only {util_pct:.0%} utilization, no merge partner available"
                        }
                        actions.append(action)
                        course_actions[course] = action
                    
        return actions[:self.max_changes]