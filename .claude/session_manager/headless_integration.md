# Session Manager + Headless Claude Integration

## Key Discovery: Claude Headless Mode

We can run Claude agents from the command line using `-p` (print/headless mode), which opens up powerful automation possibilities when combined with our session management system.

## Quick Reference

### Basic Headless Command
```bash
claude -p "Your task"
```

### Optimized for Speed (3-5 seconds)
```bash
# Create minimal MCP config
echo '{"mcpServers": {}}' > ~/.claude_minimal.json

# Fast execution
claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  --session-id "$(uuidgen)" \
  "Your task"
```

## Integration with Session Manager

### 1. Use Session Context in Headless Agents

```bash
#!/bin/bash
# Get context from current session and pass to headless agent

# Extract recent context from current session
SESSION_UUID=464f3bd5-9e49-4cc4-8ab3-86700d8633b9
CONTEXT=$(tail -100 /home/opsvi/.claude/projects/-home-opsvi-master-root/$SESSION_UUID.jsonl | \
  jq -r 'select(.type == "user") | .content' | tail -5)

# Pass context to headless agent
claude -p \
  --model opus \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --session-id "$(uuidgen)" \
  "Based on this recent context: $CONTEXT

   Now complete this task: Generate comprehensive tests"
```

### 2. Chain Sessions Together

```bash
#!/bin/bash
# Run multiple agents with shared context

SESSION_BASE=$(uuidgen | cut -d'-' -f1)

# Agent 1: Design
DESIGN_SESSION="${SESSION_BASE}-design"
claude -p --model opus --session-id "$DESIGN_SESSION" \
  "Design a user authentication system"

# Extract design results
DESIGN=$(cat ~/.claude/projects/*/$DESIGN_SESSION.jsonl | \
  jq -r '.message.content[0].text // empty' | tail -1)

# Agent 2: Implement based on design
IMPL_SESSION="${SESSION_BASE}-impl"
claude -p --model opus --session-id "$IMPL_SESSION" \
  "Implement this design: $DESIGN"

# Agent 3: Test the implementation
TEST_SESSION="${SESSION_BASE}-test"
claude -p --model sonnet --session-id "$TEST_SESSION" \
  "Write tests for the implementation in session: $IMPL_SESSION"
```

### 3. Parallel Agent Team with Session Tracking

```bash
#!/bin/bash
# Launch parallel agents with session management

run_agent_team() {
    local TASK="$1"
    local BASE_SESSION=$(uuidgen | cut -d'-' -f1)

    # Launch agents in parallel with unique sessions
    (
        SESSION="${BASE_SESSION}-architect"
        claude -p --model opus --session-id "$SESSION" \
            "Design architecture for: $TASK"
        echo "Architect session: $SESSION"
    ) &

    (
        SESSION="${BASE_SESSION}-researcher"
        claude -p --model opus --session-id "$SESSION" \
            "Research best practices for: $TASK"
        echo "Researcher session: $SESSION"
    ) &

    (
        SESSION="${BASE_SESSION}-tester"
        claude -p --model sonnet --session-id "$SESSION" \
            "Create test plan for: $TASK"
        echo "Tester session: $SESSION"
    ) &

    wait

    # Aggregate results using session manager
    echo "=== Team Results ==="
    for role in architect researcher tester; do
        SESSION="${BASE_SESSION}-${role}"
        echo "$role results:"
        /home/opsvi/master_root/.claude/session_manager/claude-session \
            summary --session-id "$SESSION" --json | jq -r '.recent_topics[0]'
    done
}
```

### 4. Monitor Headless Agents in Real-Time

```bash
#!/bin/bash
# Start headless agent with monitoring

SESSION_ID=$(uuidgen)
echo "Starting agent with session: $SESSION_ID"

# Launch agent in background
claude -p \
  --model opus \
  --session-id "$SESSION_ID" \
  --output-format json \
  "Complex multi-step task" &

AGENT_PID=$!

# Monitor session in real-time
echo "Monitoring session..."
tail -f ~/.claude/projects/*/$SESSION_ID.jsonl | \
  jq 'select(.type == "tool_use") | {tool: .tool_name, timestamp: .timestamp}'

# Wait for completion
wait $AGENT_PID

# Get final summary
/home/opsvi/master_root/.claude/session_manager/claude-session \
  summary --session-id "$SESSION_ID"
```

### 5. Context-Aware Prompt Optimization

```bash
#!/bin/bash
# Use session context to optimize prompts for headless agents

optimize_and_run() {
    local RAW_PROMPT="$1"

    # Get current session context
    CURRENT_SESSION=$(export CLAUDE_SESSION_UUID=464f3bd5-9e49-4cc4-8ab3-86700d8633b9 && \
        /home/opsvi/master_root/.claude/session_manager/claude-session recent 50 --json)

    # Extract relevant context
    CONTEXT_SUMMARY=$(echo "$CURRENT_SESSION" | \
        jq -r '[.[] | select(.type == "user")] | map(.content) | join("\n")' | \
        head -c 1000)

    # Run with optimized context
    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config ~/.claude_minimal.json \
        --permission-mode acceptEdits \
        --session-id "$(uuidgen)" \
        "Context from current session:
        $CONTEXT_SUMMARY

        Task: $RAW_PROMPT"
}
```

## Performance Optimization Matrix

| Configuration | Speed | Quality | Use Case |
|--------------|-------|---------|----------|
| Sonnet + Minimal MCP | 3-5s | Good | Quick tasks |
| Opus + Minimal MCP | 5-20s | Excellent | Production code |
| Sonnet + Full MCP | 10-20s | Good | Tool-heavy tasks |
| Opus + Full MCP | 20-100s | Excellent | Complex systems |

## Powerful Combinations

### 1. Session-Aware Hooks
```bash
# In prompt_opt.py, use headless Claude for better optimization
SESSION_ID=$(uuidgen)
OPTIMIZED=$(echo "$USER_PROMPT" | claude -p \
    --model sonnet \
    --strict-mcp-config --mcp-config ~/.claude_minimal.json \
    --session-id "$SESSION_ID" \
    "Optimize this prompt for Claude Code: $USER_PROMPT")
```

### 2. Automated Testing Pipeline
```bash
# After code changes, run headless test agent
git diff --name-only | while read file; do
    claude -p --model sonnet --session-id "test-$(uuidgen)" \
        "Write and run tests for changes in: $file"
done
```

### 3. Multi-Stage Workflows
```bash
# Complex workflow with session tracking
MAIN_SESSION=$(uuidgen)

# Stage 1: Analysis
claude -p --model opus --session-id "${MAIN_SESSION}-analysis" \
    "Analyze codebase and identify improvements"

# Stage 2: Implementation (parallel)
for improvement in $(seq 1 5); do
    claude -p --model sonnet --session-id "${MAIN_SESSION}-impl-$improvement" \
        "Implement improvement #$improvement" &
done
wait

# Stage 3: Integration
claude -p --model opus --session-id "${MAIN_SESSION}-integration" \
    "Integrate all improvements from sessions: ${MAIN_SESSION}-impl-*"
```

## Key Insights

1. **Speed**: Headless mode with minimal MCP config runs in 3-5 seconds
2. **Parallelization**: Can run multiple agents simultaneously
3. **Session Tracking**: Every headless run creates a session log
4. **Context Sharing**: Can extract and share context between sessions
5. **Automation**: Perfect for CI/CD, testing, and bulk operations

## Next Steps

1. Create aliases for common headless configurations
2. Build session-aware automation scripts
3. Integrate with prompt optimizer for context-aware optimization
4. Use for automated testing and code review
5. Create agent teams for complex tasks
