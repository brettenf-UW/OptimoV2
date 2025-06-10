#!/bin/bash

# Script to enable CORS on the existing API Gateway
# This script adds OPTIONS methods and proper CORS headers to all endpoints

API_ID="3dbrbfl8f3"
REGION="us-west-2"
ORIGIN="https://brettenf-uw.github.io"

echo "Enabling CORS for API Gateway: $API_ID"

# Function to get resource ID by path
get_resource_id() {
    local path=$1
    aws apigateway get-resources \
        --rest-api-id $API_ID \
        --region $REGION \
        --query "items[?path=='$path'].id" \
        --output text
}

# Function to enable CORS for a resource
enable_cors_for_resource() {
    local resource_id=$1
    local resource_path=$2
    
    echo "Enabling CORS for resource: $resource_path (ID: $resource_id)"
    
    # Check if OPTIONS method exists
    OPTIONS_EXISTS=$(aws apigateway get-method \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --region $REGION 2>&1 | grep -c "NotFoundException")
    
    if [ "$OPTIONS_EXISTS" -eq "1" ]; then
        echo "Adding OPTIONS method for $resource_path..."
        
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
            --response-parameters '{
                "method.response.header.Access-Control-Allow-Origin": true,
                "method.response.header.Access-Control-Allow-Methods": true,
                "method.response.header.Access-Control-Allow-Headers": true
            }' \
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
    else
        echo "OPTIONS method already exists for $resource_path"
    fi
}

# Get resource IDs
echo "Getting resource IDs..."
UPLOAD_ID=$(get_resource_id "/upload")
JOBS_ID=$(get_resource_id "/jobs")
JOBS_STATUS_ID=$(get_resource_id "/jobs/{jobId}/status")
JOBS_RESULTS_ID=$(get_resource_id "/jobs/{jobId}/results")
JOBS_CANCEL_ID=$(get_resource_id "/jobs/{jobId}/cancel")

# Enable CORS for each endpoint
enable_cors_for_resource "$UPLOAD_ID" "/upload"
enable_cors_for_resource "$JOBS_ID" "/jobs"
enable_cors_for_resource "$JOBS_STATUS_ID" "/jobs/{jobId}/status"
enable_cors_for_resource "$JOBS_RESULTS_ID" "/jobs/{jobId}/results"
enable_cors_for_resource "$JOBS_CANCEL_ID" "/jobs/{jobId}/cancel"

# Deploy the API
echo "Deploying API to prod stage..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Enable CORS" \
    --region $REGION

echo "CORS configuration complete!"
echo "API URL: https://$API_ID.execute-api.$REGION.amazonaws.com/prod"

# Test CORS with curl
echo -e "\nTesting CORS preflight request..."
curl -X OPTIONS \
    -H "Origin: $ORIGIN" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -v "https://$API_ID.execute-api.$REGION.amazonaws.com/prod/jobs" 2>&1 | grep -i "access-control"