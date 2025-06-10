#!/bin/bash

# This script enables CORS on API Gateway by creating a new API with proper CORS configuration

# Set variables
REGION="us-west-2"
ORIGIN="https://brettenf-uw.github.io"

# Create a new API Gateway with proper CORS configuration
echo "Creating a new API Gateway with proper CORS configuration..."

# Step 1: Create a new REST API
API_ID=$(aws apigateway create-rest-api \
  --name "optimo-api-cors" \
  --description "API for OptimoV2 with CORS enabled" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created new API Gateway with ID: $API_ID"

# Step 2: Get the root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query "items[0].id" \
  --output text)

echo "Root resource ID: $ROOT_ID"

# Step 3: Create resources and methods with CORS enabled

# Create /upload resource
UPLOAD_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "upload" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /upload resource with ID: $UPLOAD_ID"

# Create /jobs resource
JOBS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "jobs" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /jobs resource with ID: $JOBS_ID"

# Create /jobs/{jobId} resource
JOB_ID_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOBS_ID \
  --path-part "{jobId}" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /jobs/{jobId} resource with ID: $JOB_ID_RESOURCE"

# Create /jobs/{jobId}/status resource
STATUS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOB_ID_RESOURCE \
  --path-part "status" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /jobs/{jobId}/status resource with ID: $STATUS_ID"

# Create /jobs/{jobId}/results resource
RESULTS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOB_ID_RESOURCE \
  --path-part "results" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /jobs/{jobId}/results resource with ID: $RESULTS_ID"

# Create /jobs/{jobId}/cancel resource
CANCEL_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $JOB_ID_RESOURCE \
  --path-part "cancel" \
  --region $REGION \
  --query "id" \
  --output text)

echo "Created /jobs/{jobId}/cancel resource with ID: $CANCEL_ID"

# Function to enable CORS for a resource
enable_cors() {
  local resource_id=$1
  local lambda_function=$2
  local http_method=$3
  
  echo "Enabling CORS for resource $resource_id, method $http_method, function $lambda_function..."
  
  # Add method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --authorization-type NONE \
    --region $REGION
  
  # Add Lambda integration
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:529088253685:function:$lambda_function/invocations" \
    --region $REGION
  
  # Add method response
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --status-code 200 \
    --response-parameters "{
      \"method.response.header.Access-Control-Allow-Origin\": true
    }" \
    --region $REGION
  
  # Add OPTIONS method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION
  
  # Add mock integration for OPTIONS
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION
  
  # Add method response for OPTIONS
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters "{
      \"method.response.header.Access-Control-Allow-Origin\": true,
      \"method.response.header.Access-Control-Allow-Methods\": true,
      \"method.response.header.Access-Control-Allow-Headers\": true
    }" \
    --region $REGION
  
  # Add integration response for OPTIONS
  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters "{
      \"method.response.header.Access-Control-Allow-Origin\": \"'$ORIGIN'\",
      \"method.response.header.Access-Control-Allow-Methods\": \"'GET,POST,OPTIONS'\",
      \"method.response.header.Access-Control-Allow-Headers\": \"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\"
    }" \
    --region $REGION
}

# Enable CORS for each resource and method
enable_cors "$UPLOAD_ID" "optimo-upload-handler" "POST"
enable_cors "$JOBS_ID" "optimo-job-submission" "POST"
enable_cors "$JOBS_ID" "optimo-job-submission" "GET"
enable_cors "$STATUS_ID" "optimo-job-status" "GET"
enable_cors "$RESULTS_ID" "optimo-results-handler" "GET"
enable_cors "$CANCEL_ID" "optimo-job-submission" "POST"

# Step 4: Add Lambda permissions
echo "Adding Lambda permissions..."

aws lambda add-permission \
  --function-name optimo-upload-handler \
  --statement-id apigateway-$API_ID-upload \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/POST/upload" \
  --region $REGION

aws lambda add-permission \
  --function-name optimo-job-submission \
  --statement-id apigateway-$API_ID-jobs-post \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/POST/jobs" \
  --region $REGION

aws lambda add-permission \
  --function-name optimo-job-submission \
  --statement-id apigateway-$API_ID-jobs-get \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/GET/jobs" \
  --region $REGION

aws lambda add-permission \
  --function-name optimo-job-status \
  --statement-id apigateway-$API_ID-status \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/GET/jobs/*/status" \
  --region $REGION

aws lambda add-permission \
  --function-name optimo-results-handler \
  --statement-id apigateway-$API_ID-results \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/GET/jobs/*/results" \
  --region $REGION

aws lambda add-permission \
  --function-name optimo-job-submission \
  --statement-id apigateway-$API_ID-cancel \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/POST/jobs/*/cancel" \
  --region $REGION

# Step 5: Create deployment
echo "Creating deployment..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION

# Step 6: Update config file with new API URL
NEW_API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
echo "New API URL: $NEW_API_URL"

echo "Updating config file..."
sed -i "s|https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod|$NEW_API_URL|g" /mnt/c/dev/OptimoV2/config/aws_config.json

echo "CORS configuration complete!"
echo "Please update your frontend to use the new API URL: $NEW_API_URL"
