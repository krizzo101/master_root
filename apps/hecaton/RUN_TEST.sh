#!/bin/bash

# CRITICAL: Ensure environment is set correctly
echo "=== Environment Check ==="
echo "CLAUDE_CODE_TOKEN: ${CLAUDE_CODE_TOKEN:0:20}..."
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-NOT_SET (good!)}"

# Make sure ANTHROPIC_API_KEY is NOT set
unset ANTHROPIC_API_KEY

# Navigate to HECATON
cd /home/opsvi/master_root/apps/hecaton

# Test 1: Simple test with verbose output to see what's happening
echo -e "\n=== Test 1: Simple execution with merge-back (verbose) ==="
python -m hecaton run "Add a simple comment to main function" --agents 1 --merge-back --dry-run --verbose

# Test 2: Two agents with merge-back
echo -e "\n=== Test 2: Two agents with merge-back ==="
python -m hecaton run "Add error handling to all functions" --agents 2 --merge-back --dry-run

# Check for patches
echo -e "\n=== Checking for patches ==="
if [ -d ".hecaton/patches" ]; then
    find .hecaton/patches -name "*.patch" -type f | head -5
    echo "Total patches found: $(find .hecaton/patches -name "*.patch" -type f | wc -l)"
else
    echo "No patches directory found"
fi

# Check for artifacts
echo -e "\n=== Checking for artifacts ==="
if [ -d ".hecaton/artifacts" ]; then
    ls -la .hecaton/artifacts/ | head -10
else
    echo "No artifacts directory found"
fi

# Check debug log for merge-back activity
echo -e "\n=== Recent debug log (checking for merge-back) ==="
if [ -f "logs/hecaton_debug_*.log" ]; then
    tail -n 20 logs/hecaton_debug_*.log | grep -E "(merge|patch|run_id)" || echo "No merge-back activity in logs"
fi
