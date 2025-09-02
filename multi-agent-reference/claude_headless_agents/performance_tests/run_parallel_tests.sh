#!/bin/bash
# Run all model tests in parallel and collect results

echo "Starting Parallel Model Performance Tests"
echo "========================================="
echo ""

# Make scripts executable
chmod +x test_haiku.sh test_sonnet.sh test_opus.sh

# Run tests in parallel
echo "Launching parallel tests..."
./test_haiku.sh > haiku_test.log 2>&1 &
PID_HAIKU=$!

./test_sonnet.sh > sonnet_test.log 2>&1 &
PID_SONNET=$!

./test_opus.sh > opus_test.log 2>&1 &
PID_OPUS=$!

echo "Tests running with PIDs:"
echo "  Haiku:  $PID_HAIKU"
echo "  Sonnet: $PID_SONNET"
echo "  Opus:   $PID_OPUS"
echo ""

# Wait for all to complete
echo "Waiting for tests to complete..."
wait $PID_HAIKU
echo "✓ Haiku complete"
wait $PID_SONNET
echo "✓ Sonnet complete"
wait $PID_OPUS
echo "✓ Opus complete"

echo ""
echo "All tests completed! Generating summary..."
echo ""

# Find result directories
HAIKU_DIR=$(ls -d results_haiku_* 2>/dev/null | tail -1)
SONNET_DIR=$(ls -d results_sonnet_* 2>/dev/null | tail -1)
OPUS_DIR=$(ls -d results_opus_* 2>/dev/null | tail -1)

echo "=== PERFORMANCE SUMMARY ==="
echo ""

if [ -d "$HAIKU_DIR" ]; then
    echo "HAIKU Results:"
    cat "$HAIKU_DIR/metrics.csv" | column -t -s','
    echo ""
fi

if [ -d "$SONNET_DIR" ]; then
    echo "SONNET Results:"
    cat "$SONNET_DIR/metrics.csv" | column -t -s','
    echo ""
fi

if [ -d "$OPUS_DIR" ]; then
    echo "OPUS Results:"
    cat "$OPUS_DIR/metrics.csv" | column -t -s','
    echo ""
fi

echo "Detailed outputs saved in:"
echo "  - $HAIKU_DIR/"
echo "  - $SONNET_DIR/"
echo "  - $OPUS_DIR/"
