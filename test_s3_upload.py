#!/usr/bin/env python3
"""
Quick S3 presigned URL test script
"""
import boto3
import requests
import sys
import os

# Test different presigned URL configurations
def test_presigned_url_configs():
    s3 = boto3.client('s3', region_name='us-west-2')
    bucket = 'optimo-input-files'
    test_key = 'uploads/test/test.csv'
    test_content = b'test,data\n1,2\n'
    
    print("Testing different presigned URL configurations...\n")
    
    # Test 1: Basic presigned URL (no Content-Type)
    print("Test 1: Basic presigned URL (no Content-Type)")
    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket, 'Key': test_key},
            ExpiresIn=300
        )
        response = requests.put(url, data=test_content)
        print(f"Result: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 2: With Content-Type in params and header
    print("Test 2: With Content-Type in params and header")
    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket, 
                'Key': test_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=300
        )
        response = requests.put(url, data=test_content, headers={'Content-Type': 'text/csv'})
        print(f"Result: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 3: Direct S3 upload (to verify permissions)
    print("Test 3: Direct S3 upload (to verify IAM permissions)")
    try:
        s3.put_object(Bucket=bucket, Key=test_key, Body=test_content)
        print("Result: SUCCESS - Direct upload works")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 4: Generate URL without security token
    print("Test 4: Using IAM user credentials instead of role")
    print("(This would require IAM user access keys)")
    
if __name__ == "__main__":
    test_presigned_url_configs()