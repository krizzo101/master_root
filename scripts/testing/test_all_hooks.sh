#!/bin/bash
echo "=== Testing All Claude Code Hooks ==="
echo ""

# Test prompt_opt.py via wrapper
echo "1. Testing prompt_opt_wrapper.sh:"
echo '{"prompt": "hello world", "session_id": "test", "hook_event_name": "UserPromptSubmit"}' | \
    /home/opsvi/master_root/.claude/hooks/prompt_opt_wrapper.sh 2>&1 | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ SUCCESS' if 'hookSpecificOutput' in d else '❌ FAILED')"

# Test answer_review.py via wrapper
echo ""
echo "2. Testing answer_review_wrapper.sh:"
echo '{"session_id": "test", "hook_event_name": "Stop"}' | \
    /home/opsvi/master_root/.claude/hooks/answer_review_wrapper.sh 2>&1 | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ SUCCESS' if 'suppressOutput' in d else '❌ FAILED')"

# Test safety_gate.py
echo ""
echo "3. Testing safety_gate.py:"
echo '{"tool_name": "Bash", "tool_input": {"command": "ls"}, "hook_event_name": "PreToolUse"}' | \
    /home/opsvi/master_root/.claude/hooks/safety_gate.py 2>&1
if [ $? -eq 0 ]; then echo "✅ SUCCESS"; else echo "❌ FAILED"; fi

echo ""
echo "=== All Hook Tests Complete ===="
