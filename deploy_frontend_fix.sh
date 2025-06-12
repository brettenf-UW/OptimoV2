#!/bin/bash

echo "=== Deploying Frontend Fix for Results Display ==="

cd optimo-frontend

# Build the production version
echo "Building production bundle..."
npm run build

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Deploy to GitHub Pages
echo "Deploying to GitHub Pages..."
npm run deploy

if [ $? -ne 0 ]; then
    echo "Deploy failed!"
    exit 1
fi

echo ""
echo "✅ Frontend deployed successfully!"
echo "✅ Fixed:"
echo "   - Metric cards now show real data from metrics.summary"
echo "   - Charts use correct data path (metrics.charts)"
echo "   - Optimization summary displays correctly"
echo ""
echo "🌐 Visit https://brettenf-uw.github.io/OptimoV2/ to see the updated results!"
echo ""
echo "The results will now show:"
echo "- Real utilization percentages"
echo "- Actual number of optimized sections"
echo "- True student placement rates"
echo "- Calculated teacher loads"
echo "- Actual constraint violations"