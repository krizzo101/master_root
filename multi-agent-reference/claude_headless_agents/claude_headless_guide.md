# Claude Code Headless Mode Guide for Dev Agents

## Overview
Claude Code can be run in "headless" mode using the `-p` or `--print` flag, which makes it suitable for automated scripts and subprocess calls. This mode prints the response and exits immediately, rather than starting an interactive session.

## Basic Usage

### Simple Command Structure
```bash
claude -p "Your prompt here"
```

### With Debug Output
```bash
claude -p -d "Your prompt here"
```
Debug mode shows detailed execution information including hooks, permissions, and API calls.

## Core Options for Automation

### 1. Print Mode (Required for Headless)
```bash
claude -p "prompt"           # Basic headless mode
claude --print "prompt"      # Long form
```

### 2. Output Formats
```bash
claude -p --output-format text "prompt"        # Default - plain text output
claude -p --output-format json "prompt"        # JSON response with metadata
claude -p --output-format stream-json --verbose "prompt"  # Streaming JSON (requires --verbose)
```

**JSON Output Example:**
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 1994,
  "result": "4",
  "session_id": "16e1b012-61e1-4c46-ac0a-393482601b77",
  "total_cost_usd": 0.0222735,
  "usage": {
    "input_tokens": 3,
    "output_tokens": 5
  }
}
```

### 3. Input Methods

#### Direct Prompt
```bash
claude -p "What is 2+2?"
```

#### Via Pipe (STDIN)
```bash
echo "What is 2+2?" | claude -p
cat file.txt | claude -p "Summarize this"
ls -la | claude -p "Count the files"
```

#### Heredoc for Multiline
```bash
cat << 'EOF' | claude -p
Generate a Python function that
calculates fibonacci numbers
EOF
```

### 4. Model Selection
```bash
claude -p --model haiku "prompt"    # Fastest, most economical
claude -p --model sonnet "prompt"   # Balanced performance
claude -p --model opus "prompt"     # Most capable
```

### 5. Tool Permissions and Restrictions

#### Allow Specific Tools
```bash
claude -p --allowed-tools "Read,Write" "prompt"
claude -p --allowed-tools "Bash(git:*)" "prompt"  # Allow only git commands
```

#### Disallow Specific Tools
```bash
claude -p --disallowed-tools "Bash,Edit" "prompt"
```

#### Bypass All Permissions (Use Cautiously)
```bash
claude -p --dangerously-skip-permissions "prompt"
```

#### Permission Modes
```bash
claude -p --permission-mode plan "prompt"         # Planning mode
claude -p --permission-mode acceptEdits "prompt"  # Auto-accept edits
claude -p --permission-mode default "prompt"      # Standard permissions
```

### 6. Directory Access
```bash
claude -p --add-dir /path/to/dir "Work with files in this directory"
claude -p --add-dir /tmp --add-dir /home/user "Multiple directories"
```

### 7. Session Management & Hooks

#### Use Specific Session ID
```bash
claude -p --session-id "550e8400-e29b-41d4-a716-446655440000" "prompt"
```

#### Continue Last Session
```bash
claude -p -c "follow up prompt"
```

#### Resume Specific Session
```bash
claude -p -r session_id "prompt"
```

#### Hooks Configuration (Limited in Headless)
**Working**: SessionEnd hooks execute on completion
```json
{
  "hooks": {
    "SessionEnd": [  // Note: Use "SessionEnd" not "SessionStop"
      {
        "hooks": [{
          "type": "command",
          "command": "echo 'Session completed' >> session.log"
        }]
      }
    ]
  }
}
```

**NOT Working in Headless**:
- PreToolUse hooks (file security checks)
- PostToolUse hooks (post-edit actions)
- SessionStart hooks (initialization)

#### Automatic Session Logging
**IMPORTANT**: All Claude sessions are automatically logged to `.claude/projects/[project-name]/[session-id].jsonl`

```bash
# Every session creates a log file automatically
# Example: Running from /home/opsvi/test
claude -p "test prompt"
# Creates: ~/.claude/projects/-home-opsvi-test/[auto-generated-session-id].jsonl

# Track specific session by setting ID
SESSION_ID=$(uuidgen)
claude -p --session-id $SESSION_ID "your task"
# Creates: ~/.claude/projects/-home-opsvi-test/$SESSION_ID.jsonl

# Monitor session in real-time (in another terminal)
tail -f ~/.claude/projects/-home-opsvi-test/$SESSION_ID.jsonl

