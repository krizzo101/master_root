#!/bin/bash

# Comprehensive CLI Spawning Tests
# Tests optimized CLI spawning, recursive spawning, and parallel execution

echo "=== COMPREHENSIVE CLI SPAWNING TESTS ==="
echo "Starting at: $(date)"
echo ""

# Setup minimal MCP config for speed
echo '{"mcpServers": {}}' > ~/.claude_minimal.json

# Test 1: Basic Optimized CLI Spawn
echo "TEST 1: Basic Optimized CLI Spawn (should be 3-10s)"
echo "----------------------------------------"
START=$(date +%s%N)
claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  "Write 'CLI Test 1 Complete at $(date +%s%N)' to /tmp/cli-test-1.log"
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo "Duration: ${DURATION}ms"
echo ""

# Test 2: Multiple Sequential CLI Spawns
echo "TEST 2: 3 Sequential CLI Spawns"
echo "----------------------------------------"
START=$(date +%s%N)
for i in 1 2 3; do
  claude -p \
    --model sonnet \
    --strict-mcp-config --mcp-config ~/.claude_minimal.json \
    --permission-mode acceptEdits \
    "Write 'Sequential spawn $i at $(date +%s%N)' to /tmp/cli-seq-$i.log"
done
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo "Total Duration: ${DURATION}ms"
echo ""

# Test 3: Parallel CLI Spawns
echo "TEST 3: 3 Parallel CLI Spawns"
echo "----------------------------------------"
START=$(date +%s%N)
for i in 1 2 3; do
  (claude -p \
    --model sonnet \
    --strict-mcp-config --mcp-config ~/.claude_minimal.json \
    --permission-mode acceptEdits \
    "Write 'Parallel spawn $i started at $(date +%s%N)' to /tmp/cli-par-$i.log" &)
done
wait
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo "Total Duration: ${DURATION}ms"
echo ""

# Test 4: Recursive CLI Spawn (Claude spawning Claude)
echo "TEST 4: Recursive CLI Spawn (Claude spawning Claude)"
echo "----------------------------------------"
START=$(date +%s%N)
claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --allowed-tools "Bash" \
  "Use Bash to run: claude -p 'Write \"Recursive spawn complete\" to /tmp/cli-recursive.log'"
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo "Duration: ${DURATION}ms"
echo ""

# Test 5: Deep Recursive Spawn (3 levels)
echo "TEST 5: Deep Recursive Spawn (3 levels)"
echo "----------------------------------------"
START=$(date +%s%N)
cat > /tmp/spawn_level2.sh << 'EOF'
#!/bin/bash
claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  "Write 'Level 2 complete' to /tmp/cli-level2.log; Use Bash to run: claude -p \"Write 'Level 3 complete' to /tmp/cli-level3.log\""
EOF
chmod +x /tmp/spawn_level2.sh

claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --allowed-tools "Bash" \
  "Use Bash to run: /tmp/spawn_level2.sh"
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))
echo "Duration: ${DURATION}ms"
echo ""

# Results Summary
echo "=== RESULTS SUMMARY ==="
echo "Test files created:"
ls -la /tmp/cli-*.log 2>/dev/null | wc -l
echo ""
echo "Chat logs created:"
find ~/.claude -name "*.jsonl" -mmin -5 2>/dev/null | wc -l
echo ""
echo "Test complete at: $(date)"
