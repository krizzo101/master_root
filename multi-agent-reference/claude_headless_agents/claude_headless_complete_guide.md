# Claude Headless Agent Complete Guide

## Quick Start: 80/20 Solution (30 seconds setup, 3-20 seconds per call)

### One-Time Setup
```bash
# 1. Create minimal MCP config (biggest performance gain)
echo '{"mcpServers": {}}' > ~/.claude_minimal.json

# 2. Add optimized alias to your shell
echo 'alias claude-fast="claude -p --strict-mcp-config --mcp-config ~/.claude_minimal.json --permission-mode acceptEdits --output-format json"' >> ~/.bashrc
source ~/.bashrc
```

### Daily Usage
```bash
# Production quality (5-20 seconds)
claude-fast --model opus --session-id "$(uuidgen)" "Your task"

# Maximum speed (3-5 seconds)
claude-fast --model sonnet --dangerously-skip-permissions "Simple task"

# With workspace
claude-fast --model opus --add-dir ./workspace "Complex multi-file task"
```

## Performance Facts (From Actual Testing)

### Model Speed Comparison (Surprising Results!)

| Model | Simple Tasks | Complex Tasks | Quality | **Recommendation** |
|-------|-------------|---------------|---------|-------------------|
| **Sonnet** | **3.18s** ✨ | 17-22s | Good | **Best overall** |
| Opus | 3.42s | 42-100s | Excellent | Complex tasks only |
| Haiku | 3.29s | 22-35s | Basic | Rarely needed |

**Key Finding**: Sonnet is often FASTER than Haiku with much better quality!

### Real Performance Bottlenecks

| Problem | Default Time | Optimized | Fix | Impact |
|---------|--------------|-----------|-----|--------|
| **MCP servers** | 12-20s | 2-4s | `--strict-mcp-config` | **80% faster** |
| Permission prompts | +2-5s each | 0s | `--permission-mode acceptEdits` | Save 5-15s |
| Debug mode | +30% | 0% | Remove `-d` flag | 30% faster |
| Sequential execution | 15+ min | 2-5 min | Parallelize | 70% faster |

## Core Command Options

### Essential Flags

| Flag | Purpose | Impact | When to Use |
|------|---------|--------|-------------|
| `-p, --print` | Headless mode | Required | Always for automation |
| `--model` | Model selection | Quality/speed | opus=quality, sonnet=speed |
| `--strict-mcp-config` | Limit MCP servers | -10s | Always |
| `--permission-mode` | Skip prompts | -5s | acceptEdits or bypass |
| `--output-format json` | Structured output | Parsing | Automation |
| `--session-id` | Track sessions | Debugging | Always recommended |
| `--allowed-tools` | Limit tools | Security | When specific tools needed |
| `--add-dir` | Directory access | Required | File operations |

### Input Methods

```bash
# Direct prompt
claude -p "Your prompt"

# Via stdin
echo "Your prompt" | claude -p
cat file.txt | claude -p "Analyze this"

# Heredoc for multiline
cat << 'EOF' | claude -p
Multi-line
prompt here
EOF
```

## Session Management & Monitoring

### Automatic Session Logging

Every session is automatically logged to:
```
~/.claude/projects/[project-name]/[session-id].jsonl
```

### Real-Time Monitoring
```bash
# Start agent with tracking
SESSION_ID=$(uuidgen)
claude-fast --session-id $SESSION_ID "Your task" &

# Monitor in another terminal
tail -f ~/.claude/projects/*/$SESSION_ID.jsonl | jq '.type'
```

### Post-Execution Analysis
```bash
# View full session
cat ~/.claude/projects/*/$SESSION_ID.jsonl | jq '.'

# Extract errors
cat ~/.claude/projects/*/$SESSION_ID.jsonl | jq 'select(.error != null)'

# Get all responses
cat ~/.claude/projects/*/$SESSION_ID.jsonl | jq -r '.message.content[0].text // empty'
```

## Agent Configuration Templates

### 1. Universal Production Agent (90% of use cases)
```bash
claude -p \
  --model opus \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  --session-id "$(uuidgen)" \
  --allowed-tools "Write,Read,Edit,Bash,TodoWrite" \
  --add-dir "./workspace" \
  -- "Your task"
```
**Time: 5-20 seconds**

### 2. Speed Demon (Simple tasks)
```bash
claude -p \
  --model sonnet \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --dangerously-skip-permissions \
  -- "Quick question"
```
**Time: 3-5 seconds**

### 3. Quality Champion (Complex tasks)
```bash
claude -p \
  --model opus \
  --output-format json \
  --session-id "$(uuidgen)" \
  --append-system-prompt "Be thorough. Include error handling and tests." \
  --allowed-tools "Write,Read,Edit,Bash,TodoWrite" \
  -- "Complex implementation task"
```
**Time: 20-100 seconds**

## Parallel Agent Orchestration

### Cut Time by 70% with Parallel Execution
```bash
#!/bin/bash

run_agent_team() {
    local TASK="$1"
    local WORKSPACE="./team_workspace"
    mkdir -p "$WORKSPACE"

    # Launch agents in parallel
    (
        claude-fast --model opus --session-id "$(uuidgen)" \
            --add-dir "$WORKSPACE" \
            "Design the architecture for: $TASK" > design.json
    ) &

    (
        claude-fast --model opus --session-id "$(uuidgen)" \
            --add-dir "$WORKSPACE" \
            "Research best practices for: $TASK" > research.json
    ) &

    (
        claude-fast --model sonnet --session-id "$(uuidgen)" \
            --add-dir "$WORKSPACE" \
            "Create test plan for: $TASK" > tests.json
    ) &

    # Wait for all to complete
    wait

    # Aggregate results
    echo "=== Team Results ==="
    for file in design.json research.json tests.json; do
        echo "${file%.*}: $(jq -r '.result' $file | head -5)..."
    done
}

# Usage
run_agent_team "user authentication system"
```

