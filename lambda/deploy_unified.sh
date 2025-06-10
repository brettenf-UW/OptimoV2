#!/bin/bash

# Deploy unified Lambda handler
echo "Deploying unified Lambda handler..."

# Create deployment package
echo "Creating deployment package..."
cp unified_handler.py package/
cd package

# Create zip file
zip -r ../unified_handler.zip . -x "*.pyc" -x "*__pycache__*"
cd ..

# Update Lambda function (or create if doesn't exist)
echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name optimo-unified-handler \
    --zip-file fileb://unified_handler.zip \
    --region us-west-2

# If the function doesn't exist, create it
if [ $? -ne 0 ]; then
    echo "Function doesn't exist, creating it..."
    aws lambda create-function \
        --function-name optimo-unified-handler \
        --runtime python3.9 \
        --role arn:aws:iam::529088253685:role/optimo-lambda-role \
        --handler unified_handler.lambda_handler \
        --zip-file fileb://unified_handler.zip \
        --timeout 300 \
        --memory-size 1024 \
        --environment Variables="{
            DYNAMODB_TABLE=optimo-jobs,
            S3_INPUT_BUCKET=optimo-input-files,
            S3_OUTPUT_BUCKET=optimo-output-files,
            JOB_QUEUE=optimo-job-queue,
            JOB_DEFINITION=optimo-job-updated
        }" \
        --region us-west-2
fi

# Update Lambda configuration
echo "Updating Lambda configuration..."
aws lambda update-function-configuration \
    --function-name optimo-unified-handler \
    --timeout 300 \
    --memory-size 1024 \
    --region us-west-2

# Clean up
rm unified_handler.zip

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Update API Gateway to route all endpoints to optimo-unified-handler"
echo "2. Test the endpoints"
echo "3. Remove old Lambda functions once verified"