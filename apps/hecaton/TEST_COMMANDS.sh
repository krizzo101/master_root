#!/bin/bash
# HECATON Merge-Back Testing Commands

# Setup - Navigate to HECATON directory
cd /home/opsvi/master_root/apps/hecaton

# Test 1: Basic execution with merge-back (dry-run for safety)
echo "=== Test 1: Basic merge-back with 2 agents (dry-run) ==="
python -m hecaton run "Add debug logging to all functions" --agents 2 --merge-back --dry-run

# Check if patches were created
echo -e "\n=== Checking for patches ==="
ls -la .hecaton/patches/run_*/

# Test 2: Simple task without merge-back (control test)
echo -e "\n=== Test 2: Without merge-back (control) ==="
python -m hecaton run "Write a hello world function" --agents 2 --no-merge-back

# Test 3: Test with verbose output to see run_id generation
echo -e "\n=== Test 3: Verbose mode to see run_id ==="
python -m hecaton run "Create a simple calculator class" --agents 2 --merge-back --dry-run --verbose 2>&1 | grep -E "(run_id|merge-back|patch)"

# Test 4: Check for conflicts with overlapping changes
echo -e "\n=== Test 4: Test conflict detection ==="
python -m hecaton run "Refactor the entire __main__.py file completely" --agents 3 --merge-back --dry-run

# Check artifacts generated
echo -e "\n=== Checking for artifacts ==="
ls -la .hecaton/artifacts/

# Test 5: Minimal test - single agent
echo -e "\n=== Test 5: Single agent test ==="
python -m hecaton run "Add a comment to the main function" --agents 1 --merge-back --dry-run

# View any generated patches
echo -e "\n=== Viewing patch contents (if any) ==="
find .hecaton/patches -name "*.patch" -type f -exec echo "--- Patch: {} ---" \; -exec head -20 {} \; 2>/dev/null

# Check git worktrees (should see staging worktrees)
echo -e "\n=== Checking git worktrees ==="
git worktree list

# Clean up test artifacts (optional)
echo -e "\n=== Cleanup commands (uncomment to run) ==="
echo "# rm -rf .hecaton/patches/*"
echo "# rm -rf .hecaton/artifacts/*"
echo "# git worktree prune"
