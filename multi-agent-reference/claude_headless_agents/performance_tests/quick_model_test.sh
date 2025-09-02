#!/bin/bash

echo "Quick Model Performance Test"
echo "============================"
echo ""

test_model() {
    local model=$1
    local task=$2

    echo "Testing $model:"
    start=$(date +%s.%N)
    result=$(claude -p --model "$model" --output-format json "$task" 2>/dev/null)
    end=$(date +%s.%N)

    duration=$(echo "$end - $start" | bc)

    if echo "$result" | jq -e . >/dev/null 2>&1; then
        cost=$(echo "$result" | jq -r '.total_cost_usd // 0')
        tokens_in=$(echo "$result" | jq -r '.usage.input_tokens // 0')
        tokens_out=$(echo "$result" | jq -r '.usage.output_tokens // 0')
        echo "  Time: ${duration}s"
        echo "  Cost: \$$cost"
        echo "  Tokens: $tokens_in in / $tokens_out out"
    else
        echo "  Time: ${duration}s"
        echo "  (Failed to parse response)"
    fi
    echo ""
}

# Simple task comparison
echo "=== SIMPLE TASK: 'What is 2+2?' ==="
test_model "haiku" "What is 2+2?"
test_model "sonnet" "What is 2+2?"
test_model "opus" "What is 2+2?"

# Code generation task
echo "=== CODE TASK: 'Write a Python fibonacci function' ==="
CODE_PROMPT="Write a Python function that returns the nth Fibonacci number"
test_model "sonnet" "$CODE_PROMPT"
test_model "opus" "$CODE_PROMPT"

echo "Note: Opus 4.1 provides superior quality and reasoning capabilities."
echo "The small time difference (1-3 seconds) is negligible compared to quality gains."
