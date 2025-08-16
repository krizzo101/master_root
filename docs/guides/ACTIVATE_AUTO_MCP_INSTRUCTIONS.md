# How to Activate and Use Auto MCP with Claude Code

## Current Status
✅ Setup is complete - all files are in place
⚠️ Aliases need to be loaded in your current shell
ℹ️ The system enhances Claude Code but doesn't replace how you start it

## Step-by-Step Activation

### Option 1: Quick Activation (Current Session Only)

```bash
# 1. Load the aliases into your current shell
source /home/opsvi/master_root/.claude/aliases.sh

# 2. Activate the auto MCP system
claude-auto-activate

# 3. Test that it's working
claude-auto-status

# 4. Start Claude Code normally
claude
```

### Option 2: Permanent Activation (Recommended)

```bash
# 1. Reload your shell configuration (already added by setup)
source ~/.bashrc

# 2. Now the aliases should work
claude-auto-status

# 3. Start Claude Code normally
claude
```

### Option 3: New Terminal Session

Simply open a new terminal and the aliases will be available:
```bash
# In new terminal:
claude-auto-activate
claude
```

## What Each Command Does

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `source ~/.bashrc` | Loads aliases into current shell | Once after setup |
| `claude-auto-activate` | Sets environment variables for auto MCP | Each session (or add to .bashrc) |
| `claude-auto-status` | Tests the selection logic | To verify it's working |
| `claude` | Starts Claude Code normally | After activation |

## How It Works with Claude Code

1. **You start Claude normally**: Just type `claude` as usual
2. **Behind the scenes**: Every prompt you type is automatically analyzed
3. **Automatic selection**: Based on complexity, the appropriate MCP server (V1/V2/V3) is selected
4. **Seamless experience**: You don't need to mention MCP servers at all

## Example Workflow

```bash
# One-time setup (you've already done this)
./setup_auto_mcp.sh

# Each new terminal session:
claude-auto-activate   # Or add this to your .bashrc for auto-activation

# Start Claude Code normally
claude

# Now when you type prompts, they're automatically routed:
# "Fix the login bug" → Automatically uses V1
# "Analyze all Python files" → Automatically uses V2  
# "Build production API" → Automatically uses V3
```

## Making Activation Permanent

To avoid running `claude-auto-activate` every session, add it to your `.bashrc`:

```bash
echo "" >> ~/.bashrc
echo "# Auto-activate Claude MCP on shell start" >> ~/.bashrc
echo "source /home/opsvi/master_root/.claude/activate_auto_mcp.sh 2>/dev/null" >> ~/.bashrc
```

## Testing the System

### Quick Test
```bash
# After activation, run:
claude-auto-status
```

Expected output:
```
Testing Automatic MCP Server Selection
==================================================
✅ Prompt: Fix the login bug...
   Expected: V1, Got: V1
...
Score: 6/7 (85.7%)
```

### Manual Test
```bash
# Test specific prompts
python3 -c "
import sys
sys.path.insert(0, '/home/opsvi/master_root/.claude')
from auto_mcp_middleware import analyze_user_prompt
result = analyze_user_prompt('Create a production-ready API')
print(f'Server selected: {result}')
"
```

## Troubleshooting

### "command not found" for aliases
```bash
# Solution: Source the aliases
source /home/opsvi/master_root/.claude/aliases.sh
```

### Environment variables not set
```bash
# Solution: Run activation
source /home/opsvi/master_root/.claude/activate_auto_mcp.sh
```

### Want to disable temporarily
```bash
claude-auto-off  # Disables auto MCP
claude-auto-on   # Re-enables auto MCP
```

## Important Notes

1. **Claude starts normally**: The activation doesn't start Claude, it just configures the environment
2. **Works transparently**: Once activated, you use Claude exactly as before
3. **No explicit mentions needed**: Don't say "use MCP" or "use V2" - it's automatic
4. **Session-based**: Activation is per terminal session unless added to .bashrc

## Quick Reference Card

```bash
# Must run once per session (or add to .bashrc):
claude-auto-activate

# Then use Claude normally:
claude

# Available commands after activation:
claude-auto-on        # Enable auto MCP
claude-auto-off       # Disable auto MCP  
claude-auto-status    # Test selection logic
claude-auto-config    # Edit configuration
claude-auto-logs      # View logs
claude-auto-metrics   # View usage stats
```

## Current Session Quick Fix

Right now, to get everything working in your current terminal:

```bash
# Run these three commands:
source /home/opsvi/master_root/.claude/aliases.sh
claude-auto-activate
claude

# Now Claude will have automatic MCP server selection!
```

The system is ready - it just needs to be activated in your shell session!