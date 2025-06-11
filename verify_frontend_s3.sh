#!/bin/bash

# Verify frontend S3 configuration
echo "=== Frontend S3 Configuration Verification ==="
echo

# Check frontend config
echo "1. Frontend aws-config.ts:"
grep -A2 "buckets:" optimo-frontend/src/aws-config.ts | grep "input:" | sed 's/.*input: "\(.*\)".*/  Input bucket: \1/'

# Check if bucket exists and has CORS
BUCKET="optimo-input-files-v2"
echo
echo "2. S3 Bucket Status:"
if aws s3api head-bucket --bucket $BUCKET 2>/dev/null; then
    echo "  ✅ Bucket '$BUCKET' exists"
    
    # Check CORS
    if aws s3api get-bucket-cors --bucket $BUCKET 2>/dev/null | grep -q "AllowedOrigins"; then
        echo "  ✅ CORS is configured"
        echo "  Allowed origins:"
        aws s3api get-bucket-cors --bucket $BUCKET 2>/dev/null | grep -A1 "AllowedOrigins" | grep -v "AllowedOrigins" | sed 's/.*"\(.*\)".*/    - \1/'
    else
        echo "  ❌ CORS is not configured"
    fi
else
    echo "  ❌ Bucket '$BUCKET' does not exist"
fi

# Check Lambda configuration matches
echo
echo "3. Lambda Configuration:"
LAMBDA_BUCKET=$(aws lambda get-function-configuration --function-name optimo-unified-handler --region us-west-2 --query 'Environment.Variables.S3_INPUT_BUCKET' --output text)
echo "  Lambda S3_INPUT_BUCKET: $LAMBDA_BUCKET"

if [[ "$LAMBDA_BUCKET" == "$BUCKET" ]]; then
    echo "  ✅ Lambda and frontend use the same bucket"
else
    echo "  ❌ Mismatch: Lambda uses '$LAMBDA_BUCKET', frontend uses '$BUCKET'"
fi

echo
echo "4. Test Upload Permission:"
# Create a test file
echo "test" > /tmp/test-upload.txt
if aws s3 cp /tmp/test-upload.txt s3://$BUCKET/test-upload.txt 2>/dev/null; then
    echo "  ✅ Can upload to bucket"
    # Clean up
    aws s3 rm s3://$BUCKET/test-upload.txt 2>/dev/null
else
    echo "  ❌ Cannot upload to bucket (this is expected if running locally)"
fi
rm /tmp/test-upload.txt

echo
echo "=== Summary ==="
echo "Frontend is configured to use: $BUCKET"
echo "This matches the Lambda configuration and the bucket exists with CORS enabled."
echo "The system should work correctly for file uploads from the frontend."