#!/usr/bin/env python3
"""
Test both Anthropic and Gemini APIs with proper environment loading
"""

import os
import sys
import requests
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def test_anthropic():
    """Test Anthropic API"""
    print(f"\n{Colors.BLUE}Testing Anthropic API{Colors.END}")
    print("="*40)
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print_error("ANTHROPIC_API_KEY not found in environment")
        return False
    
    print_info(f"API key loaded: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        import anthropic
        
        # Create client
        client = anthropic.Anthropic(api_key=api_key)
        print_success("Client created successfully")
        
        # Test with correct model name
        print_info("Testing with claude-3-5-sonnet-20241022...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'OptimoV2 API test successful!' and nothing else."
            }]
        )
        
        result = response.content[0].text
        print_success(f"API call successful! Response: {result}")
        return True
        
    except Exception as e:
        print_error(f"Error: {type(e).__name__}: {str(e)}")
        
        # Try with different model names
        if "model_not_found" in str(e).lower() or "does not exist" in str(e).lower():
            print_info("Trying alternative model names...")
            
            alternative_models = [
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-opus-20240229"
            ]
            
            for model in alternative_models:
                try:
                    print_info(f"Testing {model}...")
                    response = client.messages.create(
                        model=model,
                        max_tokens=100,
                        messages=[{
                            "role": "user",
                            "content": "Say 'OptimoV2 API test successful!' and nothing else."
                        }]
                    )
                    result = response.content[0].text
                    print_success(f"Success with {model}! Response: {result}")
                    print_info(f"Update config to use model: {model}")
                    return True
                except Exception as e2:
                    print_error(f"{model} failed: {str(e2)}")
                    
        return False

def test_gemini():
    """Test Gemini API"""
    print(f"\n{Colors.BLUE}Testing Gemini API{Colors.END}")
    print("="*40)
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print_error("GEMINI_API_KEY not found in environment")
        return False
    
    print_info(f"API key loaded: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Say 'OptimoV2 API test successful!' and nothing else."
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 100
            }
        }
        
        response = requests.post(
            endpoint,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            print_success(f"API call successful! Response: {text}")
            return True
        else:
            print_error(f"API error: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {type(e).__name__}: {str(e)}")
        return False

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}OptimoV2 API Testing{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # Check environment
    print(f"\n{Colors.BLUE}Environment Check{Colors.END}")
    print("="*40)
    
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if anthropic_key:
        print_success(f"ANTHROPIC_API_KEY found (length: {len(anthropic_key)})")
    else:
        print_error("ANTHROPIC_API_KEY not found")
        
    if gemini_key:
        print_success(f"GEMINI_API_KEY found (length: {len(gemini_key)})")
    else:
        print_error("GEMINI_API_KEY not found")
    
    # Test APIs
    anthropic_works = test_anthropic()
    gemini_works = test_gemini()
    
    # Summary
    print(f"\n{Colors.BLUE}Summary{Colors.END}")
    print("="*40)
    
    if anthropic_works:
        print_success("Anthropic API is working!")
        print_info("To use Anthropic, run: python scripts/run_pipeline.py --ai-provider claude")
    else:
        print_error("Anthropic API is not working")
        
    if gemini_works:
        print_success("Gemini API is working!")
        print_info("To use Gemini, run: python scripts/run_pipeline.py --ai-provider gemini")
    else:
        print_error("Gemini API is not working")
    
    if not anthropic_works and not gemini_works:
        print_error("No APIs are working! Please check your API keys.")
    
    # Show current config
    import yaml
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    current_provider = config.get('pipeline', {}).get('ai_provider', 'claude')
    print(f"\n{Colors.BLUE}Current Configuration{Colors.END}")
    print("="*40)
    print_info(f"AI Provider: {current_provider}")
    print_info(f"Anthropic Model: {config.get('registrar', {}).get('model', 'Not set')}")
    print_info(f"Gemini Model: {config.get('gemini', {}).get('model', 'Not set')}")

if __name__ == "__main__":
    main()