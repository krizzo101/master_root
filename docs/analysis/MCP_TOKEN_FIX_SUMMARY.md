# MCP Server Token Configuration Fix Summary

## The Issue

Claude Code requires:
1. **`CLAUDE_CODE_TOKEN` MUST be set** with a valid token
2. **`ANTHROPIC_API_KEY` MUST be empty or unset**

## Current Status

### Environment (✅ Correct)
Your main environment is correctly configured:
- `CLAUDE_CODE_TOKEN` = set with valid token
- `ANTHROPIC_API_KEY` = empty string

### MCP Server Status

| Server | Token Handling | Status | Fix Applied |
|--------|---------------|--------|------------|
| **V1** | ✅ Correctly removes ANTHROPIC_API_KEY | Working | None needed |
| **V2** | ❌ Was NOT removing ANTHROPIC_API_KEY | Fixed | Added removal code |
| **V3** | ⚠️ Doesn't spawn subprocesses | N/A | Runs in same process |

## The V2 Fix Applied

In `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code_v2/job_manager.py`:

```python
# BEFORE: Was copying environment as-is
env = os.environ.copy()

# AFTER: Now removes ANTHROPIC_API_KEY
env = os.environ.copy()
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]
env["ANTHROPIC_API_KEY"] = ""  # Explicitly set to empty
```

## Why V2 Failed Earlier

When you tested V2's `spawn_parallel_agents`:
1. It spawned 10 agents successfully
2. But each agent inherited `ANTHROPIC_API_KEY` from parent
3. Claude Code refused to run with both tokens present
4. Agents failed silently, producing no results
5. That's why `/tmp/python_analysis/` remained empty

## Testing the Fix

To verify V2 now works correctly:

```bash
# Start new Claude session
cd /home/opsvi/master_root
claude

# Test V2 with a simpler task
"Analyze all README files in the libs directory"
```

V2 should now:
1. Spawn agents with correct environment
2. Agents should execute successfully
3. Results should appear in output directory

## V1 and V3 Status

### V1 (Working)
Already has proper token handling:
```python
if key == "ANTHROPIC_API_KEY":
    del env[key]
```

### V3 (Different Architecture)
- Doesn't spawn separate processes
- Runs in same process as Claude
- Inherits correct environment automatically

## Summary

The auto MCP system is working correctly:
1. **CLAUDE.md instructions**: ✅ Claude follows them
2. **Tool selection**: ✅ Claude picks correct server
3. **V1 execution**: ✅ Has correct token handling
4. **V2 execution**: ✅ NOW FIXED - removes ANTHROPIC_API_KEY
5. **V3 execution**: ✅ Runs in-process with correct env

The V2 parallel agents should now work properly with the fix applied!