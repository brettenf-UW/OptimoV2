#!/bin/bash

echo "=== URGENT: Rebuilding Container v8 with Region Fix ==="
echo
echo "CRITICAL: The current v8 container does NOT have the AWS_DEFAULT_REGION fix!"
echo "It was built before the script was updated."
echo
echo "Please run ONE of these commands:"
echo
echo "Option 1 - PowerShell (if Docker Desktop is running):"
echo "  ./rebuild_container_v8.ps1"
echo
echo "Option 2 - AWS CloudShell:"
echo "  1. Open AWS CloudShell in your browser"
echo "  2. Clone your repo: git clone https://github.com/YOUR-REPO/OptimoV2.git"
echo "  3. cd OptimoV2"
echo "  4. Run: ./rebuild_container_v8.sh"
echo
echo "Option 3 - EC2 Instance:"
echo "  Launch a small EC2 instance with Docker installed and run the build there"
echo
echo "The container MUST be rebuilt to include the region fix!"