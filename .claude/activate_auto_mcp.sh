#!/bin/bash
# Activate automatic MCP server detection

# Project root
export CLAUDE_PROJECT_ROOT="/home/opsvi/master_root"

# MCP configuration
export CLAUDE_AUTO_MCP=true
export CLAUDE_MCP_THRESHOLD=2
export CLAUDE_DEFAULT_SERVER=V1
export CLAUDE_GUIDANCE_PATH="/home/opsvi/master_root/libs/opsvi-mcp"
export CLAUDE_CONFIG_PATH="/home/opsvi/master_root/.claude/config.json"
export CLAUDE_MIDDLEWARE_PATH="/home/opsvi/master_root/.claude/auto_mcp_middleware.py"

# Run Python initialization
python3 "/home/opsvi/master_root/.claude/init_auto_mcp.py"

echo "✅ Automatic MCP server detection activated"
echo ""
echo "Configuration:"
echo "  - Project Root: $CLAUDE_PROJECT_ROOT"
echo "  - Auto MCP: $CLAUDE_AUTO_MCP"
echo "  - Threshold: $CLAUDE_MCP_THRESHOLD"
echo "  - Default Server: $CLAUDE_DEFAULT_SERVER"
echo "  - Config Path: $CLAUDE_CONFIG_PATH"
echo ""
echo "The system will now automatically:"
echo "  1. Analyze every prompt for complexity"
echo "  2. Select appropriate MCP server (V1/V2/V3)"
echo "  3. Execute with optimal configuration"
echo "  4. Fallback gracefully if needed"
echo ""
echo "No manual MCP server selection required!"
