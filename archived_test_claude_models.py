#!/usr/bin/env python3
"""Test Claude API models"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in environment")
    sys.exit(1)

print(f"API Key found: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else 'TOO_SHORT'}")

# Models to test based on documentation
models_to_test = [
    "claude-3-5-sonnet-20241022",  # Current model
    "claude-sonnet-4-20250514",     # From docs example
    "claude-opus-4-20250514",       # From docs example
    "claude-3.5-sonnet",            # Possible alias
]

# Try to import and use anthropic
try:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    
    print("\nTesting different model names:")
    print("-" * 40)
    
    for model in models_to_test:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": "Say 'OK' and nothing else."
                }]
            )
            print(f"✓ {model}: WORKS - {response.content[0].text.strip()}")
        except Exception as e:
            error_msg = str(e)
            if "model_not_found" in error_msg or "does not exist" in error_msg:
                print(f"✗ {model}: Model not found")
            elif "authentication" in error_msg.lower():
                print(f"✗ {model}: Authentication error - check API key")
                break  # No point testing other models if auth fails
            else:
                print(f"✗ {model}: {type(e).__name__}: {error_msg[:50]}...")
    
except ImportError:
    print("Error: anthropic package not installed")
    print("Run: pip install anthropic")