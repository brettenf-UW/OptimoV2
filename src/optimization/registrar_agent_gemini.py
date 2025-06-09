"""
Registrar Agent - AI-powered section optimization using Google Gemini
Uses Gemini 2.0 Flash to make decisions based on utilization statistics
"""

import json
import requests
import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class RegistrarAgentGemini:
    """AI agent that decides section optimization actions using Google Gemini"""
    
    def __init__(self, api_key: str, config: Dict):
        self.api_key = api_key
        self.config = config
        self.model = config.get('gemini', {}).get('model', 'gemini-2.0-flash')
        self.max_changes = config.get('optimization', {}).get('actions', {}).get('max_changes_per_iteration', 10)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
    def decide_actions(self, summary_stats: Dict, prompt_template: str) -> List[Dict]:
        """Get optimization decisions from Gemini based on summary statistics"""
        
        # Format the prompt with actual data
        prompt = self._format_prompt(prompt_template, summary_stats)
        
        try:
            # Call Gemini API
            response = self._call_gemini_api(prompt)
            
            # Extract and parse response
            response_text = self._extract_response_text(response)
            
            # Try to extract JSON from response
            actions = self._parse_actions(response_text)
            
            print(f"Registrar suggested {len(actions)} actions")
            return actions
            
        except Exception as e:
            print(f"Error getting registrar decisions: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_exc()
            # Optionally fall back to heuristics or raise error
            if self.config.get('pipeline', {}).get('allow_heuristic_fallback', True):
                print("Falling back to heuristic rules...")
                return self._heuristic_decisions(summary_stats)
            else:
                print("Heuristic fallback disabled. Please fix API issues.")
                raise e
    
    def _call_gemini_api(self, prompt: str) -> Dict:
        """Call the Gemini API with the formatted prompt"""
        
        # Construct the API endpoint
        endpoint = f"{self.base_url}/{self.model}:generateContent"
        
        # Define the response schema for structured output
        response_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["SPLIT", "MERGE", "ADD", "REMOVE"]
                    },
                    "section_id": {
                        "type": "string"
                    },
                    "section_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "course": {
                        "type": "string"
                    },
                    "reason": {
                        "type": "string"
                    }
                },
                "required": ["action", "reason"]
            }
        }
        
        # Prepare the request payload with JSON response format
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": self.config.get('gemini', {}).get('temperature', 0.1),
                "maxOutputTokens": self.config.get('gemini', {}).get('max_tokens', 2000),
                "topP": self.config.get('gemini', {}).get('top_p', 0.1),
                "topK": self.config.get('gemini', {}).get('top_k', 1),
                "responseMimeType": "application/json",
                "responseSchema": response_schema
            }
        }
        
        # Make the API request
        response = requests.post(
            endpoint,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        # Check for errors
        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _extract_response_text(self, response: Dict) -> str:
        """Extract the text content from Gemini's response"""
        
        try:
            # Navigate through the response structure
            candidates = response.get('candidates', [])
            if not candidates:
                raise ValueError("No candidates in response")
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                raise ValueError("No parts in response content")
            
            return parts[0].get('text', '').strip()
            
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Failed to extract text from response: {e}")
            
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
        """Parse JSON actions from Gemini's response"""
        
        try:
            # With responseMimeType set to JSON, Gemini should return valid JSON
            actions = json.loads(response_text)
            
            # Ensure it's a list
            if not isinstance(actions, list):
                print(f"Expected list but got {type(actions)}")
                return []
            
            # Validate actions
            validated_actions = []
            for action in actions:
                if self._validate_action(action):
                    validated_actions.append(action)
                else:
                    print(f"Invalid action skipped: {action}")
                    
            return validated_actions[:self.max_changes]  # Limit to max changes
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from response: {e}")
            print(f"Response text: {response_text[:500]}...")  # Debug output
            return []
        except Exception as e:
            print(f"Unexpected error parsing actions: {e}")
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
        
        # Load percentage-based constraints from config
        min_split_ratio = self.config.get('optimization', {}).get('actions', {}).get('min_split_ratio', 0.40)
        max_merge_ratio = self.config.get('optimization', {}).get('actions', {}).get('max_merge_ratio', 1.30)
        min_enrollment_percentage = self.config.get('optimization', {}).get('actions', {}).get('min_enrollment_percentage', 0.20)
        min_viable_utilization = self.config.get('optimization', {}).get('actions', {}).get('min_viable_utilization', 0.30)
        split_threshold = self.config.get('optimization', {}).get('actions', {}).get('split_threshold', 1.20)
        add_threshold = self.config.get('optimization', {}).get('actions', {}).get('add_threshold', 1.30)
        
        # Group by course for merge opportunities
        course_sections = {}
        for section in problem_sections:
            course = section['course']
            if course not in course_sections:
                course_sections[course] = []
            course_sections[course].append(section)
            
        # Apply smart rules with new constraints - ONE ACTION PER COURSE
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
                # For severely over-capacity (>add_threshold), prefer ADD over SPLIT
                if util_pct > add_threshold:
                    action = {
                        'action': 'ADD',
                        'course': section['course'],
                        'reason': f"Severe overcrowding at {section['utilization']} - need additional section"
                    }
                    actions.append(action)
                    course_actions[course] = action
                # Only split if significantly over capacity (>split_threshold)
                elif util_pct > split_threshold:
                    # Check if split would create viable sections
                    min_enrollment_per_split = capacity * 0.3
                    if enrolled >= min_enrollment_per_split * 2 and capacity >= (capacity * min_split_ratio * 2):
                        action = {
                            'action': 'SPLIT',
                            'section_id': section['section_id'],
                            'reason': f"{section['utilization']} utilization with {enrolled} students"
                        }
                        actions.append(action)
                        course_actions[course] = action
                    else:
                        # Not enough students to split effectively, add new section instead
                        action = {
                            'action': 'ADD',
                            'course': section['course'],
                            'reason': f"Over capacity at {section['utilization']} but too few students to split effectively"
                        }
                        actions.append(action)
                        course_actions[course] = action
                # For 110-120% utilization, accept it as within reasonable range (no action)
                
            # Under capacity - try to merge (<70%)
            elif util_pct < 0.70 and len(actions) < self.max_changes:
                # Look for merge partner
                course = section['course']
                partners = [s for s in course_sections[course] 
                           if s['section_id'] != section['section_id'] 
                           and float(s['utilization'].rstrip('%')) / 100 < 0.70]
                
                if partners:
                    # Find best merge partner (check combined enrollment)
                    for partner in partners:
                        # Skip if trying to merge with self
                        if partner['section_id'] == section['section_id']:
                            continue
                            
                        partner_info = partner.get('enrollment_vs_capacity', '0/0')
                        partner_enrolled = int(partner_info.split('/')[0])
                        combined_enrollment = enrolled + partner_enrolled
                        
                        # Get average capacity between the two sections
                        partner_capacity = int(partner.get('enrollment_vs_capacity', '0/0').split('/')[1])
                        avg_capacity = (capacity + partner_capacity) / 2
                        
                        # Only merge if combined enrollment won't exceed max_merge_ratio of average capacity
                        if combined_enrollment <= avg_capacity * max_merge_ratio:
                            # Check if we haven't already planned to merge these
                            existing_merges = [a for a in actions if a['action'] == 'MERGE']
                            section_ids = {section['section_id'], partner['section_id']}
                            
                            already_planned = any(
                                set(a['section_ids']) & section_ids 
                                for a in existing_merges
                            )
                            
                            if not already_planned:
                                combined_util = combined_enrollment / avg_capacity
                                # Check if merged result would be in target range
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
                elif util_pct < 0.70:  # Changed from 0.65 to catch 66-67% sections
                    # Check if this is the only section for the course
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