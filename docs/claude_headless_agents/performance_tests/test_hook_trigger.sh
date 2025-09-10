#!/bin/bash
SESSION_ID=$(uuidgen)
echo "Testing hooks with session: $SESSION_ID"

# Test SessionStart hook
echo "=== Testing SessionStart hook ==="
claude -p -d --session-id "$SESSION_ID" "What is 1+1?" 2>&1 | grep -E "(Session started|hook|Hook)" | head -5

# Test PreToolUse hook (should block sensitive file write)
echo "=== Testing PreToolUse hook (sensitive file block) ==="
claude -p -d --session-id "$SESSION_ID" "Create a file called .env with test content" 2>&1 | grep -E "(hook|blocked|denied|ERROR)" | head -5

# Test PostToolUse hook
echo "=== Testing PostToolUse hook ==="
claude -p -d --session-id "$SESSION_ID" "Edit the file test.txt and add 'hello'" 2>&1 | grep -E "(post-edit|hook|Hook)" | head -5
