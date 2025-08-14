# Auto MCP Project Paths Reference

## Project Root Configuration

All Auto MCP components are localized to the project root to ensure portability and avoid polluting the user's home directory.

```bash
PROJECT_ROOT="/home/opsvi/master_root"
```

## Directory Structure

```
/home/opsvi/master_root/
├── .claude/                           # Auto MCP configuration directory
│   ├── config.json                   # Main configuration file
│   ├── auto_mcp_middleware.py        # Middleware for prompt analysis
│   ├── setup_auto_mcp.sh            # Setup and installation script
│   ├── activate_auto_mcp.sh         # Activation script (generated)
│   ├── init_auto_mcp.py             # Python initialization (generated)
│   ├── test_auto_mcp.py             # Test script (generated)
│   └── aliases.sh                    # Shell aliases (generated)
│
├── libs/opsvi-mcp/                   # MCP library and documentation
│   ├── CLAUDE.md                    # Quick reference guide
│   ├── CLAUDE_CODE_AGENT_GUIDANCE.md # Comprehensive guidance
│   ├── CLAUDE_CODE_SCENARIOS.md     # Real-world scenarios
│   ├── CLAUDE_CODE_USE_CASES.md     # Use case documentation
│   ├── AGENT_PROFILE.md             # Agent behavior profile
│   └── SYSTEM_PROMPT.md             # System-level directives
│
└── AUTO_MCP_INTEGRATION_GUIDE.md     # Integration documentation
```

## Key Paths

### Configuration Files
- **Main Config**: `/home/opsvi/master_root/.claude/config.json`
- **Middleware**: `/home/opsvi/master_root/.claude/auto_mcp_middleware.py`
- **Setup Script**: `/home/opsvi/master_root/.claude/setup_auto_mcp.sh`

### Guidance Documents
- **Quick Ref**: `/home/opsvi/master_root/libs/opsvi-mcp/CLAUDE.md`
- **Agent Guide**: `/home/opsvi/master_root/libs/opsvi-mcp/CLAUDE_CODE_AGENT_GUIDANCE.md`
- **Scenarios**: `/home/opsvi/master_root/libs/opsvi-mcp/CLAUDE_CODE_SCENARIOS.md`
- **Use Cases**: `/home/opsvi/master_root/libs/opsvi-mcp/CLAUDE_CODE_USE_CASES.md`

### Generated Files (Created by setup script)
- **Activation**: `/home/opsvi/master_root/.claude/activate_auto_mcp.sh`
- **Init Python**: `/home/opsvi/master_root/.claude/init_auto_mcp.py`
- **Test Script**: `/home/opsvi/master_root/.claude/test_auto_mcp.py`
- **Aliases**: `/home/opsvi/master_root/.claude/aliases.sh`

### Runtime Files (Created during operation)
- **Logs**: `/tmp/claude_auto_mcp.log`
- **Metrics**: `/tmp/claude_mcp_metrics.json`
- **Results**: `/tmp/claude_results/` (V2 server output)

## Environment Variables

When activated, these environment variables are set:

```bash
CLAUDE_PROJECT_ROOT="/home/opsvi/master_root"
CLAUDE_AUTO_MCP="true"
CLAUDE_MCP_THRESHOLD="2"
CLAUDE_DEFAULT_SERVER="V1"
CLAUDE_GUIDANCE_PATH="/home/opsvi/master_root/libs/opsvi-mcp"
CLAUDE_CONFIG_PATH="/home/opsvi/master_root/.claude/config.json"
CLAUDE_MIDDLEWARE_PATH="/home/opsvi/master_root/.claude/auto_mcp_middleware.py"
```

## Shell Aliases

After setup, these aliases are available:

```bash
claude-auto-on       # Enable automatic MCP
claude-auto-off      # Disable automatic MCP
claude-auto-status   # Test server selection
claude-auto-config   # Edit configuration
claude-auto-logs     # View live logs
claude-auto-metrics  # View usage metrics
claude-auto-activate # Activate the system
```

## Installation Commands

```bash
# One-time setup (run from anywhere)
bash /home/opsvi/master_root/.claude/setup_auto_mcp.sh

# Activation (run each session or add to .bashrc)
source /home/opsvi/master_root/.claude/activate_auto_mcp.sh
# OR use the alias after setup:
claude-auto-activate

# Test the system
python3 /home/opsvi/master_root/.claude/test_auto_mcp.py
# OR use the alias:
claude-auto-status
```

## Changing Project Root

If you need to move the project to a different location:

1. Edit the `PROJECT_ROOT` variable at the top of:
   - `/new/location/.claude/setup_auto_mcp.sh`

2. Re-run the setup script:
   ```bash
   bash /new/location/.claude/setup_auto_mcp.sh
   ```

3. The script will update all paths automatically.

## Integration Points

### For Python Scripts
```python
import sys
sys.path.insert(0, "/home/opsvi/master_root/.claude")
from auto_mcp_middleware import analyze_user_prompt
```

### For IDE Configuration
Add to `.cursor/mcp.json` or similar:
```json
{
  "auto_mcp": {
    "middleware_path": "/home/opsvi/master_root/.claude/auto_mcp_middleware.py",
    "config_path": "/home/opsvi/master_root/.claude/config.json",
    "enabled": true
  }
}
```

## Benefits of Project-Local Configuration

1. **Portability**: Entire configuration moves with the project
2. **Isolation**: Doesn't affect user's home directory or other projects
3. **Version Control**: Can be committed with the project
4. **Multi-Project**: Different projects can have different configurations
5. **Easy Cleanup**: Simply delete the project directory to remove everything

## Troubleshooting Paths

If paths are not working:

1. Verify project root exists:
   ```bash
   ls -la /home/opsvi/master_root/
   ```

2. Check configuration is in place:
   ```bash
   ls -la /home/opsvi/master_root/.claude/
   ```

3. Verify environment variables:
   ```bash
   echo $CLAUDE_PROJECT_ROOT
   echo $CLAUDE_CONFIG_PATH
   ```

4. Test middleware directly:
   ```bash
   python3 /home/opsvi/master_root/.claude/test_auto_mcp.py
   ```

All paths are hardcoded to `/home/opsvi/master_root` for consistency and reliability within this project environment.