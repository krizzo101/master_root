#!/bin/bash

echo "=== HECATON Merge-Back Testing ==="
echo ""
echo "This will test merge-back functionality without requiring real Claude Code tokens"
echo ""

# Navigate to HECATON
cd /home/opsvi/master_root/apps/hecaton

# Method 1: Test the wiring directly
echo "=== Test 1: Direct wiring test (mock executor) ==="
python TEST_MERGEBACK_ONLY.py

echo ""
echo "=== Test 2: Run with test tokens (dry-run) ==="
# Set test mode and unset ANTHROPIC_API_KEY
export HECATON_TEST_MODE=1
unset ANTHROPIC_API_KEY

# Run HECATON - this will use test tokens but won't actually execute Claude
python -m hecaton run "Add error handling to functions" --agents 2 --merge-back --dry-run 2>&1 | head -40

# Check for patches (there won't be real ones in test mode)
echo ""
echo "=== Checking for any artifacts created ==="
ls -la .hecaton/patches/ 2>/dev/null || echo "No patches directory"
ls -la .hecaton/artifacts/ 2>/dev/null || echo "No artifacts directory"
