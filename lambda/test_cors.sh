#!/bin/bash

# Test CORS configuration for the API

API_URL="https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod"
ORIGIN="https://brettenf-uw.github.io"

echo "Testing CORS configuration for OptimoV2 API"
echo "==========================================="
echo "API URL: $API_URL"
echo "Origin: $ORIGIN"
echo ""

# Test each endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    echo "Testing $description ($method $endpoint)..."
    echo "-------------------------------------------"
    
    # Test preflight request
    echo "Preflight (OPTIONS) request:"
    curl -X OPTIONS \
        -H "Origin: $ORIGIN" \
        -H "Access-Control-Request-Method: $method" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -i "$API_URL$endpoint" 2>/dev/null | grep -E "(HTTP|Access-Control-|CORS)"
    
    echo -e "\nActual request:"
    if [ "$method" == "GET" ]; then
        curl -X $method \
            -H "Origin: $ORIGIN" \
            -H "Content-Type: application/json" \
            -i "$API_URL$endpoint" 2>/dev/null | grep -E "(HTTP|Access-Control-|CORS)" | head -5
    else
        curl -X $method \
            -H "Origin: $ORIGIN" \
            -H "Content-Type: application/json" \
            -d '{"test": "data"}' \
            -i "$API_URL$endpoint" 2>/dev/null | grep -E "(HTTP|Access-Control-|CORS)" | head -5
    fi
    
    echo -e "\n"
}

# Test all endpoints
test_endpoint "GET" "/jobs" "List all jobs"
test_endpoint "POST" "/upload" "Upload file"
test_endpoint "POST" "/jobs" "Submit job"
test_endpoint "GET" "/jobs/test-job-id/status" "Get job status"
test_endpoint "GET" "/jobs/test-job-id/results" "Get job results"
test_endpoint "POST" "/jobs/test-job-id/cancel" "Cancel job"

echo "CORS test complete!"