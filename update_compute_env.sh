#!/bin/bash

# Update compute environment for heavy workloads with fast startup

echo "Updating compute environment for heavy optimization workloads..."

# First, disable the compute environment to make changes
aws batch update-compute-environment \
  --compute-environment optimo-compute-env \
  --state DISABLED \
  --region us-west-2

echo "Waiting for compute environment to disable..."
sleep 30

# Create a new compute environment with better settings
aws batch create-compute-environment \
  --compute-environment-name optimo-compute-env-v2 \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type": "EC2",
    "allocationStrategy": "BEST_FIT_PROGRESSIVE",
    "minvCpus": 32,
    "maxvCpus": 256,
    "desiredvCpus": 64,
    "instanceTypes": [
      "c5.9xlarge",
      "c5.12xlarge",
      "c5.18xlarge",
      "c5.24xlarge",
      "c5n.18xlarge",
      "m5.12xlarge",
      "m5.16xlarge",
      "m5.24xlarge"
    ],
    "subnets": ["subnet-052f00df5ca1b5b60"],
    "securityGroupIds": ["sg-0c0ab9f921426265c"],
    "instanceRole": "arn:aws:iam::529088253685:instance-profile/ecsInstanceRole",
    "tags": {
      "Name": "optimo-batch-instance",
      "Project": "OptimoV2"
    },
    "bidPercentage": 80,
    "spotIamFleetRole": "arn:aws:iam::529088253685:role/aws-batch-spot-fleet-role",
    "ec2Configuration": [{
      "imageType": "ECS_AL2"
    }]
  }' \
  --service-role arn:aws:iam::529088253685:role/aws-service-role/batch.amazonaws.com/AWSServiceRoleForBatch \
  --region us-west-2

echo "Compute environment created. Now updating job queue..."

# Create new job queue
aws batch create-job-queue \
  --job-queue-name optimo-job-queue-v2 \
  --state ENABLED \
  --priority 1000 \
  --compute-environment-order order=1,computeEnvironment=optimo-compute-env-v2 \
  --region us-west-2

echo "Done! New compute environment and job queue created."
echo ""
echo "Next steps:"
echo "1. Update Lambda environment variable JOB_QUEUE to 'optimo-job-queue-v2'"
echo "2. Delete old compute environment and job queue once verified"