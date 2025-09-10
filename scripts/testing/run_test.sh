#!/bin/bash
# Test script for prompt_opt.py hang fix
# Usage: ./run_test.sh

set -e  # Exit on error

echo "=== Testing prompt_opt.py hang fix ==="
echo

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/.claude/hooks/prompt_opt.py"
TRANSCRIPT="/tmp/test_transcript.jsonl"

# Test 1: Valid input should work
echo "Test 1: Valid input with proper pipe"
echo '{"role": "user", "content": "previous question"}' > "$TRANSCRIPT"
if echo '{"prompt": "test prompt", "transcript_path": "'$TRANSCRIPT'"}' | python3 "$HOOK_SCRIPT" 2>/dev/null | grep -q "hookSpecificOutput"; then
  echo "✓ PASS: Script processes valid input correctly"
else
  echo "✗ FAIL: Script did not process valid input"
  exit 1
fi

# Test 2: No input should fail fast
echo -e "\nTest 2: No stdin (should fail within 3 seconds)"
START=$(date +%s)
timeout 3 python3 "$HOOK_SCRIPT" 2>/dev/null || true
END=$(date +%s)
DURATION=$((END - START))
if [ $DURATION -le 3 ]; then
  echo "✓ PASS: Script exits quickly with no stdin (${DURATION}s)"
else
  echo "✗ FAIL: Script hung for ${DURATION} seconds"
  exit 1
fi

# Test 3: Empty stdin should timeout properly
echo -e "\nTest 3: Empty stdin (should timeout in ~2 seconds)"
START=$(date +%s)
echo -n | python3 "$HOOK_SCRIPT" 2>/dev/null || true
END=$(date +%s)
DURATION=$((END - START))
if [ $DURATION -le 3 ]; then
  echo "✓ PASS: Script times out properly with empty stdin (${DURATION}s)"
else
  echo "✗ FAIL: Script hung too long (${DURATION}s)"
  exit 1
fi

# Test 4: Script works with valid input (acceptance test)
echo -e "\nTest 4: Complete valid input test"
echo '{"role": "user", "content": "test"}' > "$TRANSCRIPT"
OUTPUT=$(echo '{"prompt": "how to build a REST API", "transcript_path": "'$TRANSCRIPT'"}' | python3 "$HOOK_SCRIPT" 2>/dev/null)
if echo "$OUTPUT" | grep -q "hookSpecificOutput"; then
  echo "✓ PASS: Script produces valid output for real input"
else
  echo "✗ FAIL: Script did not produce expected output"
  exit 1
fi

echo -e "\n=== All tests passed! ==="
echo
echo "The original command that was hanging:"
echo '  (echo JSON | echo ROLE > file && python3 script)'
echo
echo "Should be replaced with one of these:"
echo '  echo JSON | python3 script                      # Simple pipe'
echo '  python3 script < input.json                      # From file'
echo '  python3 script <<EOF                             # Here-doc'
echo '  JSON_CONTENT'
echo '  EOF'
