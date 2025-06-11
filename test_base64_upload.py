#!/usr/bin/env python3
"""
Test script for base64 file upload functionality
"""

import requests
import base64
import json

# API endpoint
API_URL = "https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/upload"

# Test file content
test_csv_content = """student_id,name,grade
1,John Doe,10
2,Jane Smith,11
3,Bob Johnson,10"""

# Encode to base64
file_content_base64 = base64.b64encode(test_csv_content.encode()).decode()

# Prepare request
payload = {
    "filename": "test_file.csv",
    "fileContent": file_content_base64
}

# Headers
headers = {
    "Content-Type": "application/json"
}

print("Testing base64 file upload...")
print(f"API URL: {API_URL}")
print(f"Payload size: {len(json.dumps(payload))} bytes")

try:
    # Send request
    response = requests.post(API_URL, json=payload, headers=headers)
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess! Response data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\nError! Response:")
        print(response.text)
        
except Exception as e:
    print(f"\nException occurred: {e}")