# Parse session log for analysis
cat ~/.claude/projects/-home-opsvi-test/$SESSION_ID.jsonl | jq '.'
```

**Session Log Contents**: Each line is a JSON object with:
- User messages and prompts
- Assistant responses
- Tool invocations and results
- Timestamps for correlation
- Working directory and git branch
- Error messages and debugging info

### 8. System Prompt Customization
```bash
claude -p --append-system-prompt "Always be concise" "prompt"
claude -p --append-system-prompt "Output JSON only" "prompt"
```

### 9. MCP Server Configuration and Execution

#### Loading MCP Server Configurations
```bash
claude -p --mcp-config config.json "prompt"
claude -p --strict-mcp-config "prompt"  # Only use specified MCP servers
```

#### Executing MCP Server Tools
```bash
# Single MCP tool execution
claude -p -d --allowed-tools "mcp__time__current_time" -- "What time is it?"

# Multiple tools allowed (comma-separated)
claude -p --allowed-tools "mcp__calc__add,mcp__calc__mul" -- "Calculate 5+3 and 5*3"

# With JSON output for programmatic parsing
claude -p --output-format json --allowed-tools "mcp__calc__mul" -- "Multiply 42 by 17"

# Via stdin
echo "What is the current time in UTC?" | claude -p -d --allowed-tools "mcp__time__current_time"

# Complex calculation with debug output
claude -p -d --allowed-tools "mcp__calc__add,mcp__calc__sub" -- "What is 100 plus 25 and what is 100 minus 25?"
```

**MCP Tool Naming Convention**: MCP tools follow the format `mcp__<server_name>__<tool_name>`

**Debug Output for MCP**: The `-d` flag shows:
- MCP server connection status and timing
- Tool execution details
- Server stderr output (warnings, info messages)
- Connection failures and retry attempts

## Best Practices for Automation

### 1. Error Handling
```bash
# Check exit code
if claude -p "prompt" > output.txt 2>&1; then
    echo "Success"
else
    echo "Failed with exit code $?"
fi
```

### 2. Parsing JSON Output
```bash
# Get just the result from JSON output
claude -p --output-format json "What is 2+2?" | jq -r '.result'
```

### 3. Timeout Handling
```bash
# Use timeout command for long operations
timeout 30 claude -p "Complex task"
```

### 4. Combining with Shell Scripts
```bash
#!/bin/bash
RESULT=$(claude -p "Generate a random number between 1 and 10")
echo "Claude says: $RESULT"
```

### 5. Processing Files
```bash
# Process file content
cat code.py | claude -p "Review this code for bugs"

# Process multiple files
for file in *.js; do
    claude -p "Summarize: $(cat $file)" > "${file}.summary"
done
```

## Common Use Cases

### 1. Code Review
```bash
git diff | claude -p "Review these changes"
```

### 2. Documentation Generation
```bash
cat function.py | claude -p "Generate docstring for this function"
```

### 3. Quick Calculations
```bash
claude -p --output-format json "Calculate compound interest for \$1000 at 5% for 10 years" | jq -r '.result'
```

### 4. File Analysis
```bash
find . -name "*.log" | claude -p "What log files are these?"
```

### 5. Command Generation
```bash
claude -p "Command to find all Python files modified in last 24 hours"
```

### 6. MCP Server Tool Execution
```bash
# Time operations
claude -p --allowed-tools "mcp__time__current_time" -- "What's the current UTC time?"

# Mathematical calculations using MCP calc server
claude -p --allowed-tools "mcp__calc__mul,mcp__calc__div" -- "What is 144 divided by 12 and multiplied by 5?"

# Web search via MCP
claude -p --allowed-tools "mcp__mcp_web_search__brave_web_search" -- "Search for the latest news about AI"

