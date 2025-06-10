#!/bin/bash

# Update API Gateway routes to use unified handler
API_ID="3dbrbfl8f3"
REGION="us-west-2"
LAMBDA_ARN="arn:aws:lambda:us-west-2:529088253685:function:optimo-unified-handler"

echo "Updating API Gateway routes to use unified Lambda handler..."

# Helper function to update or create integration
update_integration() {
    local resource_id=$1
    local http_method=$2
    
    echo "Updating $http_method integration for resource $resource_id..."
    
    # Delete existing integration if it exists
    aws apigateway delete-integration \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --region $REGION 2>/dev/null
    
    # Create new integration
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
        --region $REGION
    
    # Add Lambda permission
    aws lambda add-permission \
        --function-name optimo-unified-handler \
        --statement-id "apigateway-$resource_id-$http_method" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:529088253685:$API_ID/*/$http_method/*" \
        --region $REGION 2>/dev/null
}

# Get all resources
echo "Getting API Gateway resources..."
RESOURCES=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION)

# Update each endpoint
echo "$RESOURCES" | jq -r '.items[] | select(.path != null) | "\(.id) \(.path)"' | while read -r resource_id path; do
    case $path in
        "/upload")
            update_integration $resource_id "POST"
            update_integration $resource_id "OPTIONS"
            ;;
        "/jobs")
            update_integration $resource_id "GET"
            update_integration $resource_id "POST"
            update_integration $resource_id "OPTIONS"
            ;;
        "/jobs/{jobId}/status")
            update_integration $resource_id "GET"
            update_integration $resource_id "OPTIONS"
            ;;
        "/jobs/{jobId}/results")
            update_integration $resource_id "GET"
            update_integration $resource_id "OPTIONS"
            ;;
        "/jobs/{jobId}/cancel")
            update_integration $resource_id "POST"
            update_integration $resource_id "OPTIONS"
            ;;
    esac
done

# Deploy API changes
echo "Deploying API changes..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Unified Lambda handler deployment" \
    --region $REGION

echo "API Gateway update complete!"
echo ""
echo "All endpoints now route to the unified Lambda handler."