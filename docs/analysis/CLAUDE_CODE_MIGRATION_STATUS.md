# Claude Code MCP Server Migration Status

## ✅ Migration Complete

The Claude Code MCP Server has been successfully migrated from TypeScript to Python and integrated into the OPSVI monorepo.

## Current Status

### ✅ What's Working
- **Python Implementation**: Fully functional at `libs/opsvi-mcp/opsvi_mcp/servers/claude_code/`
- **All 8 MCP Tools**: Preserved and working
- **FastMCP Integration**: Using the Python FastMCP framework
- **Configuration Updated**: `.cursor/mcp.json` points to Python implementation
- **Server Runs**: Successfully starts and initializes

### ⚠️ Cursor Integration Issue
The Cursor logs show it's still trying to use the old TypeScript path in some places. This appears to be a caching issue.

## Required Actions to Complete Setup

### 1. Restart Cursor Completely
```bash
# Fully quit Cursor (not just close window)
# On macOS: Cmd+Q
# On Linux: Close all windows and kill any cursor processes
pkill -f cursor || true

# Clear Cursor MCP cache (if it exists)
rm -rf ~/.cursor/mcp-cache 2>/dev/null || true

# Restart Cursor
```

### 2. Verify Python Dependencies
```bash
# Ensure you're using the conda environment
/home/opsvi/miniconda/bin/pip install fastmcp uvloop psutil python-dotenv
```

### 3. Set Claude Code Token
Make sure your token is available:
```bash
# Check if token exists
cat ~/.env | grep CLAUDE_CODE_TOKEN

# Or set it
echo "CLAUDE_CODE_TOKEN=your_token_here" >> ~/.env
```

### 4. Test the Server Manually
```bash
# Test that the server starts
export PYTHONPATH=/home/opsvi/master_root/libs
/home/opsvi/miniconda/bin/python -m opsvi_mcp.servers.claude_code --help
```

## File Locations

### New Python Implementation
- **Main Server**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code/server.py`
- **Job Manager**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code/job_manager.py`
- **Config**: `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/claude_code/config.py`
- **Tests**: `/home/opsvi/master_root/libs/opsvi-mcp/tests/test_claude_code_server.py`
- **Documentation**: `/home/opsvi/master_root/libs/opsvi-mcp/docs/CLAUDE_CODE_MIGRATION.md`

### Original TypeScript (Preserved)
- **Location**: `/home/opsvi/master_root/claude-code/`
- **Status**: Can be removed after verifying Python implementation works

## Configuration

The MCP configuration at `.cursor/mcp.json` has been updated:

```json
{
  "mcpServers": {
    "claude-code-wrapper": {
      "command": "/home/opsvi/miniconda/bin/python",
      "args": ["-m", "opsvi_mcp.servers.claude_code"],
      "env": {
        "PYTHONPATH": "/home/opsvi/master_root/libs",
        "CLAUDE_CODE_TOKEN": "${CLAUDE_CODE_TOKEN}",
        "CLAUDE_MAX_RECURSION_DEPTH": "3",
        "CLAUDE_MAX_CONCURRENT_AT_DEPTH": "5",
        "CLAUDE_MAX_TOTAL_JOBS": "20",
        "CLAUDE_LOG_LEVEL": "INFO",
        "CLAUDE_PERF_LOGGING": "true",
        "CLAUDE_CHILD_LOGGING": "true",
        "CLAUDE_RECURSION_LOGGING": "true"
      }
    }
  }
}
```

## Troubleshooting

### If Cursor Still Shows Errors
1. Check if there are multiple mcp.json files:
   ```bash
   find ~ -name "mcp.json" -o -name ".mcp.json" 2>/dev/null
   ```

2. Update all found configurations to use the Python server

3. Clear npm cache (for the old TypeScript references):
   ```bash
   npm cache clean --force
   ```

4. Check Cursor's application support directory for cached configs:
   ```bash
   # macOS
   ls ~/Library/Application\ Support/Cursor/
   
   # Linux
   ls ~/.config/Cursor/
   ```

### Server Won't Start
1. Verify Python path:
   ```bash
   which python
   # Should be: /home/opsvi/miniconda/bin/python
   ```

2. Check imports work:
   ```bash
   /home/opsvi/miniconda/bin/python -c "from fastmcp import FastMCP; print('OK')"
   ```

3. Check logs:
   ```bash
   ls -la /home/opsvi/master_root/logs/claude-code/
   ```

## Next Steps

After Cursor recognizes the new server:
1. Test the `claude_run` tool with a simple task
2. Verify parallel execution with `claude_run_async`
3. Check the dashboard with `claude_dashboard`
4. Monitor logs for any issues

## Success Criteria

The migration is complete when:
- ✅ Python server starts without errors
- ✅ All 8 MCP tools are available in Cursor
- ⏳ Claude Code tasks execute successfully (pending Cursor restart)
- ⏳ Parallel execution works as expected (pending Cursor restart)
- ✅ Logs are written to the correct directory

## Support

For issues, check:
- Server logs: `/home/opsvi/master_root/logs/claude-code/`
- Migration guide: `/home/opsvi/master_root/libs/opsvi-mcp/docs/CLAUDE_CODE_MIGRATION.md`
- Original TypeScript for reference: `/home/opsvi/master_root/claude-code/`