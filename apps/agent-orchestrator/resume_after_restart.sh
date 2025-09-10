#!/bin/bash
# Standardized resume for orchestrator workflows after restart

echo "======================================"
echo "STANDARDIZED CHECKPOINT RESUME"
echo "======================================"

cd /home/opsvi/master_root/apps/agent-orchestrator

# Use standardized resume script - auto-detects checkpoint and resumes appropriately
python standardized_resume.py output/self_improvement_continued --max-parallel 15

echo ""
echo "Resume complete - Check output above for status"