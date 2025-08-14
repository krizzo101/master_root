# Testing Claude's Integration with Auto MCP

## The Solution: CLAUDE.md

Claude automatically reads `CLAUDE.md` files in the project root when starting a session. This file now contains:
1. Instructions to use the auto MCP system
2. Decision criteria for each server
3. The actual MCP tool names to use

## How Claude Should Now Behave

When you start a new Claude session in this directory (`/home/opsvi/master_root`), Claude will:

1. **Read CLAUDE.md** automatically
2. **See the instructions** to check task complexity
3. **Use the appropriate MCP tools** based on the task

## Test Prompts to Verify It's Working

Start a NEW Claude session (important - needs to read the updated CLAUDE.md):
```bash
cd /home/opsvi/master_root
claude
```

### Test 1: Debug Task (Should Use V1)
```
Debug why the authentication function fails
```

**Expected Behavior:**
- Claude should use `mcp__claude-code-wrapper__claude_run`
- You'll see Claude using the tool to debug
- No need to mention MCP

### Test 2: Bulk Analysis (Should Use V2)
```
Analyze all Python files for unused imports
```

**Expected Behavior:**
- Claude should use `mcp__claude-code-v2__spawn_parallel_agents`
- Might mention parallel processing
- Handles multiple files efficiently

### Test 3: Production System (Should Use V3)
```
Create a production-ready REST API with authentication
```

**Expected Behavior:**
- Claude should use `mcp__claude-code-v3__claude_run_v3`
- Comprehensive approach with tests
- High quality output

### Test 4: Simple Question (No MCP)
```
What is a Python decorator?
```

**Expected Behavior:**
- Direct answer without using MCP tools
- Simple explanation

## How to Verify Claude is Following Instructions

### Option 1: Watch Claude's Tool Usage
When Claude uses MCP tools, you'll see something like:
```
● mcp__claude-code-wrapper__claude_run
  ⎿ Debugging the authentication function...
```

### Option 2: Check If Claude Mentions the System
Ask Claude directly:
```
Are you using the auto MCP system described in CLAUDE.md?
```

Claude should confirm it's aware of and using the system.

### Option 3: Compare Behavior
Try the same prompt with and without CLAUDE.md:
- With CLAUDE.md: Should use appropriate MCP tools
- Without (different directory): Won't use MCP unless asked

## The Key Difference

### Before (Without CLAUDE.md):
```
User: "Debug my login function"
Claude: "I'll help you debug the login function. Let me search for it..."
[Uses basic search tools]
```

### After (With CLAUDE.md):
```
User: "Debug my login function"
Claude: [Reads CLAUDE.md, sees "debug" → V1]
● mcp__claude-code-wrapper__claude_run
  ⎿ Debugging your login function...
```

## Important Notes

1. **New Session Required**: Claude reads CLAUDE.md when starting, so you need a fresh session
2. **Project Directory**: Must start Claude in `/home/opsvi/master_root` for it to find CLAUDE.md
3. **Automatic**: You don't need to mention MCP - Claude should follow the instructions
4. **Tool Names**: Claude now knows the exact tool names to use

## Quick Verification Script

Run this to confirm the middleware is working:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/opsvi/master_root/.claude')
from auto_mcp_middleware import analyze_user_prompt

prompts = [
    "Debug the login error",
    "Analyze all files for security",  
    "Build a production API"
]

for p in prompts:
    result = analyze_user_prompt(p)
    print(f"'{p}' → Server: {result.get('server', 'None')}")
EOF
```

## Summary

The integration now works through:
1. **CLAUDE.md** - Instructions Claude reads automatically
2. **Middleware** - Decision logic Claude can check
3. **MCP Tools** - The actual tools Claude will use

Claude should now automatically select and use the appropriate MCP server based on your task complexity without you needing to specify it!