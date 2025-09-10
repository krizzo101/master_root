#!/bin/bash
# Test specific optimization combinations

echo "Testing Optimization Combinations"
echo "================================="
echo ""

RESULTS_DIR="optimization_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Create minimal MCP config
echo '{"mcpServers": {}}' > "$RESULTS_DIR/minimal_mcp.json"

# Test function
test_combo() {
    local name="$1"
    local model="$2"
    local prompt="$3"
    local flags="$4"

    echo -n "$name: "

    start=$(date +%s.%N)
    output=$(claude -p --model "$model" $flags -- "$prompt" 2>&1)
    exit_code=$?
    end=$(date +%s.%N)

    duration=$(echo "$end - $start" | bc)

    echo "${duration}s"
    echo "$output" > "$RESULTS_DIR/${name}.output"
    echo "$name,$model,$duration,$exit_code,\"$flags\"" >> "$RESULTS_DIR/combos.csv"
}

# Initialize CSV
echo "Name,Model,Duration,ExitCode,Flags" > "$RESULTS_DIR/combos.csv"

echo "=== FASTEST POSSIBLE CONFIGURATIONS ==="
test_combo "fastest_haiku" "haiku" "What is 2+2?" \
    "--dangerously-skip-permissions --strict-mcp-config --mcp-config $RESULTS_DIR/minimal_mcp.json"

test_combo "fastest_sonnet" "sonnet" "What is 2+2?" \
    "--dangerously-skip-permissions --strict-mcp-config --mcp-config $RESULTS_DIR/minimal_mcp.json"

test_combo "fastest_opus" "opus" "What is 2+2?" \
    "--dangerously-skip-permissions --strict-mcp-config --mcp-config $RESULTS_DIR/minimal_mcp.json"

echo ""
echo "=== PRODUCTION CONFIGURATIONS ==="
test_combo "prod_haiku" "haiku" "List 3 programming languages" \
    "--output-format json --permission-mode acceptEdits --session-id $(uuidgen)"

test_combo "prod_sonnet" "sonnet" "List 3 programming languages" \
    "--output-format json --permission-mode acceptEdits --session-id $(uuidgen)"

test_combo "prod_opus" "opus" "List 3 programming languages" \
    "--output-format json --permission-mode acceptEdits --session-id $(uuidgen)"

echo ""
echo "=== COMPLEX TASK OPTIMIZED ==="
COMPLEX="Write a Python function for quicksort with comments"

test_combo "complex_fast_haiku" "haiku" "$COMPLEX" \
    "--dangerously-skip-permissions --output-format json"

test_combo "complex_fast_sonnet" "sonnet" "$COMPLEX" \
    "--dangerously-skip-permissions --output-format json"

test_combo "complex_fast_opus" "opus" "$COMPLEX" \
    "--dangerously-skip-permissions --output-format json"

echo ""
echo "=== MONITORING CONFIGURATIONS ==="
test_combo "monitor_sonnet" "sonnet" "Count to 3" \
    "--output-format stream-json --verbose"

test_combo "monitor_opus" "opus" "Count to 3" \
    "--output-format stream-json --verbose"

echo ""
echo "Results saved to: $RESULTS_DIR/combos.csv"
echo ""
cat "$RESULTS_DIR/combos.csv" | column -t -s','
