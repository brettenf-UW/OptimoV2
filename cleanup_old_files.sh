#!/bin/bash

# Cleanup old debug scripts and test files
echo "🧹 Cleaning up old OptimoV2 files..."

# Create archive directory
mkdir -p archived_scripts
ARCHIVE_DATE=$(date +%Y%m%d_%H%M%S)

# Scripts to archive (not delete)
SCRIPTS_TO_ARCHIVE=(
    "fix_deployment.sh"
    "fix_optimo_now.sh"
    "diagnose_optimo.sh"
    "rebuild_container.sh"
    "fix_deployment_optimo.sh"
    "fix_lambda_s3_permissions.sh"
    "fix_batch_s3_permissions.sh"
    "rebuild_container_v8.sh"
    "add_gemini_key_v9.sh"
    "setup_gemini_key_complete.sh"
    "verify_frontend_s3.sh"
    "test_job_submission.sh"
)

# Archive old scripts
echo "📦 Archiving old scripts..."
for script in "${SCRIPTS_TO_ARCHIVE[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "archived_scripts/${script}.${ARCHIVE_DATE}"
        echo "  ✓ Archived $script"
    fi
done

# Keep only essential scripts
echo
echo "📋 Essential scripts kept:"
ls -la *.sh *.py 2>/dev/null | grep -E "(auto_debug_system|direct_job_test|comprehensive_test|check_optimo_status)" || echo "None"

# Clean up temp files
echo
echo "🗑️ Removing temporary files..."
rm -f /tmp/optimo-* 2>/dev/null
rm -f /tmp/job-definition-*.json 2>/dev/null
rm -f /tmp/*-policy.json 2>/dev/null

echo
echo "✅ Cleanup complete!"
echo
echo "Essential files for debugging:"
echo "  • auto_debug_system.py - Automated job submission and debugging"
echo "  • direct_job_test.py - Direct Batch job testing"
echo "  • comprehensive_test.sh - System verification"
echo "  • check_optimo_status.sh - Quick status check"