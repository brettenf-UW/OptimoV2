#!/bin/bash

# This script updates all Lambda functions with proper CORS headers and error handling

# Set variables
REGION="us-west-2"
LAMBDA_FUNCTIONS=(
  "optimo-upload-handler"
  "optimo-job-submission"
  "optimo-job-status"
  "optimo-results-handler"
)

# Create package directory if it doesn't exist
mkdir -p package

# Install dependencies for results_handler_real_metrics.py
echo "Installing dependencies..."
pip install pandas -t package/
cp results_handler_real_metrics.py package/

# Create zip file for results_handler_real_metrics
echo "Creating zip file for results_handler_real_metrics..."
cd package
zip -r ../results_handler_real_metrics.zip .
cd ..

# Update each Lambda function
echo "Updating Lambda functions..."

# Update upload_handler
echo "Updating optimo-upload-handler..."
zip upload_handler.zip upload_handler.py
aws lambda update-function-code --function-name optimo-upload-handler --zip-file fileb://upload_handler.zip --region $REGION

# Update job_submission
echo "Updating optimo-job-submission..."
zip job_submission.zip job_submission.py
aws lambda update-function-code --function-name optimo-job-submission --zip-file fileb://job_submission.zip --region $REGION

# Update job_status
echo "Updating optimo-job-status..."
zip job_status.zip job_status.py
aws lambda update-function-code --function-name optimo-job-status --zip-file fileb://job_status.zip --region $REGION

# Update results_handler with the new implementation
echo "Updating optimo-results-handler..."
aws lambda update-function-code --function-name optimo-results-handler --zip-file fileb://results_handler_real_metrics.zip --region $REGION

# Update Lambda configuration for results_handler
echo "Updating Lambda configuration for optimo-results-handler..."
aws lambda update-function-configuration \
  --function-name optimo-results-handler \
  --handler results_handler_real_metrics.lambda_handler \
  --timeout 30 \
  --memory-size 512 \
  --region $REGION

# Create new API Gateway deployment
echo "Creating new API Gateway deployment..."
API_ID=$(aws apigateway get-rest-apis --region $REGION --query "items[?name=='optimo-api'].id" --output text)
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --region $REGION

echo "Lambda functions updated successfully!"
echo "API Gateway deployment created successfully!"
echo ""
echo "Next steps:"
echo "1. Test the API endpoints with sample data"
echo "2. Monitor CloudWatch logs for any errors"
echo "3. Integrate batch_job_metrics.py into your batch job container"
