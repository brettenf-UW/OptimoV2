#!/usr/bin/env python3
"""
Direct test of Anthropic API without dependencies
Manually loads .env file
"""

import os
import sys
from pathlib import Path

# Manually load .env file
def load_env():
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables
load_env()

# Get API key
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found!")
    sys.exit(1)

print(f"API Key loaded: {api_key[:20]}...{api_key[-10:]}")
print(f"Key length: {len(api_key)}")

# Create a simple test request using urllib
import urllib.request
import urllib.error
import json

url = "https://api.anthropic.com/v1/messages"

headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

data = {
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 100,
    "messages": [{
        "role": "user",
        "content": "Say 'OptimoV2 test successful!' and nothing else."
    }]
}

try:
    # Create request
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    
    # Make request
    print("\nMaking API request...")
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode('utf-8'))
    
    # Extract text
    if 'content' in result and len(result['content']) > 0:
        text = result['content'][0].get('text', '')
        print(f"✓ SUCCESS! Response: {text}")
        print("\nAnthropic API is working correctly!")
        print("\nTo use with OptimoV2:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run: python scripts/run_pipeline.py --ai-provider claude")
    else:
        print("Unexpected response format:", result)
        
except urllib.error.HTTPError as e:
    print(f"✗ HTTP Error {e.code}: {e.reason}")
    error_body = e.read().decode('utf-8')
    print(f"Error details: {error_body}")
    
    if e.code == 401:
        print("\nAuthentication failed - API key may be invalid")
    elif e.code == 404:
        print("\nModel not found - trying with claude-3-haiku-20240307")
        # Try with a different model
        data['model'] = 'claude-3-haiku-20240307'
        try:
            req2 = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            response2 = urllib.request.urlopen(req2)
            result2 = json.loads(response2.read().decode('utf-8'))
            text = result2['content'][0].get('text', '')
            print(f"✓ SUCCESS with claude-3-haiku! Response: {text}")
        except Exception as e2:
            print(f"Also failed with claude-3-haiku: {str(e2)}")
            
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")

# Also test if we can import anthropic (if installed)
print("\nChecking if anthropic library is installed...")
try:
    import anthropic
    print("✓ anthropic library is installed")
    print(f"  Version: {anthropic.__version__ if hasattr(anthropic, '__version__') else 'Unknown'}")
except ImportError:
    print("✗ anthropic library not installed")
    print("  Run: pip install anthropic")