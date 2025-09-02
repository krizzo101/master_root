# Headless Claude Agent Testing Report

## Testing Environment
- **Location**: `/home/opsvi/test/`
- **Configuration**: Copied `.claude/` directory from `/home/opsvi/master_root/`
- **Testing Method**: Using `claude -p` (headless/print mode)

## Key Findings

### 1. Commands in Headless Mode ❌
**Finding**: Slash commands (like `/context-prime`, `/help`) work differently in headless mode
- `/help` returns generic help information, not custom commands
- Custom commands from `.claude/commands/` are NOT accessible in headless mode
- Commands appear to be an interactive-only feature
- **Reason**: Headless mode bypasses the command system entirely

### 2. Hooks in Headless Mode ✅⚠️
**Finding**: Hooks partially work when configured correctly
- **Fixed**: Changed `SessionStop` to `SessionEnd` in settings.json (proper event name)
- **SessionEnd hooks**: ✅ Working - executes on session completion
- **SessionStart hooks**: ⚠️ Not consistently triggered in headless mode
- **PreToolUse/PostToolUse hooks**: ❌ Not triggered for tool-specific events
- **Issue**: Only session-level hooks work reliably; tool-level hooks don't execute in headless mode
- **Note**: Hooks must be in project `.claude/settings.json` to be loaded

### 3. Agent Configurations via System Prompts ✅
**Finding**: Agent personalities CAN be loaded via `--append-system-prompt`
```bash
# This works to load agent configuration
claude -p --append-system-prompt "$(cat .claude/agents/agent-name.md)" "task"
```
- Agent markdown files can be injected as system prompts
- This provides the agent's instructions but not the full interactive experience
- Model selection can be controlled via `--model` flag

### 4. Session Logging ✅
**Finding**: All sessions are automatically logged
- Location: `~/.claude/projects/[project-path]/[session-id].jsonl`
- Contains full conversation history including tool calls
- Can be monitored in real-time with `tail -f`
- Provides audit trail for headless executions

### 5. MCP Servers ✅
**Finding**: MCP servers work in headless mode
- Can be configured via `--mcp-config` flag
- Tools accessible via `--allowed-tools "mcp__server__tool"`
- Debug output shows MCP server connections

## Limitations in Headless Mode

### What DOESN'T Work:
1. **Custom slash commands** - Not available
2. **Tool-level hooks** - PreToolUse/PostToolUse not triggered
3. **Agent switching** - No `/agents` command
4. **Memory management** - No `/memory` command
5. **Project-specific commands** - Not loaded

### What DOES Work:
1. **System prompt injection** - Full control via `--append-system-prompt`
2. **Tool restrictions** - Via `--allowed-tools` and `--disallowed-tools`
3. **Session tracking** - Automatic JSONL logging
4. **MCP servers** - Full functionality with proper config
5. **Permission controls** - All permission modes work
6. **SessionEnd hooks** - Execute on session completion for cleanup/export

## Recommended Approach for Headless Agents

### 1. Agent Configuration
```bash
# Load agent personality via system prompt
AGENT_PROMPT=$(cat .claude/agents/research-genius.md)
claude -p \
  --append-system-prompt "$AGENT_PROMPT" \
  --model opus \
  --session-id "$(uuidgen)" \
  "Your task here"
```

### 2. Custom Workflows
Instead of commands, use:
- Shell scripts that call claude with specific configurations
- System prompts that include workflow instructions
- Multiple sequential claude calls for complex workflows

### 3. Hook Alternative
Since hooks are unreliable, implement checks externally:
```bash
# Pre-execution checks
check_sensitive_files() {
  # Custom validation logic
}

# Run claude
claude -p "task"

# Post-execution actions
process_results() {
  # Custom post-processing
}
```

### 4. Command Alternative
Create wrapper scripts:
```bash
#!/bin/bash
# Custom command implementation
case "$1" in
  "context-prime")
    claude -p --append-system-prompt "$(cat context.md)" "$2"
    ;;
  "sdlc")
    claude -p --append-system-prompt "$(cat sdlc-prompt.md)" "$2"
    ;;
esac
```

## Conclusion

Headless Claude agents have significant limitations compared to interactive sessions:
- **Commands and hooks are primarily interactive features**
- **Agent configurations must be loaded via system prompts**
- **Workflows need external orchestration**

However, headless mode is still powerful for:
- **Automated tasks with predefined configurations**
- **Batch processing with specific agent personalities**
- **Parallel execution with session tracking**
- **Integration into CI/CD pipelines**

The key is to move configuration and orchestration logic outside of Claude into wrapper scripts and use Claude as a pure processing engine with carefully crafted system prompts and tool restrictions.
