#!/bin/bash
# Test script to verify hook functionality

echo "=== Testing Claude Code Hooks ==="
echo ""

# Test 1: Simple stdin test
echo "Test 1: Testing JSON stdin input to hook"
echo '{"prompt": "test prompt", "session_id": "test123", "hook_event_name": "UserPromptSubmit"}' | python3 .claude/hooks/prompt_opt_minimal.py
echo "Exit code: $?"
echo ""

# Test 2: Check environment variable
echo "Test 2: Checking CLAUDE_PROJECT_DIR"
echo "Current value: '$CLAUDE_PROJECT_DIR'"
echo "Setting to: /home/opsvi/master_root"
export CLAUDE_PROJECT_DIR="/home/opsvi/master_root"
echo "New value: '$CLAUDE_PROJECT_DIR'"
echo ""

# Test 3: Test with full path
echo "Test 3: Testing hook with absolute path"
echo '{"prompt": "test", "session_id": "test", "hook_event_name": "UserPromptSubmit"}' | /home/opsvi/master_root/test_hook.py
echo "Exit code: $?"
echo ""

# Test 4: Check log file
echo "Test 4: Checking test log output"
if [ -f /tmp/hook_test.log ]; then
    echo "Log contents:"
    tail -20 /tmp/hook_test.log
else
    echo "No log file found"
fi
