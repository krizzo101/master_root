# Testing Auto MCP in Live Claude Session

## How to Confirm It's Working

### 1. First, Check Your Environment (Before Starting Claude)

```bash
# Run this BEFORE starting claude to confirm activation:
echo "Auto MCP Enabled: $CLAUDE_AUTO_MCP"
echo "Config Path: $CLAUDE_CONFIG_PATH"
echo "Project Root: $CLAUDE_PROJECT_ROOT"
```

You should see:
```
Auto MCP Enabled: true
Config Path: /home/opsvi/master_root/.claude/config.json
Project Root: /home/opsvi/master_root
```

### 2. Check Logs Are Being Created

```bash
# Check if the log file exists and is being written to:
ls -la /tmp/claude_auto_mcp.log
tail -5 /tmp/claude_auto_mcp.log
```

---

## Test Prompts to Enter in Claude

Once you've started Claude (`claude` command), try these test prompts in sequence:

### Test 1: V1 Selection (Debugging Task)
**Enter this prompt:**
```
Debug why my login function returns null
```

**What to Look For:**
- Claude should respond naturally about debugging
- Check the log afterward: `tail -10 /tmp/claude_auto_mcp.log`
- You should see: `INFO - Auto-selected V1 for prompt (score: X)`

**How You Know It Worked:**
- Claude handles the debugging task
- No mention of "I'll use MCP" needed from you
- Log shows V1 was auto-selected

---

### Test 2: V2 Selection (Parallel Task)
**Enter this prompt:**
```
Analyze all Python files in the project for security vulnerabilities
```

**What to Look For:**
- Claude might mention "I'll handle this in parallel" or "I'll analyze multiple files"
- Check log: `tail -10 /tmp/claude_auto_mcp.log`
- Should see: `INFO - Auto-selected V2 for prompt (score: X)`

**How You Know It Worked:**
- The task involves multiple files
- Log confirms V2 selection
- Claude processes files in parallel (faster)

---

### Test 3: V3 Selection (Production Task)
**Enter this prompt:**
```
Create a production-ready REST API with authentication and tests
```

**What to Look For:**
- Claude might mention ensuring "production quality" or "comprehensive implementation"
- Check log: `tail -10 /tmp/claude_auto_mcp.log`
- Should see: `INFO - Auto-selected V3 for prompt (score: X)`

**How You Know It Worked:**
- Claude takes a comprehensive approach
- Includes tests and documentation
- Log confirms V3 selection

---

### Test 4: No MCP Needed (Simple Question)
**Enter this prompt:**
```
What is the difference between let and const in JavaScript?
```

**What to Look For:**
- Claude answers directly without using MCP tools
- Check log: `tail -10 /tmp/claude_auto_mcp.log`
- Should see: `below_threshold` or no new entry

**How You Know It Worked:**
- Simple question answered directly
- No MCP server engaged (as expected)

---

## Live Monitoring Commands

### While Claude is Running (in another terminal):

```bash
# Watch the logs in real-time:
tail -f /tmp/claude_auto_mcp.log

# Check metrics after a few prompts:
cat /tmp/claude_mcp_metrics.json | python3 -m json.tool
```

Expected metrics output:
```json
{
  "timestamp": "2024-01-13T...",
  "metrics": {
    "total_prompts": 4,
    "mcp_engaged": 3,
    "server_usage": {
      "V1": 1,
      "V2": 1,
      "V3": 1
    },
    "fallbacks": 0
  }
}
```

---

## Visual Indicators in Claude's Responses

### When V1 is Auto-Selected:
- Claude debugs or investigates step-by-step
- Synchronous, immediate responses
- Good for: debugging, simple fixes, investigations

### When V2 is Auto-Selected:
- Claude mentions parallel processing
- Multiple independent tasks handled
- Good for: analyzing many files, batch operations

### When V3 is Auto-Selected:
- Claude takes comprehensive approach
- Mentions quality, tests, documentation
- Good for: production systems, complex features

---

## Quick Verification Script

Create and run this test script to verify everything is connected:

```bash
cat > /tmp/test_mcp_live.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
import json

# Add middleware to path
sys.path.insert(0, "/home/opsvi/master_root/.claude")

try:
    from auto_mcp_middleware import analyze_user_prompt, get_metrics
    
    print("✅ Middleware loaded successfully")
    print(f"✅ Config found at: {os.path.exists('/home/opsvi/master_root/.claude/config.json')}")
    
    # Test a prompt
    test_prompt = "Debug the authentication error"
    result = analyze_user_prompt(test_prompt)
    
    print(f"\nTest prompt: '{test_prompt}'")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Show metrics
    metrics = get_metrics()
    print(f"\nCurrent metrics: {json.dumps(metrics, indent=2)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
EOF

python3 /tmp/test_mcp_live.py
```

---

## Complete Test Sequence

1. **Before Claude**: Run verification script above
2. **Start Claude**: `claude`
3. **Enter test prompts** in this order:
   - "Fix the null pointer error in line 45" → Should use V1
   - "Review all API endpoints for security issues" → Should use V2  
   - "Build a production-ready user management system" → Should use V3
   - "What is Python?" → Should NOT use MCP

4. **Check the results**:
```bash
# See what happened:
echo "=== Last 20 log entries ===" 
tail -20 /tmp/claude_auto_mcp.log

echo -e "\n=== Current Metrics ===" 
cat /tmp/claude_mcp_metrics.json | python3 -m json.tool

echo -e "\n=== Server Selection Summary ===" 
grep "Auto-selected" /tmp/claude_auto_mcp.log | tail -5
```

---

## Success Indicators

✅ **It's working if you see:**
1. Log entries showing "Auto-selected V1/V2/V3" for different prompts
2. Metrics showing different servers being used
3. Claude handling tasks appropriately without you mentioning MCP
4. Different response patterns for different complexity tasks

❌ **It's NOT working if:**
1. No log file at `/tmp/claude_auto_mcp.log`
2. No entries being added when you enter prompts
3. Metrics stay at zero
4. Claude asks you which MCP server to use

---

## Troubleshooting Commands

If it doesn't seem to be working:

```bash
# 1. Verify environment is set:
env | grep CLAUDE

# 2. Check if middleware is accessible:
python3 -c "import sys; sys.path.insert(0, '/home/opsvi/master_root/.claude'); from auto_mcp_middleware import middleware; print('✅ Middleware accessible')"

# 3. Test middleware directly:
python3 /home/opsvi/master_root/.claude/test_auto_mcp.py

# 4. Check Claude is using the config:
# (Look for any MCP-related initialization in Claude's startup)
```

---

## Expected Behavior Summary

| Your Prompt | Auto-Selected | You'll Notice |
|------------|---------------|---------------|
| "Debug this error" | V1 | Step-by-step debugging |
| "Analyze all files" | V2 | Parallel processing mentioned |
| "Create production API" | V3 | Comprehensive approach with tests |
| "What is X?" | None | Direct answer, no MCP |

The key is: **You never mention MCP servers, but they're being used automatically based on your task complexity!**