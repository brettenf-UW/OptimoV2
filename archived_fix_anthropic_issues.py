#!/usr/bin/env python3
"""
Fix Anthropic API issues in OptimoV2
"""

import os
import sys
import yaml
from pathlib import Path

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

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}OptimoV2 Anthropic API Fix Script{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 1. Check and fix config file
    print(f"\n{Colors.BLUE}1. Checking configuration file{Colors.END}")
    config_path = Path("config/settings.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    current_model = config.get('registrar', {}).get('model', '')
    print(f"Current model: {current_model}")
    
    # List of valid Anthropic models
    valid_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]
    
    if current_model not in valid_models:
        print_warning(f"Current model '{current_model}' may not be valid")
        print_info("Valid Anthropic models:")
        for model in valid_models:
            print(f"  - {model}")
        
        # Suggest claude-3-sonnet as it's a good balance
        print_info("Updating to claude-3-sonnet-20240229 (recommended)")
        config['registrar']['model'] = 'claude-3-sonnet-20240229'
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print_success("Configuration updated")
    else:
        print_success("Model configuration is valid")
    
    # 2. Check .env file
    print(f"\n{Colors.BLUE}2. Checking .env file{Colors.END}")
    env_path = Path(".env")
    
    if not env_path.exists():
        print_error(".env file not found!")
        return
    
    # Load and check API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if anthropic_key:
        print_success(f"ANTHROPIC_API_KEY loaded (length: {len(anthropic_key)})")
        if anthropic_key.startswith('sk-ant-'):
            print_success("API key format looks correct")
        else:
            print_warning("API key doesn't start with expected 'sk-ant-' prefix")
    else:
        print_error("ANTHROPIC_API_KEY not found in environment")
    
    if gemini_key:
        print_success(f"GEMINI_API_KEY loaded (length: {len(gemini_key)})")
    
    # 3. Test Anthropic API
    print(f"\n{Colors.BLUE}3. Testing Anthropic API{Colors.END}")
    
    if anthropic_key:
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=anthropic_key)
            print_info("Testing API connection...")
            
            # Test with the configured model
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            model = config.get('registrar', {}).get('model', 'claude-3-sonnet-20240229')
            
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=50,
                    messages=[{
                        "role": "user",
                        "content": "Say 'API test successful' and nothing else."
                    }]
                )
                
                result = response.content[0].text.strip()
                print_success(f"API test passed! Response: {result}")
                print_success(f"Model {model} is working correctly")
                
            except Exception as e:
                print_error(f"API test failed: {str(e)}")
                
                # If model not found, try other models
                if "model" in str(e).lower():
                    print_info("Trying other models...")
                    for test_model in ["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1"]:
                        try:
                            response = client.messages.create(
                                model=test_model,
                                max_tokens=50,
                                messages=[{
                                    "role": "user",
                                    "content": "Say 'test' and nothing else."
                                }]
                            )
                            print_success(f"Model {test_model} works!")
                            
                            # Update config
                            config['registrar']['model'] = test_model
                            with open(config_path, 'w') as f:
                                yaml.dump(config, f, default_flow_style=False)
                            print_success(f"Updated config to use {test_model}")
                            break
                            
                        except:
                            print_error(f"Model {test_model} failed")
                            
        except ImportError:
            print_error("anthropic library not installed")
            print_info("Run: pip install -r requirements.txt")
    else:
        print_error("Cannot test API without API key")
    
    # 4. Summary and recommendations
    print(f"\n{Colors.BLUE}Summary and Recommendations{Colors.END}")
    print("="*60)
    
    print("\nTo use Anthropic API with OptimoV2:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Set AI provider: python scripts/run_pipeline.py --ai-provider claude")
    print("3. Or change default in config/settings.yaml:")
    print("   pipeline:")
    print("     ai_provider: claude")
    
    print("\nTo generate test data and run:")
    print("python scripts/run_pipeline.py --generate-test-data small --ai-provider claude")
    
    print("\nCurrent configuration:")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"  AI Provider: {config.get('pipeline', {}).get('ai_provider', 'Not set')}")
    print(f"  Anthropic Model: {config.get('registrar', {}).get('model', 'Not set')}")
    print(f"  Gemini Model: {config.get('gemini', {}).get('model', 'Not set')}")

if __name__ == "__main__":
    main()