#!/bin/bash

echo "=== Fixing Batch Role S3 Permissions ==="

REGION="us-west-2"
ACCOUNT_ID="529088253685"
BATCH_ROLE="optimo-batch-role"

# Create policy for Batch role to access new S3 bucket
cat > /tmp/batch-s3-policy.json << EOF
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

echo "Creating S3 access policy for Batch role..."

# Check if policy exists
POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/optimo-batch-s3-v2-policy"

if aws iam get-policy --policy-arn $POLICY_ARN 2>/dev/null; then
    echo "Policy exists, creating new version..."
    aws iam create-policy-version \
        --policy-arn $POLICY_ARN \
        --policy-document file:///tmp/batch-s3-policy.json \
        --set-as-default
else
    echo "Creating new policy..."
    aws iam create-policy \
        --policy-name optimo-batch-s3-v2-policy \
        --policy-document file:///tmp/batch-s3-policy.json
fi

# Attach policy to Batch role
echo "Attaching policy to Batch role..."
aws iam attach-role-policy \
    --role-name $BATCH_ROLE \
    --policy-arn $POLICY_ARN

echo
echo "✅ S3 permissions updated for Batch role!"
echo
echo "The Batch jobs now have permissions to:"
echo "- List and read from optimo-input-files-v2"
echo "- Write to optimo-output-files"
echo
echo "Submit your job again - it should work now!"

# Clean up
rm /tmp/batch-s3-policy.json