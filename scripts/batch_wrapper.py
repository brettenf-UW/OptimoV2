#!/usr/bin/env python3
"""
Wrapper script to bridge between Lambda environment variables and the batch job script
"""
import os
import sys
import subprocess

# Map Lambda environment variables to what the script expects
env_mappings = {
    'jobId': os.environ.get('JOB_ID', ''),
    'inputFiles': ','.join([
        os.environ.get('STUDENT_INFO_KEY', ''),
        os.environ.get('STUDENT_PREFERENCES_KEY', ''),
        os.environ.get('TEACHER_INFO_KEY', ''),
        os.environ.get('TEACHER_UNAVAILABILITY_KEY', ''),
        os.environ.get('SECTIONS_INFO_KEY', ''),
        os.environ.get('PERIOD_KEY', '')
    ]).rstrip(',')
}

# Set the mapped environment variables
for key, value in env_mappings.items():
    os.environ[key] = value

# Also ensure the script can find the input files by their keys
os.environ['STUDENT_INFO_KEY'] = os.environ.get('STUDENT_INFO_KEY', '')
os.environ['STUDENT_PREFERENCES_KEY'] = os.environ.get('STUDENT_PREFERENCES_KEY', '')
os.environ['TEACHER_INFO_KEY'] = os.environ.get('TEACHER_INFO_KEY', '')
os.environ['TEACHER_UNAVAILABILITY_KEY'] = os.environ.get('TEACHER_UNAVAILABILITY_KEY', '')
os.environ['SECTIONS_INFO_KEY'] = os.environ.get('SECTIONS_INFO_KEY', '')
os.environ['PERIOD_KEY'] = os.environ.get('PERIOD_KEY', '')

# Run the actual batch job script
sys.exit(subprocess.call(['python', '/app/scripts/run_batch_job.py']))