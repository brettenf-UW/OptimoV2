#!/bin/bash

# This script enables CORS on API Gateway resources

# Set variables
REGION="us-west-2"
API_ID="ppwbzsy1bh"
ORIGIN="https://brettenf-uw.github.io"

# Function to enable CORS on a resource
enable_cors() {
  local resource_id=$1
  local http_method=$2
  
  echo "Enabling CORS for resource $resource_id, method $http_method..."
  
  # Update the method response to include CORS headers
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --status-code 200 \
    --response-parameters "{
      \"method.response.header.Access-Control-Allow-Origin\": true,
      \"method.response.header.Access-Control-Allow-Methods\": true,
      \"method.response.header.Access-Control-Allow-Headers\": true
    }" \
    --region $REGION
  
  # Update the integration response to set CORS headers
  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --status-code 200 \
    --response-parameters "{
      \"method.response.header.Access-Control-Allow-Origin\": \"'$ORIGIN'\",
      \"method.response.header.Access-Control-Allow-Methods\": \"'GET,POST,OPTIONS'\",
      \"method.response.header.Access-Control-Allow-Headers\": \"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\"
    }" \
    --region $REGION
}

# Function to add OPTIONS method to a resource
add_options_method() {
  local resource_id=$1
  
  echo "Adding OPTIONS method to resource $resource_id..."
  
  # Add OPTIONS method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION
  
  # Add mock integration
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION
  
  # Add method response
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
  
  # Add integration response
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
# /jobs - POST
enable_cors "hyp49y" "POST"
enable_cors "hyp49y" "GET"
enable_cors "hyp49y" "OPTIONS"

# /upload - POST
enable_cors "jbyew8" "POST"
enable_cors "jbyew8" "OPTIONS"

# /jobs/{jobId}/status - GET
enable_cors "zdl7c1" "GET"
enable_cors "zdl7c1" "OPTIONS"

# /jobs/{jobId}/results - GET
enable_cors "v5q1d6" "GET"
enable_cors "v5q1d6" "OPTIONS"

# /jobs/{jobId}/cancel - POST
enable_cors "f4wanb" "POST"
enable_cors "f4wanb" "OPTIONS"

# Create new API Gateway deployment
echo "Creating new API Gateway deployment..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION

echo "CORS configuration complete!"
