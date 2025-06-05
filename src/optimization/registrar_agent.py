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
            # Fall back to heuristic rules
            return self._heuristic_decisions(summary_stats)
            
    def _format_prompt(self, template: str, summary_stats: Dict) -> str:
        """Format the prompt template with actual data"""
        
        # Create formatted sections list
        problem_sections_str = json.dumps(summary_stats['problem_sections'], indent=2)
        summary_stats_str = json.dumps(summary_stats['summary_stats'], indent=2)
        
        # Replace template variables
        prompt = template.format(
            summary_stats=summary_stats_str,
            problem_sections=problem_sections_str,
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
                
        return True
        
    def _heuristic_decisions(self, summary_stats: Dict) -> List[Dict]:
        """Fallback heuristic rules if AI fails"""
        
        actions = []
        problem_sections = summary_stats.get('problem_sections', [])
        
        # Group by course for merge opportunities
        course_sections = {}
        for section in problem_sections:
            course = section['course']
            if course not in course_sections:
                course_sections[course] = []
            course_sections[course].append(section)
            
        # Apply simple rules
        for section in problem_sections:
            util_str = section['utilization']
            util_pct = float(util_str.rstrip('%')) / 100
            
            # Over capacity - split
            if util_pct > 1.15 and len(actions) < self.max_changes:
                actions.append({
                    'action': 'SPLIT',
                    'section_id': section['section_id'],
                    'reason': f"{section['utilization']} utilization"
                })
                
            # Under capacity - try to merge
            elif util_pct < 0.75 and len(actions) < self.max_changes:
                # Look for merge partner
                course = section['course']
                partners = [s for s in course_sections[course] 
                           if s['section_id'] != section['section_id'] 
                           and float(s['utilization'].rstrip('%')) / 100 < 0.75]
                
                if partners:
                    # Check if we haven't already planned to merge these
                    existing_merges = [a for a in actions if a['action'] == 'MERGE']
                    section_ids = {section['section_id'], partners[0]['section_id']}
                    
                    already_planned = any(
                        set(a['section_ids']) & section_ids 
                        for a in existing_merges
                    )
                    
                    if not already_planned:
                        actions.append({
                            'action': 'MERGE',
                            'section_ids': [section['section_id'], partners[0]['section_id']],
                            'reason': f"Both sections under 75% utilization"
                        })
                        
                elif util_pct < 0.25:  # Very low - remove
                    actions.append({
                        'action': 'REMOVE',
                        'section_id': section['section_id'],
                        'reason': f"Only {section['utilization']} utilization"
                    })
                    
        return actions[:self.max_changes]