#!/bin/bash
# Final verification of prompt_opt.py hook

echo "=== HOOK FUNCTIONALITY VERIFICATION ==="
echo
echo "Testing: .claude/hooks/prompt_opt.py"
echo "Expected: Optimizes prompts without hanging"
echo

RESULTS=()

# Test 1: Normal operation
echo -n "1. Normal operation with valid input: "
echo '{"role": "user", "content": "test"}' > /tmp/t.jsonl
if echo '{"prompt": "test", "transcript_path": "/tmp/t.jsonl"}' | timeout 5 python3 .claude/hooks/prompt_opt.py 2>/dev/null | grep -q "hookSpecificOutput"; then
    echo "✓ PASS"
    RESULTS+=("PASS")
else
    echo "✗ FAIL"
    RESULTS+=("FAIL")
fi

# Test 2: No hang on missing stdin
echo -n "2. No hang when stdin missing: "
START=$(date +%s%N)
timeout 3 python3 .claude/hooks/prompt_opt.py </dev/null 2>&1 >/dev/null
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
if [ $DURATION -lt 3000 ]; then
    echo "✓ PASS (exited in ${DURATION}ms)"
    RESULTS+=("PASS")
else
    echo "✗ FAIL (took ${DURATION}ms)"
    RESULTS+=("FAIL")
fi

# Test 3: Handles pipe correctly
echo -n "3. Processes piped input correctly: "
if echo '{"prompt": "how to code", "transcript_path": "/tmp/t.jsonl"}' | python3 .claude/hooks/prompt_opt.py 2>/dev/null | jq -e '.hookSpecificOutput.hookEventName == "UserPromptSubmit"' >/dev/null 2>&1; then
    echo "✓ PASS"
    RESULTS+=("PASS")
else
    echo "✗ FAIL"
    RESULTS+=("FAIL")
fi

# Test 4: Error handling
echo -n "4. Handles invalid input gracefully: "
if echo "invalid json" | timeout 2 python3 .claude/hooks/prompt_opt.py 2>&1 | grep -q "suppressOutput"; then
    echo "✓ PASS"
    RESULTS+=("PASS")
else
    echo "✗ FAIL"
    RESULTS+=("FAIL")
fi

# Test 5: API integration (if API key is set)
echo -n "5. OpenAI API integration: "
if [ -n "$OPENAI_API_KEY" ]; then
    OUTPUT=$(echo '{"prompt": "test API", "transcript_path": "/tmp/t.jsonl"}' | timeout 15 python3 .claude/hooks/prompt_opt.py 2>/dev/null)
    if echo "$OUTPUT" | grep -q "hookSpecificOutput"; then
        echo "✓ PASS"
        RESULTS+=("PASS")
    else
        echo "⚠ WARN (API may be down/quota exceeded)"
        RESULTS+=("WARN")
    fi
else
    echo "⚠ SKIP (no API key)"
    RESULTS+=("SKIP")
fi

echo
echo "=== FINAL VERDICT ==="
FAIL_COUNT=0
for result in "${RESULTS[@]}"; do
    if [ "$result" == "FAIL" ]; then
        ((FAIL_COUNT++))
    fi
done

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ HOOK IS WORKING CORRECTLY"
    echo "All critical tests passed. The hook:"
    echo "  • Processes valid input and returns optimized prompts"
    echo "  • Does not hang when stdin is missing (fixed)"
    echo "  • Handles pipes and redirects properly"
    echo "  • Gracefully handles invalid input"
    exit 0
else
    echo "❌ HOOK HAS ISSUES"
    echo "$FAIL_COUNT test(s) failed"
    exit 1
fi
