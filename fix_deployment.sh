#!/bin/bash

# Fix deployment issues for OptimoV2

echo "=== Fixing OptimoV2 Deployment ==="
echo ""

# Make scripts executable
chmod +x lambda/deploy_unified.sh
chmod +x lambda/update_api_routes.sh

# Deploy the unified Lambda handler
echo "Step 1: Deploying unified Lambda handler..."
cd lambda
./deploy_unified.sh
cd ..

# Wait a bit for Lambda to be ready
echo "Waiting for Lambda deployment to complete..."
sleep 5

# Update API Gateway routes
echo ""
echo "Step 2: Updating API Gateway routes..."
cd lambda
./update_api_routes.sh
cd ..

echo ""
echo "=== Deployment Fix Complete ==="
echo ""
echo "The unified handler should now be deployed and all API routes updated."
echo "Please test the application again."