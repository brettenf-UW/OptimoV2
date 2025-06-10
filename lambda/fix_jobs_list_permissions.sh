#!/bin/bash

# Script to fix permissions for the jobs list Lambda function

REGION="us-west-2"
ACCOUNT_ID="529088253685"  # Replace with your AWS account ID if different

echo "Fixing permissions for Jobs List Lambda function..."

# First, let's get the Lambda function's execution role
FUNCTION_NAME="optimo-jobs-list"
echo "Getting execution role for Lambda function: $FUNCTION_NAME"

ROLE_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.Role' \
    --output text 2>/dev/null)

if [ -z "$ROLE_ARN" ]; then
    echo "Error: Could not find Lambda function $FUNCTION_NAME"
    echo "Trying alternative function names..."
    
    # Try alternative names
    for alt_name in "optimo-job-list" "optimo-list-jobs" "jobs-list-handler"; do
        ROLE_ARN=$(aws lambda get-function \
            --function-name $alt_name \
            --region $REGION \
            --query 'Configuration.Role' \
            --output text 2>/dev/null)
        
        if [ ! -z "$ROLE_ARN" ]; then
            FUNCTION_NAME=$alt_name
            echo "Found function with name: $FUNCTION_NAME"
            break
        fi
    done
fi

if [ -z "$ROLE_ARN" ]; then
    echo "Error: Could not find the Lambda function. Please specify the correct function name."
    exit 1
fi

ROLE_NAME=$(echo $ROLE_ARN | awk -F'/' '{print $NF}')
echo "Execution role: $ROLE_NAME"

# Create a policy document for DynamoDB access
cat > /tmp/dynamodb-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:Scan",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/optimo-jobs",
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/optimo-jobs/*"
            ]
        }
    ]
}
EOF

echo "Creating/updating DynamoDB access policy..."

# Create or update the inline policy
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name OptimoDynamoDBAccess \
    --policy-document file:///tmp/dynamodb-policy.json \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Successfully added DynamoDB permissions to role: $ROLE_NAME"
else
    echo "❌ Failed to add DynamoDB permissions"
    exit 1
fi

# Also ensure the Lambda function has the correct environment variable
echo "Checking environment variables..."

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables={DYNAMODB_TABLE=optimo-jobs} \
    --region $REGION > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Environment variable DYNAMODB_TABLE set to 'optimo-jobs'"
else
    echo "❌ Failed to update environment variables"
fi

# Clean up
rm /tmp/dynamodb-policy.json

echo ""
echo "Permissions fixed! Testing the function..."

# Test the Lambda function
echo "Invoking Lambda function to test..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"httpMethod": "GET", "path": "/jobs"}' \
    --region $REGION \
    /tmp/lambda-response.json

if [ -f /tmp/lambda-response.json ]; then
    echo "Lambda response:"
    cat /tmp/lambda-response.json | python -m json.tool
    rm /tmp/lambda-response.json
fi

echo ""
echo "Next steps:"
echo "1. Test the API endpoint: curl https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod/jobs"
echo "2. Check CloudWatch logs if there are still errors"
echo "3. Verify in the AWS Console that the permissions are correctly applied"