# Combining multiple MCP servers
claude -p --allowed-tools "mcp__time__current_time,mcp__calc__add" -- "What time is it and what is 50+50?"
```

## Important Notes

1. **Input Required**: When using `-p`, you must provide input either as a prompt argument or via STDIN
2. **Non-Interactive**: The `-p` flag makes Claude non-interactive - it processes once and exits
3. **Debug Mode**: Use `-d` for troubleshooting to see detailed execution information including MCP server connections
4. **Permissions**: By default, Claude respects permission settings. Use `--dangerously-skip-permissions` only in secure environments
5. **Cost Tracking**: JSON output format includes cost information (`total_cost_usd`)
6. **Stream JSON**: Requires `--verbose` flag to work properly
7. **MCP Tools**: Use `--allowed-tools` to specify which MCP server tools can be executed
8. **Prompt Separator**: Use `--` before the prompt when combining multiple flags to avoid ambiguity
9. **Commands**: Custom slash commands (e.g., `/context-prime`, `/sdlc`) are NOT available in headless mode
10. **Hooks**: Only SessionEnd hooks work reliably; PreToolUse/PostToolUse hooks don't trigger in headless mode

## Performance Optimization (Based on Actual Testing)

### Critical Finding: Model Speed is Similar
Testing shows minimal speed difference between models for simple tasks:
- **Haiku**: 10-35 seconds average
- **Sonnet**: 11-22 seconds (most consistent, sometimes fastest!)
- **Opus**: 11-46 seconds (best quality)

### Real Performance Bottlenecks

| Issue | Impact | Solution | Time Saved |
|-------|---------|----------|------------|
| MCP server loading | +10-20s | Use `--strict-mcp-config` with minimal config | 80% faster |
| Permission prompts | +2-5s each | Use `--permission-mode acceptEdits` | 5-15s total |
| Debug mode | +20-30% | Remove `-d` flag in production | 20-30% faster |
| Sequential execution | 3x slower | Run agents in parallel | 60-70% faster |

### Fastest Possible Configuration (3-4 seconds)
```bash
# Create minimal MCP config
echo '{"mcpServers": {}}' > ~/.claude_minimal.json

# Run with all optimizations
claude -p \
  --model sonnet \  # Surprisingly fastest in tests!
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --dangerously-skip-permissions \
  "Your prompt"
```

### Recommended Production Configuration (5-20 seconds)
```bash
claude -p \
  --model opus \  # Best quality-speed balance
  --strict-mcp-config --mcp-config ~/.claude_minimal.json \
  --permission-mode acceptEdits \
  --output-format json \
  --session-id "$(uuidgen)" \
  "Your prompt"
```

## Limitations in Headless Mode

### Commands Not Available
1. **Custom slash commands** - `/context-prime`, `/sdlc`, etc. don't work
2. **Agent switching** - No `/agents` command
3. **Memory management** - No `/memory` command
4. **Cost tracking** - `/cost` command unavailable (use JSON output instead)

### Hooks Limitations
1. **PreToolUse hooks** - Security checks don't execute
2. **PostToolUse hooks** - Post-edit actions don't trigger
3. **SessionStart hooks** - Initialization hooks unreliable
4. **Only SessionEnd works** - Cleanup/export hooks execute properly

### Workarounds Required
- Use wrapper scripts for command functionality
- Implement security checks externally
- Load agent configs via `--append-system-prompt`
- Handle initialization in calling script

## Error Messages

Common errors and their meanings:
- "Input must be provided either through stdin or as a prompt argument" - No prompt given
- "When using --print, --output-format=stream-json requires --verbose" - Missing verbose flag
- Permission denied errors - Add `--add-dir` or adjust permissions
- "Invalid settings in projectSettings source - key: hooks.SessionStop" - Use "SessionEnd" not "SessionStop"

## Multi-Agent Session Tracking

When running multiple agents in parallel, each gets its own session log:

```bash
#!/bin/bash

