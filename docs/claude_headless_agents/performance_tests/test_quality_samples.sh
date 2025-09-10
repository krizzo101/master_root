#!/bin/bash
# Generate quality samples from each model for comparison

echo "Generating Quality Samples"
echo "=========================="
echo ""

SAMPLES_DIR="quality_samples_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAMPLES_DIR"

# Test prompt for quality comparison
QUALITY_PROMPT="Write a Python function that validates credit card numbers using the Luhn algorithm. Include docstring, type hints, and error handling."

echo "Testing identical prompt across all models..."
echo "Prompt: $QUALITY_PROMPT"
echo ""

# Haiku sample
echo "Generating Haiku sample..."
claude -p --model haiku "$QUALITY_PROMPT" > "$SAMPLES_DIR/haiku_sample.py" 2>/dev/null
echo "✓ Haiku sample saved"

# Sonnet sample
echo "Generating Sonnet sample..."
claude -p --model sonnet "$QUALITY_PROMPT" > "$SAMPLES_DIR/sonnet_sample.py" 2>/dev/null
echo "✓ Sonnet sample saved"

# Opus sample
echo "Generating Opus sample..."
claude -p --model opus "$QUALITY_PROMPT" > "$SAMPLES_DIR/opus_sample.py" 2>/dev/null
echo "✓ Opus sample saved"

echo ""
echo "=== QUALITY ANALYSIS ==="

for model in haiku sonnet opus; do
    file="$SAMPLES_DIR/${model}_sample.py"
    if [ -f "$file" ]; then
        echo ""
        echo "${model^^} Quality Metrics:"
        echo "  Lines of code: $(wc -l < "$file")"
        echo "  Has docstring: $(grep -c '"""' "$file" || echo "0")"
        echo "  Has type hints: $(grep -c "->.*:" "$file" || echo "0")"
        echo "  Has error handling: $(grep -c "try\|except\|raise" "$file" || echo "0")"
        echo "  Validates input: $(grep -c "if\|assert" "$file" || echo "0")"

        # Check if it's valid Python
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  Valid Python: ✓"
        else
            echo "  Valid Python: ✗"
        fi

        # Show first 20 lines
        echo ""
        echo "  Preview:"
        echo "  --------"
        head -20 "$file" | sed 's/^/  /'
    fi
done

echo ""
echo "Full samples saved in: $SAMPLES_DIR/"
echo ""
echo "Quick diff between models:"
echo "=========================="

if [ -f "$SAMPLES_DIR/haiku_sample.py" ] && [ -f "$SAMPLES_DIR/opus_sample.py" ]; then
    echo "Key differences Haiku vs Opus:"
    diff --suppress-common-lines -y "$SAMPLES_DIR/haiku_sample.py" "$SAMPLES_DIR/opus_sample.py" | head -20
fi
