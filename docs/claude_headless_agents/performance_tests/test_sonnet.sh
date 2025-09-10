#!/bin/bash
# Sonnet Model Performance Test

MODEL="sonnet"
RESULTS_DIR="results_${MODEL}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Testing Sonnet Model"
echo "===================="
echo "Results directory: $RESULTS_DIR"
echo ""

# Function to test and measure
run_test() {
    local test_name="$1"
    local prompt="$2"
    local flags="$3"

    echo -n "Test: $test_name... "

    start=$(date +%s.%N)
    result=$(claude -p --model "$MODEL" $flags -- "$prompt" 2>&1)
    exit_code=$?
    end=$(date +%s.%N)

    duration=$(echo "$end - $start" | bc)

    # Save result
    echo "$result" > "$RESULTS_DIR/${test_name}.output"
    echo "$test_name,$duration,$exit_code" >> "$RESULTS_DIR/metrics.csv"

    echo "Done (${duration}s)"
}

# Initialize metrics file
echo "Test,Duration,ExitCode" > "$RESULTS_DIR/metrics.csv"

echo "=== EASY PROMPTS ==="
run_test "easy_simple" "What is 2+2?"
run_test "easy_list" "List three colors"
run_test "easy_json" "What is 2+2?" "--output-format json"

echo ""
echo "=== NORMAL PROMPTS ==="
run_test "normal_code" "Write a Python function to reverse a string"
run_test "normal_explain" "Explain how HTTP works in 3 sentences"
run_test "normal_fast" "Write a Python hello world" "--dangerously-skip-permissions"

echo ""
echo "=== COMPLEX PROMPTS ==="
run_test "complex_design" "Design a REST API for a todo app with 5 endpoints"
run_test "complex_code" "Write a Python class for binary search tree with insert and search"
run_test "complex_optimized" "Write a recursive fibonacci function" "--dangerously-skip-permissions --output-format json"

echo ""
echo "=== WITH MCP TOOLS ==="
echo '{"mcpServers": {}}' > "$RESULTS_DIR/minimal.json"
run_test "mcp_minimal" "Calculate 5*7" "--strict-mcp-config --mcp-config $RESULTS_DIR/minimal.json --allowed-tools mcp__calc__mul"
run_test "mcp_none" "What is 2+2?" "--strict-mcp-config --mcp-config $RESULTS_DIR/minimal.json"

echo ""
echo "Summary saved to: $RESULTS_DIR/metrics.csv"
cat "$RESULTS_DIR/metrics.csv" | column -t -s','
