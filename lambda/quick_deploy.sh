#!/bin/bash

echo "Quick deployment of unified handler..."

# Copy the unified handler to package directory
cp unified_handler.py package/

# Create a minimal deployment package (without repackaging all dependencies)
cd package
zip -r ../unified_handler_minimal.zip unified_handler.py -q

# Update just the function code
cd ..
aws lambda update-function-code \
    --function-name optimo-unified-handler \
    --zip-file fileb://unified_handler_minimal.zip \
    --region us-west-2

# Clean up
rm unified_handler_minimal.zip

echo "Deployment complete!"