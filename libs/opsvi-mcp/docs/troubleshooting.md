# Troubleshooting Guide - OPSVI MCP Servers

## Overview

This guide provides solutions to common issues encountered when running OPSVI MCP servers, particularly the Claude Code servers (V1, V2, V3).

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Server Startup Errors](#server-startup-errors)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [Integration Problems](#integration-problems)
6. [Debug Techniques](#debug-techniques)

## Installation Issues

### Module Not Found Errors

**Problem**: `ModuleNotFoundError: No module named 'fastmcp'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd /home/opsvi/master_root/libs/opsvi-mcp

# Install dependencies
pip install -r requirements.txt

# Or install the package
pip install -e .
```

### Import Errors

**Problem**: `ImportError: cannot import name 'ClaudeCodeV3Server'`

**Solution**:
The servers use lazy imports. Access through the parent module:
```python
# Wrong
from opsvi_mcp.servers.claude_code_v3 import ClaudeCodeV3Server

# Correct - servers are accessed via __main__.py
python -m opsvi_mcp.servers.claude_code_v3
```

## Server Startup Errors

### Context Bridge Pydantic Validation Error

**Problem**: 
```
pydantic.errors.ValidationError: Extra inputs are not permitted
```

**Solution**:
This was fixed by adding model configuration to allow extra fields:
```python
# In context_bridge/config.py
class ContextBridgeConfig(BaseSettings):
    model_config = {
        "env_prefix": "CONTEXT_BRIDGE_",
        "env_file": ".env",
        "extra": "ignore"  # This fixes the error
    }
```

### Claude Code V2 Asyncio Error

**Problem**: 
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solution**:
V2 must use direct MCP run instead of asyncio:
```python
# Wrong - in __main__.py
async def main():
    server = ClaudeCodeV2Server()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())  # This causes the error

# Correct
def main():
    server = ClaudeCodeV2Server()
    server.mcp.run()  # Direct call, no asyncio.run()

if __name__ == "__main__":
    main()
```

### JSON Output Corruption

**Problem**: 
```
Invalid JSON in MCP response
```

**Solution**:
All logging must go to stderr to avoid corrupting JSON-RPC protocol:
```python
# Wrong
print("Debug message")  # Goes to stdout, corrupts JSON

# Correct
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stderr)  # Use stderr
    ]
)
logger = logging.getLogger(__name__)
logger.debug("Debug message")  # Goes to stderr
```

## Runtime Errors

### Authentication Failures

**Problem**: `CLAUDE_CODE_TOKEN not set`

**Solution**:
```bash
# Set the environment variable
export CLAUDE_CODE_TOKEN="your-token-here"

# Or add to .env file
echo "CLAUDE_CODE_TOKEN=your-token-here" >> .env

# Verify it's set
echo $CLAUDE_CODE_TOKEN
```

### Timeout Errors

**Problem**: Jobs timing out before completion

**Solution for V1**:
```bash
# Increase timeout
export CLAUDE_TIMEOUT_SECONDS=600  # 10 minutes
```

**Solution for V2**:
```python
# Specify longer timeout when spawning
await spawn_agent({
    "task": "Complex task",
    "timeout": 1200000  # 20 minutes in milliseconds
})
```

**Solution for V3**:
```bash
# Enable adaptive timeout
export CLAUDE_ENABLE_ADAPTIVE_TIMEOUT=true
export CLAUDE_BASE_TIMEOUT=300000
export CLAUDE_MAX_TIMEOUT=1800000
```

### Recursion Depth Exceeded

**Problem**: `Maximum recursion depth exceeded`

**Solution**:
```bash
# V1/V2 - Limited to 3 levels
export CLAUDE_MAX_RECURSION=3

# V3 - Can go up to 5 levels
export CLAUDE_MAX_RECURSION_DEPTH=5
```

### Results Not Found

**Problem**: V2 results not appearing

**Solution**:
```bash
# Check results directory
ls -la /tmp/claude_results/

# Ensure directory exists and has permissions
mkdir -p /tmp/claude_results
chmod 755 /tmp/claude_results

# Set custom directory
export CLAUDE_RESULTS_DIR=/path/to/writable/dir
```

## Performance Issues

### High CPU Usage

**Problem**: Server using too much CPU

**Solution for V3**:
```bash
# Reduce concurrency
export CLAUDE_BASE_CONCURRENCY_D0=5  # Instead of 10
export CLAUDE_BASE_CONCURRENCY_D1=4  # Instead of 8
export CLAUDE_ADAPTIVE_CONCURRENCY=true
```

### Memory Exhaustion

**Problem**: Out of memory errors

**Solution**:
```bash
# Limit concurrent jobs
export CLAUDE_MAX_CONCURRENT_L1=5  # V2
export CLAUDE_MAX_TOTAL_JOBS=20    # V3

# Enable resource monitoring
export CLAUDE_ENABLE_RESOURCE_MONITOR=true
```

### Slow Execution

**Problem**: Tasks taking too long

**Solution for V3**:
```python
# Use RAPID mode for prototypes
result = await claude_run_v3(
    task="Quick prototype",
    mode="RAPID"  # Faster, less thorough
)

# Or let auto-detect choose
result = await claude_run_v3(
    task="Create draft implementation",
    auto_detect=True  # Will detect "draft" → RAPID
)
```

## Integration Problems

### MCP Configuration Not Working

**Problem**: Server not starting from MCP config

**Solution**:
Check your `.mcp.json` or `.cursor/mcp.json`:
```json
{
  "claude-code-v3": {
    "command": "python",
    "args": ["-m", "opsvi_mcp.servers.claude_code_v3"],
    "env": {
      "PYTHONPATH": "/home/opsvi/master_root/libs",
      "CLAUDE_CODE_TOKEN": "your-token"
    }
  }
}
```

### Cursor Agent Connection Issues

**Problem**: Can't connect to Cursor IDE

**Solution**:
```bash
# Check if Cursor is running
ps aux | grep -i cursor

# Verify WebSocket port
lsof -i :7070

# Try file-based communication instead
export CURSOR_COMM_METHOD=file
export CURSOR_WORKSPACE=/path/to/workspace
```

### OpenAI Codex API Errors

**Problem**: OpenAI API rate limits

**Solution**:
```bash
# Enable caching
export CODEX_ENABLE_CACHE=true
export CODEX_CACHE_DIR=/tmp/codex_cache

# Use different model
export CODEX_MODEL=gpt-3.5-turbo  # Instead of gpt-4
```

## Debug Techniques

### Enable Verbose Logging

```bash
# For all servers
export LOG_LEVEL=DEBUG

# V3 specific
export CLAUDE_DEBUG_MODE=true
export CLAUDE_LOG_AGENT_COMMUNICATION=true
```

### Check Server Logs

```bash
# V1 logs
tail -f /tmp/claude_code_server.log

# V2 logs
tail -f /tmp/claude_code_v2_server.log

# V3 logs
tail -f /tmp/claude_code_v3_server.log
```

### Test Individual Components

```python
# Test V3 mode detection
from opsvi_mcp.servers.claude_code_v3.mode_detector import ModeDetector

detector = ModeDetector()
mode = detector.detect("Create production-ready API")
print(f"Detected mode: {mode}")  # Should print: FULL_CYCLE
```

### Monitor System Resources

```bash
# Watch CPU and memory
htop

# Monitor specific process
pidof python | xargs -I {} top -p {}

# Check disk usage for results
du -sh /tmp/claude_results/
```

### Validate Configuration

```python
# Check V3 configuration
from opsvi_mcp.servers.claude_code_v3.config import config

print(f"Max recursion: {config.recursion.max_depth}")
print(f"Multi-agent enabled: {config.decomposition.enable_decomposition}")
print(f"Modes available: {config.modes}")
```

## Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `Tool not found: claude_run_v3` | V3 server not running | Start V3 server: `python -m opsvi_mcp.servers.claude_code_v3` |
| `Job timed out` | Task too complex for timeout | Increase timeout or use V3 with decomposition |
| `Cannot spawn more agents` | Concurrency limit reached | Wait for agents to complete or increase limits |
| `Invalid mode: UNKNOWN` | Typo in mode name | Use valid mode: RAPID, CODE, QUALITY, etc. |
| `Checkpoint not found` | Recovery attempted without checkpoint | Enable checkpointing: `CLAUDE_ENABLE_CHECKPOINTING=true` |
| `Agent communication failed` | Network/IPC issue | Check agent health, restart server |
| `Quality threshold not met` | Code didn't pass review | Lower threshold or improve task description |

## Getting Help

### Diagnostic Commands

```bash
# Check environment
env | grep CLAUDE

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test import
python -c "import opsvi_mcp; print(opsvi_mcp.__file__)"

# Check server status
curl http://localhost:8080/health  # If health endpoint enabled
```

### Collecting Debug Information

When reporting issues, include:

1. **Environment details**:
```bash
python --version
pip show fastmcp
env | grep -E '(CLAUDE|OPENAI|CURSOR)'
```

2. **Error logs**:
```bash
tail -n 100 /tmp/*_server.log
```

3. **Configuration**:
```bash
cat .mcp.json
cat .env
```

4. **Minimal reproduction**:
```python
# Provide minimal code that reproduces the issue
```

## Prevention Tips

1. **Always use stderr for logging** to prevent JSON corruption
2. **Set reasonable timeouts** based on task complexity
3. **Monitor resource usage** to prevent exhaustion
4. **Use V3 for production** due to better error handling
5. **Enable checkpointing** for long-running tasks
6. **Test configuration** before deploying
7. **Keep logs** for debugging

## Recovery Procedures

### When V2 Agents Are Stuck

```bash
# List all Python processes
ps aux | grep python

# Kill specific agent
kill -9 <PID>

# Clean up results directory
rm -rf /tmp/claude_results/*.partial
```

### When V3 Checkpoints Are Corrupted

```bash
# Clear checkpoints
rm -rf /tmp/checkpoints/*

# Restart with fresh state
export CLAUDE_CLEAR_CHECKPOINTS=true
python -m opsvi_mcp.servers.claude_code_v3
```

### When Nothing Works

```bash
# Full reset
pkill -f opsvi_mcp
rm -rf /tmp/claude_*
rm -rf /tmp/checkpoints
unset $(env | grep CLAUDE | cut -d= -f1)
source .env  # Reload clean environment
```

## Summary

Most issues fall into these categories:
1. **Configuration**: Wrong environment variables or paths
2. **Protocol**: JSON corruption from stdout logging
3. **Resources**: Timeouts, memory, or concurrency limits
4. **Versions**: Using wrong server version for the task

Always check logs first, verify configuration second, and test with simple tasks before complex ones.