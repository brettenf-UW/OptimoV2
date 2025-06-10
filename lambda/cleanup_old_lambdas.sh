#!/bin/bash

# Clean up old Lambda functions after migrating to unified handler
echo "This script will remove the old Lambda functions after confirming the unified handler works."
echo "WARNING: This is destructive! Make sure the unified handler is fully tested."
echo ""
read -p "Are you sure you want to delete the old Lambda functions? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

REGION="us-west-2"

# List of old Lambda functions to remove
OLD_FUNCTIONS=(
    "optimo-upload-handler"
    "optimo-job-submission"
    "optimo-job-status"
    "optimo-jobs-list"
    "optimo-results-handler-real-metrics"
    "optimo-job-completion-handler"
    "optimo-job-cancel-handler"
    "optimo-job-manager"
)

echo "Deleting old Lambda functions..."

for func in "${OLD_FUNCTIONS[@]}"; do
    echo "Deleting $func..."
    aws lambda delete-function --function-name $func --region $REGION 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✓ Deleted $func"
    else
        echo "  ✗ Failed to delete $func (may not exist)"
    fi
done

echo ""
echo "Cleanup complete!"
echo ""
echo "Note: The unified handler (optimo-unified-handler) is now handling all API requests."
echo "EventBridge rules may need to be updated if they were triggering the old functions."