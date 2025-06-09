#!/usr/bin/env python3
"""Test Claude API connection directly"""

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

# Try to import and use anthropic
try:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    
    # Try a simple API call
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Say 'API connection successful' and nothing else."
        }]
    )
    
    print(f"✓ API Response: {response.content[0].text}")
    print("\nYour Claude API key is working correctly!")
    
except Exception as e:
    print(f"\n✗ API Error: {type(e).__name__}: {e}")
    print("\nPossible issues:")
    print("1. Invalid API key - check if it starts with 'sk-ant-api03-'")
    print("2. Expired API key - generate a new one at https://console.anthropic.com/account/keys")
    print("3. No API access - ensure your account has API access enabled")
    print("4. Rate limited - check your usage at https://console.anthropic.com/usage")