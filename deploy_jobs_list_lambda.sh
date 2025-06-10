#!/bin/bash

# Create zip file for the Lambda function
echo "Creating deployment package..."
zip lambda_jobs_list.zip lambda_jobs_list.py

# Create the Lambda function
echo "Creating Lambda function..."
aws lambda create-function \
    --function-name optimo-jobs-list \
    --runtime python3.9 \
    --handler lambda_jobs_list.lambda_handler \
    --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/optimo-lambda-role \
    --zip-file fileb://lambda_jobs_list.zip \
    --environment "Variables={DYNAMODB_TABLE=optimo-jobs}" \
    --timeout 10 \
    --memory-size 128 \
    --region us-west-2

# Get the REST API ID for optimo-api
echo "Getting API Gateway ID..."
API_ID=$(aws apigateway get-rest-apis --region us-west-2 --query "items[?name=='optimo-api'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "Error: Could not find API Gateway 'optimo-api'"
    exit 1
fi

echo "API Gateway ID: $API_ID"

# Get the root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region us-west-2 --query "items[?path=='/'].id" --output text)

# Check if /jobs resource already exists
JOBS_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region us-west-2 --query "items[?path=='/jobs'].id" --output text)

if [ -z "$JOBS_ID" ]; then
    echo "Creating /jobs resource..."
    JOBS_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ROOT_ID \
        --path-part jobs \
        --region us-west-2 \
        --query 'id' \
        --output text)
fi

echo "Jobs resource ID: $JOBS_ID"

# Create GET method for /jobs
echo "Creating GET method..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $JOBS_ID \
    --http-method GET \
    --authorization-type NONE \
    --region us-west-2

# Create Lambda integration
echo "Creating Lambda integration..."
LAMBDA_ARN="arn:aws:lambda:us-west-2:$(aws sts get-caller-identity --query Account --output text):function:optimo-jobs-list"

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $JOBS_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-west-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region us-west-2

# Add method response
echo "Adding method response..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $JOBS_ID \
    --http-method GET \
    --status-code 200 \
    --response-models '{"application/json": "Empty"}' \
    --region us-west-2

# Add integration response
echo "Adding integration response..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $JOBS_ID \
    --http-method GET \
    --status-code 200 \
    --region us-west-2

# Grant API Gateway permission to invoke Lambda
echo "Adding Lambda permission..."
aws lambda add-permission \
    --function-name optimo-jobs-list \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-west-2:$(aws sts get-caller-identity --query Account --output text):${API_ID}/*/*" \
    --region us-west-2

# Deploy the API
echo "Deploying API..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region us-west-2

echo "Done! The GET /jobs endpoint should now be available."
echo "API Endpoint: https://${API_ID}.execute-api.us-west-2.amazonaws.com/prod/jobs"

# Clean up
rm lambda_jobs_list.zip