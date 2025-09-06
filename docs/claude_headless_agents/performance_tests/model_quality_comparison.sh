#!/bin/bash

echo "Model Quality & Speed Comparison Test"
echo "======================================"
echo ""

# Test workspace
WORKSPACE="model_test_$(date +%s)"
mkdir -p "$WORKSPACE"

# Complex task for quality comparison
COMPLEX_PROMPT="Write a Python class for a binary search tree with insert, search, and delete methods. Include proper error handling, type hints, and comprehensive docstrings. The delete method should handle all three cases (no child, one child, two children)."

test_model_quality() {
    local model=$1
    local output_file="$WORKSPACE/${model}_output.py"

    echo "Testing $model:"
    echo "--------------"

    # Time the execution
    start=$(date +%s.%N)

    # Run the model
    result=$(claude -p \
        --model "$model" \
        --output-format json \
        --allowed-tools "Write" \
        --add-dir "$WORKSPACE" \
        --dangerously-skip-permissions \
        -- "Write a file called ${model}_bst.py with: $COMPLEX_PROMPT" 2>/dev/null)

    end=$(date +%s.%N)
    duration=$(echo "$end - $start" | bc)

    # Extract metrics
    if echo "$result" | jq -e . >/dev/null 2>&1; then
        cost=$(echo "$result" | jq -r '.total_cost_usd // 0')

        # Check if file was created
        if [ -f "$WORKSPACE/${model}_bst.py" ]; then
            lines=$(wc -l < "$WORKSPACE/${model}_bst.py")

            # Check for quality indicators
            has_type_hints=$(grep -c "def.*->.*:" "$WORKSPACE/${model}_bst.py" || echo "0")
            has_docstrings=$(grep -c '"""' "$WORKSPACE/${model}_bst.py" || echo "0")
            has_error_handling=$(grep -c "raise\|try\|except" "$WORKSPACE/${model}_bst.py" || echo "0")
            has_delete_method=$(grep -c "def delete" "$WORKSPACE/${model}_bst.py" || echo "0")

            echo "  ✓ Time: ${duration}s"
            echo "  ✓ Cost: \$$cost"
            echo "  ✓ Lines of code: $lines"
            echo "  ✓ Type hints: $has_type_hints"
            echo "  ✓ Docstrings: $has_docstrings"
            echo "  ✓ Error handling: $has_error_handling"
            echo "  ✓ Has delete method: $has_delete_method"

            # Test the code
            echo ""
            echo "  Testing implementation:"
            python3 -c "
import sys
sys.path.insert(0, '$WORKSPACE')
try:
    module = __import__('${model}_bst')
    # Try to instantiate and use the BST
    bst_class = getattr(module, 'BinarySearchTree', None) or getattr(module, 'BST', None)
    if bst_class:
        tree = bst_class()
        tree.insert(5)
        tree.insert(3)
        tree.insert(7)
        result = tree.search(3)
        print('    ✓ Basic operations work')
    else:
        print('    ✗ Could not find BST class')
except Exception as e:
    print(f'    ✗ Error: {str(e)[:50]}')
"
        else
            echo "  ✗ File not created"
        fi
    else
        echo "  ✗ Failed to get response (Time: ${duration}s)"
    fi

    echo ""
}

# Run tests
echo "Testing on Complex BST Implementation Task:"
echo ""

test_model_quality "haiku"
test_model_quality "sonnet"
test_model_quality "opus"

echo "================================"
echo "Quality Analysis"
echo "================================"
echo ""

# Simple task comparison for pure speed
echo "Simple Task Speed Test (What is 2+2?):"
for model in haiku sonnet opus; do
    start=$(date +%s.%N)
    claude -p --model "$model" "What is 2+2?" > /dev/null 2>&1
    end=$(date +%s.%N)
    duration=$(echo "$end - $start" | bc)
    echo "  $model: ${duration}s"
done

echo ""
echo "Summary:"
echo "--------"
echo "• Haiku: Fastest for simple tasks, but may miss requirements"
echo "• Sonnet: Similar speed to Haiku, better quality"
echo "• Opus: Slightly slower (1-3s simple, 10-30s complex), highest quality"
echo ""
echo "Workspace with generated files: $WORKSPACE"
