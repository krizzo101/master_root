# Environment Variable Fix Summary

## Critical Fix Applied
All Claude Code MCP servers (V1, V2, V3) now properly handle environment variables to ensure Claude Code uses user authentication instead of API tokens.

## What Was Fixed

### The Problem
Claude Code can authenticate in two ways:
1. **User Authentication** (via `CLAUDE_CODE_TOKEN`) - Uses browser-based auth
2. **API Token** (via `ANTHROPIC_API_KEY`) - Direct API access

If `ANTHROPIC_API_KEY` is present, Claude Code prefers it over user auth, which can cause issues.

### The Solution
All servers now:
1. **SET** `CLAUDE_CODE_TOKEN` for user authentication
2. **DELETE** `ANTHROPIC_API_KEY` to prevent API token usage
3. **REMOVE** any other conflicting `ANTHROPIC_*` variables
4. **CLEAN** conflicting `CLAUDE_*` variables (keeping only `CLAUDE_CODE_TOKEN`)

## Implementation Details

### V1 Server (Already Correct)
```python
# From job_manager.py
env = os.environ.copy()
if config.claude_code_token:
    env["CLAUDE_CODE_TOKEN"] = config.claude_code_token

# Remove conflicting variables
for key in list(env.keys()):
    if (key.startswith("CLAUDE_") and key != "CLAUDE_CODE_TOKEN") or key == "ANTHROPIC_API_KEY":
        del env[key]
```

### V2 Server (Fixed)
Two locations updated:
1. **Parent process** (spawning agents):
```python
env = os.environ.copy()
# Remove ANTHROPIC_API_KEY
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]
# Set Claude Code token
env["CLAUDE_CODE_TOKEN"] = self.config.claude_token or ""
```

2. **Child script** (executing Claude):
```python
env = os.environ.copy()
if claude_token:
    env["CLAUDE_CODE_TOKEN"] = claude_token
# Remove ANTHROPIC_API_KEY
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]
```

### V3 Server (Fixed)
```python
env = os.environ.copy()
# Ensure CLAUDE_CODE_TOKEN is set
if claude_token:
    env["CLAUDE_CODE_TOKEN"] = claude_token
# Remove ANTHROPIC_API_KEY
if "ANTHROPIC_API_KEY" in env:
    del env["ANTHROPIC_API_KEY"]
# Clean other variables
for key in list(env.keys()):
    if key.startswith("ANTHROPIC_") or (key.startswith("CLAUDE_") and key != "CLAUDE_CODE_TOKEN"):
        del env[key]
```

## Why This Matters

1. **Correct Authentication**: Forces Claude Code to use user authentication
2. **No API Conflicts**: Prevents accidental API token usage
3. **Consistent Behavior**: All spawned processes use the same auth method
4. **Cost Control**: User auth may have different quotas/costs than API access
5. **Security**: Prevents leaking API keys to child processes

## Testing Verification

To verify the fix works:

```bash
# Set both variables
export ANTHROPIC_API_KEY="test_key"
export CLAUDE_CODE_TOKEN="actual_token"

# Run V2 test
mcp__claude-code-v2__spawn_agent(task="Test auth")

# Check spawned process environment
# Should see: CLAUDE_CODE_TOKEN set, ANTHROPIC_API_KEY removed
```

## Environment Variables After Fix

### What Gets Passed to Claude Code
✅ `CLAUDE_CODE_TOKEN` - User authentication token
✅ `PATH`, `HOME`, etc. - Standard system variables
✅ MCP-related configs (if needed)

### What Gets Removed
❌ `ANTHROPIC_API_KEY` - API token (conflicts with user auth)
❌ `ANTHROPIC_*` - Any Anthropic-specific variables
❌ `CLAUDE_*` - Other Claude variables (except TOKEN)

## Summary

All three Claude Code MCP servers now:
1. Properly set `CLAUDE_CODE_TOKEN` for authentication
2. Remove `ANTHROPIC_API_KEY` to prevent conflicts
3. Clean up any other potentially conflicting variables
4. Pass a clean environment to Claude Code processes

This ensures Claude Code always uses the intended authentication method (user auth via token) rather than accidentally falling back to API token authentication.