#!/usr/bin/env python3
"""Simple Claude API test using exact documentation format"""

import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

try:
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=100,
        temperature=0.1,
        messages=[
            {"role": "user", "content": "Say 'Hello' and nothing else"}
        ]
    )
    print("Success! Response:", message.content[0].text)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    print("\nMake sure your ANTHROPIC_API_KEY in .env is valid")