# Launch multiple agents with trackable session IDs
launch_agent_team() {
    local task="$1"

    # Generate session IDs for each agent
    MASTER_ID=$(uuidgen)
    ANALYST_ID=$(uuidgen)
    DEVELOPER_ID=$(uuidgen)
    TESTER_ID=$(uuidgen)

    echo "Master Session: $MASTER_ID"
    echo "Analyst Session: $ANALYST_ID"
    echo "Developer Session: $DEVELOPER_ID"
    echo "Tester Session: $TESTER_ID"

    # Launch agents in parallel
    claude -p --session-id $ANALYST_ID "Analyze requirements for: $task" &
    claude -p --session-id $DEVELOPER_ID "Implement solution for: $task" &
    claude -p --session-id $TESTER_ID "Create tests for: $task" &

    # Master orchestrates and monitors
    claude -p --session-id $MASTER_ID "Coordinate the team working on: $task"

    # Wait for all agents to complete
    wait

    # Aggregate results from session logs
    echo "=== Team Results ===="
    for id in $ANALYST_ID $DEVELOPER_ID $TESTER_ID; do
        echo "Agent $id output:"
        tail -5 ~/.claude/projects/*/$id.jsonl | jq -r '.message.content[0].text // empty' 2>/dev/null | head -1
    done
}

# Monitor all agents in real-time (run in separate terminal)
monitor_agents() {
    local project_dir="$HOME/.claude/projects/-home-opsvi-test"

    # Use tmux or multiple terminals
    tail -f $project_dir/*.jsonl | while read line; do
        session_id=$(echo $line | jq -r '.sessionId' 2>/dev/null)
        message_type=$(echo $line | jq -r '.type' 2>/dev/null)

        if [ "$message_type" = "assistant" ]; then
            echo "[$session_id]: Processing..."
        fi
    done
}
```

**Key Benefits of Session Logging:**
- Complete audit trail of all agent activities
- Ability to debug parallel execution issues
- Performance analysis across agents
- Post-mortem investigation capabilities
- Automatic capture without configuration

## Workarounds for Headless Limitations

### Hook Alternatives
Since tool-level hooks don't work in headless mode, implement checks externally:

#### Security Check Alternative (PreToolUse replacement)
```bash
# Wrap claude execution with security checks
secure_claude() {
  local prompt="$1"

  # Pre-check for sensitive file operations
  if echo "$prompt" | grep -E "(\.env|password|secret|credential)" > /dev/null; then
    echo "ERROR: Operation blocked - sensitive file detected"
    return 1
  fi

  claude -p "$prompt"
}

# Usage
secure_claude "Create config.yaml with settings"  # Allowed
secure_claude "Create .env with API keys"         # Blocked
```

#### Post-Edit Alternative (PostToolUse replacement)
```bash
# Run post-processing after edits
claude_with_post() {
  local prompt="$1"
  local output=$(claude -p --output-format json "$prompt")

  # Check if edit was made
  if echo "$output" | jq -e '.result' | grep -q "edited"; then
    # Run post-edit actions
    ./post-edit-actions.sh
  fi

  echo "$output" | jq -r '.result'
}
```

#### Working SessionEnd Hook
```json
// .claude/settings.json - This DOES work in headless!
{
  "hooks": {
    "SessionEnd": [{  // Must use "SessionEnd" not "SessionStop"
      "hooks": [{
        "type": "command",
        "command": "./export-session.sh"
      }]
    }]
  }
}
```

### Command Alternatives
Create wrapper functions for missing commands:

```bash
#!/bin/bash
# claude-commands.sh - Emulate slash commands in headless mode

claude_cmd() {
  local cmd="$1"
  shift
  local args="$@"

  case "$cmd" in
    "context-prime")
      claude -p --append-system-prompt "$(cat .claude/commands/context-prime.md)" "$args"
      ;;
    "sdlc")
      local phase="$1"
      shift
      claude -p --append-system-prompt "$(cat .claude/commands/sdlc-${phase}.md)" "$@"
      ;;
    "five")
      claude -p --append-system-prompt "You are in FIVE methodology mode" \
        --allowed-tools "Write,Read,Edit,Bash,TodoWrite" "$args"
      ;;
    *)
      echo "Unknown command: $cmd"
      return 1
      ;;
  esac
}

# Usage
claude_cmd context-prime "Initialize the project context"
claude_cmd sdlc design "Design authentication system"
claude_cmd five "Implement user registration"
```

## Example Automation Scripts

### Basic Query Wrapper
```bash
#!/bin/bash

# Claude automation wrapper
claude_query() {
    local prompt="$1"
    local model="${2:-sonnet}"

    result=$(claude -p --model "$model" --output-format json "$prompt" 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo "$result" | jq -r '.result'
    else
        echo "Error: Query failed" >&2
        return 1
    fi
}

# Usage
answer=$(claude_query "What is the capital of France?" "haiku")
echo "Answer: $answer"
```

### MCP Tool Execution Wrapper
```bash
#!/bin/bash

# MCP-enabled Claude wrapper
claude_mcp() {
    local tools="$1"
    local prompt="$2"
    local format="${3:-text}"

    claude -p --output-format "$format" --allowed-tools "$tools" -- "$prompt"
}

# Examples
# Get current time
claude_mcp "mcp__time__current_time" "What time is it in UTC?"

# Perform calculation
result=$(claude_mcp "mcp__calc__mul,mcp__calc__add" "Calculate (5*10)+25" "json" | jq -r '.result')
echo "Result: $result"

# Web search with JSON parsing
search_results=$(claude_mcp "mcp__mcp_web_search__brave_web_search" "Latest AI news" "json")
echo "$search_results" | jq -r '.result'
```

This guide provides comprehensive information for integrating Claude Code into automated workflows and scripts.