## MCP Server Tools

### Tool Naming Convention
MCP tools follow format: `mcp__<server_name>__<tool_name>`

### Common MCP Tools
```bash
# Time operations
claude -p --allowed-tools "mcp__time__current_time" -- "What time is it?"

# Calculations
claude -p --allowed-tools "mcp__calc__mul,mcp__calc__add" -- "Calculate (5*10)+25"

# Web search
claude -p --allowed-tools "mcp__mcp_web_search__brave_web_search" -- "Latest AI news"
```

### Minimal MCP Configurations

```json
// ~/.claude_minimal.json - Maximum speed (empty)
{"mcpServers": {}}

// ~/.claude_dev.json - For development
{
  "mcpServers": {
    "shell_exec": {
      "command": "python",
      "args": ["-m", "mcp_shell_exec"]
    }
  }
}
```

## Common Patterns & Solutions

### Multi-Step Workflow (Single Call)
```bash
claude-fast --model opus -- "
1. Create a FastAPI user management API
2. Include CRUD endpoints
3. Add SQLAlchemy models
4. Write Pydantic schemas
5. Include unit tests
6. Save as: app.py, models.py, schemas.py, test_app.py
"
# Time: 45-60s (vs 15+ minutes sequential)
```

### Retry with Continuation
```bash
#!/bin/bash
run_with_retry() {
    local PROMPT="$1"
    local SESSION_ID="$(uuidgen)"
    local MAX_RETRIES=3

    for i in $(seq 1 $MAX_RETRIES); do
        if [ $i -eq 1 ]; then
            FULL_PROMPT="$PROMPT"
        else
            FULL_PROMPT="Continue from where you left off: $PROMPT"
        fi

        if result=$(claude-fast --model opus --session-id "$SESSION_ID" "$FULL_PROMPT"); then
            echo "$result"
            return 0
        fi

        echo "Retry $i/$MAX_RETRIES..." >&2
        sleep 2
    done
    return 1
}
```

### Bulk Operations (100+ tasks)
```bash
#!/bin/bash
bulk_process() {
    local items=("$@")

    for item in "${items[@]}"; do
        claude -p \
            --model sonnet \
            --strict-mcp-config --mcp-config ~/.claude_minimal.json \
            --dangerously-skip-permissions \
            "Process: $item" &

        # Limit to 10 parallel jobs
        while [ $(jobs -r | wc -l) -ge 10 ]; do
            sleep 0.1
        done
    done
    wait
}
```

## Troubleshooting Performance

### Quick Diagnosis
```bash
#!/bin/bash
echo "Performance Diagnosis"
echo "===================="

# Test 1: Baseline
echo -n "1. Default (no optimization): "
time claude -p "What is 2+2?" > /dev/null 2>&1

# Test 2: MCP optimization
echo -n "2. With MCP optimization: "
time claude -p --strict-mcp-config --mcp-config ~/.claude_minimal.json "What is 2+2?" > /dev/null 2>&1

# Test 3: Full optimization
echo -n "3. Full optimization: "
time claude -p --model sonnet \
    --strict-mcp-config --mcp-config ~/.claude_minimal.json \
    --dangerously-skip-permissions "What is 2+2?" > /dev/null 2>&1

echo ""
echo "Diagnosis:"
echo "If Test 1 > 10s: MCP servers are the issue"
echo "If Test 2 > 5s: Permission prompts are the issue"
echo "If Test 3 > 3s: Network or API issues"
```

### Common Issues & Solutions

| Symptom | Cause | Solution |
|---------|-------|----------|
| 15+ minute execution | MCP servers loading | Use `--strict-mcp-config` |
| Multiple prompts | Permission system | Use `--permission-mode acceptEdits` |
| Slow simple tasks | Wrong model | Use Sonnet, not Haiku |
| Timeout errors | Task too vague | Be specific, use Opus |
| High costs | Using Opus for everything | Use Sonnet for simple tasks |

## Decision Matrix

### When to Use Which Model

| Scenario | Model | Config | Expected Time |
|----------|-------|--------|---------------|
| Quick query | Sonnet | Full optimize | 3-5s |
| Production code | Opus | Standard | 20-60s |
| Bulk operations | Sonnet | Full optimize | 3-5s each |
| Complex design | Opus | Standard | 40-100s |
| CI/CD pipeline | Sonnet | Optimize | 10-20s |

### When to Use Which Flags

| Need | Flags | Trade-off |
|------|-------|-----------|
| Maximum speed | `--dangerously-skip-permissions --strict-mcp-config` | Less safe |
| Production safe | `--permission-mode acceptEdits --session-id` | Slightly slower |
| Debugging | `--output-format json --session-id` | Easy to parse |
| Monitoring | `--output-format stream-json --verbose` | Real-time view |

## Error Handling

### Common Errors
```
"Input must be provided either through stdin or as a prompt argument"
→ Solution: Provide prompt after flags or via stdin

"When using --print, --output-format=stream-json requires --verbose"
→ Solution: Add --verbose flag

"Permission denied"
→ Solution: Add --add-dir or use --permission-mode acceptEdits
```

## The Bottom Line

### For 95% of Tasks
```bash
claude -p \
  --model opus \
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  --session-id "$(uuidgen)" \
  "Your task"
```

### Performance Expectations
- Simple tasks: **3-10 seconds**
- Normal tasks: **10-30 seconds**
- Complex tasks: **30-100 seconds**
- Multi-agent workflows: **2-5 minutes** (parallel)

**Your 15+ minute problem is solved!**
