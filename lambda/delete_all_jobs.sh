#!/bin/bash

# Script to delete all items from optimo-jobs DynamoDB table
REGION="us-west-2"
TABLE_NAME="optimo-jobs"

echo "Starting deletion of all items from $TABLE_NAME table..."

# Read job IDs and delete each one
count=0
while IFS= read -r job_id; do
    if [ ! -z "$job_id" ]; then
        echo "Deleting job: $job_id"
        aws dynamodb delete-item \
            --table-name "$TABLE_NAME" \
            --region "$REGION" \
            --key "{\"jobId\": {\"S\": \"$job_id\"}}"
        
        if [ $? -eq 0 ]; then
            ((count++))
            echo "Successfully deleted job $job_id (Count: $count)"
        else
            echo "Failed to delete job $job_id"
        fi
    fi
done < job_ids.txt

echo "Deletion complete. Total items deleted: $count"

# Verify the table is empty
echo "Verifying table is empty..."
remaining=$(aws dynamodb scan --table-name "$TABLE_NAME" --region "$REGION" --select "COUNT" --output json | grep -o '"Count":[0-9]*' | cut -d':' -f2)
echo "Remaining items in table: $remaining"