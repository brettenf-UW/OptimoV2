#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.environ.get('ANTHROPIC_API_KEY')
print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")

# Test with anthropic library
try:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say test"}]
    )
    print(f"Success! Response: {response.content[0].text}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
