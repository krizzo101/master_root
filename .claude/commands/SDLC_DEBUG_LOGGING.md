# SDLC Debug Logging System

## What Will Be Logged

### 1. **Execution Logs** (`{phase}_{timestamp}_execution.json`)
Structured JSON containing:
- Every step with timestamp
- MCP task descriptions sent
- MCP parameters used
- Tool calls made by the agent
- Errors and exceptions
- Files created/modified
- Complete execution timeline

### 2. **Debug Logs** (`{phase}_{timestamp}_debug.log`)
Human-readable detailed logging:
- Line-by-line execution trace
- All MCP communication
- State changes
- Error messages with stack traces
- Git operations
- File system changes

### 3. **State Logs** (`{phase}_{timestamp}_state.json`)
Project state snapshots:
- Complete file listing before execution
- Complete file listing after execution
- Git status at each point
- File sizes and modification times
- Diff of changes

### 4. **Summary Logs** (`{phase}_{timestamp}_summary.json`)
High-level execution summary:
- Phase name and timing
- Step count
- Error count
- Files created/modified count
- Links to all other logs

## Where Logs Are Stored

**Primary Location**: `/home/opsvi/master_root/.sdlc-logs/`

Directory structure:
```
.sdlc-logs/
├── session_YYYYMMDD_HHMMSS.log          # Overall session
├── discovery_YYYYMMDD_HHMMSS_execution.json
├── discovery_YYYYMMDD_HHMMSS_debug.log
├── discovery_YYYYMMDD_HHMMSS_state.json
├── discovery_YYYYMMDD_HHMMSS_summary.json
├── design_YYYYMMDD_HHMMSS_execution.json
├── design_YYYYMMDD_HHMMSS_debug.log
└── ... (similar for each phase)
```

## What Gets Tracked

### Pre-Execution
- Current directory structure
- Git branch and status
- Existing files and sizes
- Environment state

### During Execution
- Every MCP tool call
- Parameters sent to claude-code
- Agent profile loading
- File operations (create/read/write/delete)
- Git operations (add/commit/branch)
- Error conditions
- Timeouts or failures

### Post-Execution
- Final directory structure
- Files created or modified
- Git diff of changes
- Success/failure status
- Duration and performance

## How to Use

### Option 1: Shell Wrapper
```bash
bash .claude/commands/sdlc-phase-executor.sh discovery apps/hello-cli "Execute discovery phase"
```

### Option 2: Python Debug Wrapper
```python
python .claude/commands/sdlc_mcp_debug_wrapper.py discovery apps/hello-cli "Execute discovery phase"
```

### Option 3: Direct with Logging
When calling MCP directly, ensure verbose logging:
```python
result = mcp__claude-code-wrapper__claude_run(
    task="...",
    outputFormat="json",
    verbose=True  # CRITICAL: Enable verbose output
)
# Log the result immediately
with open(log_file, 'w') as f:
    json.dump(result, f, indent=2)
```

## Viewing Logs

### Real-time Monitoring
```bash
# Watch execution log
tail -f .sdlc-logs/discovery_*_debug.log

# Monitor state changes
watch -n 1 'ls -la apps/hello-cli/'

# Track git changes
watch -n 1 'git status --short'
```

### Post-Execution Analysis
```bash
# View summary
cat .sdlc-logs/*_summary.json | jq .

# Check errors
grep ERROR .sdlc-logs/*_debug.log

# See all files created
jq '.files_created' .sdlc-logs/*_execution.json
```

## Critical Information Captured

1. **Task Sent to MCP**: Exact task description
2. **Agent Response**: Full JSON response
3. **Tool Usage**: Every tool called by agent
4. **File Operations**: Every file touched
5. **Git Operations**: Every commit made
6. **Errors**: Complete error traces
7. **Timing**: Duration of each step
8. **State Changes**: Before/after snapshots

## Debugging Failed Executions

If an execution fails:
1. Check `*_summary.json` for error count
2. Look in `*_debug.log` for ERROR entries
3. Review `*_execution.json` for last successful step
4. Compare `*_state.json` to see partial changes
5. Use timestamps to correlate with MCP server logs

## Integration with MCP

The debug wrapper will:
1. Capture the task before sending to MCP
2. Log the MCP response completely
3. Track any timeout or error conditions
4. Save partial results even if execution fails
5. Maintain audit trail of all operations

This ensures **complete visibility** into what the claude-code agent is doing at every step.
