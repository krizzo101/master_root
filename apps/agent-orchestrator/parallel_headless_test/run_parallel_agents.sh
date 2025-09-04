#!/bin/bash

# Definitive Parallel Execution Test using Claude Headless Agents
# Based on multi-agent-reference/claude_headless_agents guide

echo "🚀 DEFINITIVE PARALLEL EXECUTION TEST"
echo "Using Claude headless agents with automatic session logging"
echo "========================================================"

# Create minimal MCP config for speed
mkdir -p ~/.claude_temp_test
echo '{"mcpServers": {}}' > ~/.claude_temp_test/minimal.json

# Define test workspace
WORKSPACE="./parallel_headless_test/logs"
mkdir -p "$WORKSPACE"

echo "📊 Test setup:"
echo "  - Workspace: $WORKSPACE"
echo "  - Session logs: ~/.claude/projects/"
echo "  - Agents: 5 parallel agents with unique session IDs"
echo ""

# Generate unique session IDs for each agent
AGENT_1_SESSION=$(uuidgen)
AGENT_2_SESSION=$(uuidgen) 
AGENT_3_SESSION=$(uuidgen)
AGENT_4_SESSION=$(uuidgen)
AGENT_5_SESSION=$(uuidgen)

echo "🎯 Launching 5 agents in parallel with timestamped session logging:"
echo "  Agent 1: $AGENT_1_SESSION"
echo "  Agent 2: $AGENT_2_SESSION"
echo "  Agent 3: $AGENT_3_SESSION"
echo "  Agent 4: $AGENT_4_SESSION"
echo "  Agent 5: $AGENT_5_SESSION"
echo ""

# Record test start time
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "⏱️  TEST START: $START_TIME"

# Launch 5 agents in parallel - each will create detailed logs
(
    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config ~/.claude_temp_test/minimal.json \
        --permission-mode acceptEdits \
        --output-format json \
        --session-id "$AGENT_1_SESSION" \
        --add-dir "$WORKSPACE" \
        "You are AGENT ALPHA. Create a file called agent_alpha_proof.txt in the workspace with: START: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: ALPHA, TASK: Research parallel computing benefits, SESSION: $AGENT_1_SESSION. Then write 3 benefits of parallel computing. End with: END: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: ALPHA COMPLETE" \
        > "$WORKSPACE/agent_1_output.json" 2>&1
) &

(
    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config ~/.claude_temp_test/minimal.json \
        --permission-mode acceptEdits \
        --output-format json \
        --session-id "$AGENT_2_SESSION" \
        --add-dir "$WORKSPACE" \
        "You are AGENT BETA. Create a file called agent_beta_proof.txt in the workspace with: START: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: BETA, TASK: Analyze orchestration patterns, SESSION: $AGENT_2_SESSION. Then write 3 orchestration patterns. End with: END: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: BETA COMPLETE" \
        > "$WORKSPACE/agent_2_output.json" 2>&1
) &

(
    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config ~/.claude_temp_test/minimal.json \
        --permission-mode acceptEdits \
        --output-format json \
        --session-id "$AGENT_3_SESSION" \
        --add-dir "$WORKSPACE" \
        "You are AGENT GAMMA. Create a file called agent_gamma_proof.txt in the workspace with: START: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: GAMMA, TASK: Design workflow systems, SESSION: $AGENT_3_SESSION. Then write 3 workflow principles. End with: END: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: GAMMA COMPLETE" \
        > "$WORKSPACE/agent_3_output.json" 2>&1
) &

(
    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config ~/.claude_temp_test/minimal.json \
        --permission-mode acceptEdits \
        --output-format json \
        --session-id "$AGENT_4_SESSION" \
        --add-dir "$WORKSPACE" \
        "You are AGENT DELTA. Create a file called agent_delta_proof.txt in the workspace with: START: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: DELTA, TASK: Define test strategies, SESSION: $AGENT_4_SESSION. Then write 3 testing strategies. End with: END: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: DELTA COMPLETE" \
        > "$WORKSPACE/agent_4_output.json" 2>&1
) &

(
    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config ~/.claude_temp_test/minimal.json \
        --permission-mode acceptEdits \
        --output-format json \
        --session-id "$AGENT_5_SESSION" \
        --add-dir "$WORKSPACE" \
        "You are AGENT EPSILON. Create a file called agent_epsilon_proof.txt in the workspace with: START: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: EPSILON, TASK: Implementation practices, SESSION: $AGENT_5_SESSION. Then write 3 implementation best practices. End with: END: $(date '+%Y-%m-%d %H:%M:%S'), AGENT: EPSILON COMPLETE" \
        > "$WORKSPACE/agent_5_output.json" 2>&1
) &

echo "⚡ All 5 agents launched in background!"
echo "⏳ Waiting for completion..."

# Wait for all agents to complete
wait

# Record test end time
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "⏱️  TEST END: $END_TIME"

# Analyze results
echo ""
echo "📊 EXECUTION ANALYSIS:"
echo "======================"

echo ""
echo "1. Agent Output Files:"
for i in {1..5}; do
    if [ -f "$WORKSPACE/agent_${i}_output.json" ]; then
        echo "  ✅ Agent $i output: $(wc -l < "$WORKSPACE/agent_${i}_output.json") lines"
    else
        echo "  ❌ Agent $i output: Missing"
    fi
done

echo ""
echo "2. Agent Proof Files:"
for file in agent_alpha_proof.txt agent_beta_proof.txt agent_gamma_proof.txt agent_delta_proof.txt agent_epsilon_proof.txt; do
    if [ -f "$WORKSPACE/$file" ]; then
        echo "  ✅ $file: Created"
        echo "      $(head -1 "$WORKSPACE/$file")"
        echo "      $(tail -1 "$WORKSPACE/$file")"
    else
        echo "  ❌ $file: Missing"
    fi
done

echo ""
echo "3. Session Log Analysis:"
echo "  Session logs location: ~/.claude/projects/"
echo "  Agent 1 session: $AGENT_1_SESSION"
echo "  Agent 2 session: $AGENT_2_SESSION" 
echo "  Agent 3 session: $AGENT_3_SESSION"
echo "  Agent 4 session: $AGENT_4_SESSION"
echo "  Agent 5 session: $AGENT_5_SESSION"

# Save session IDs for analysis
echo "AGENT_1_SESSION=$AGENT_1_SESSION" > "$WORKSPACE/session_ids.txt"
echo "AGENT_2_SESSION=$AGENT_2_SESSION" >> "$WORKSPACE/session_ids.txt"
echo "AGENT_3_SESSION=$AGENT_3_SESSION" >> "$WORKSPACE/session_ids.txt"
echo "AGENT_4_SESSION=$AGENT_4_SESSION" >> "$WORKSPACE/session_ids.txt"
echo "AGENT_5_SESSION=$AGENT_5_SESSION" >> "$WORKSPACE/session_ids.txt"

echo ""
echo "🎉 PARALLEL EXECUTION TEST COMPLETE"
echo "Check agent proof files for timestamps proving parallel execution!"
