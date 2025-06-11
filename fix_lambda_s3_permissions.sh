#!/bin/bash

# Fix Lambda S3 permissions for the new bucket
echo "=== Fixing Lambda S3 Permissions ==="

REGION="us-west-2"
LAMBDA_ROLE="optimo-lambda-role"
ACCOUNT_ID="529088253685"

# Create a new policy for the v2 bucket
cat > /tmp/lambda-s3-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::optimo-input-files-v2",
                "arn:aws:s3:::optimo-input-files-v2/*",
                "arn:aws:s3:::optimo-output-files",
                "arn:aws:s3:::optimo-output-files/*"
            ]
        }
    ]
}
EOF

echo "Creating/updating S3 access policy..."

# Check if policy exists
POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/optimo-lambda-s3-v2-policy"

if aws iam get-policy --policy-arn $POLICY_ARN 2>/dev/null; then
    echo "Policy exists, creating new version..."
    aws iam create-policy-version \
        --policy-arn $POLICY_ARN \
        --policy-document file:///tmp/lambda-s3-policy.json \
        --set-as-default
else
    echo "Creating new policy..."
    aws iam create-policy \
        --policy-name optimo-lambda-s3-v2-policy \
        --policy-document file:///tmp/lambda-s3-policy.json
fi

# Attach the policy to the Lambda role
echo "Attaching policy to Lambda role..."
aws iam attach-role-policy \
    --role-name $LAMBDA_ROLE \
    --policy-arn $POLICY_ARN

echo
echo "✅ S3 permissions updated!"
echo
echo "The Lambda function now has permissions to:"
echo "- Read/Write to optimo-input-files-v2"
echo "- Read/Write to optimo-output-files"
echo
echo "Try uploading files again - it should work now!"

# Clean up
rm /tmp/lambda-s3-policy.json