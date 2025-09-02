#!/bin/bash
# Setup script for Agent Orchestrator

echo "Agent Orchestrator Setup"
echo "========================"

# Check for claude CLI
if ! command -v claude &> /dev/null; then
    echo "❌ Error: 'claude' CLI not found in PATH"
    echo "   Please install Claude CLI first"
    exit 1
fi
echo "✅ Claude CLI found"

# Check for token
if [ -z "$CLAUDE_CODE_TOKEN" ]; then
    echo "❌ Warning: CLAUDE_CODE_TOKEN not set"
    echo "   Please set: export CLAUDE_CODE_TOKEN='your-token'"
else
    echo "✅ Token configured"
fi

# Create minimal config
if [ ! -f ~/.claude_minimal.json ]; then
    echo '{"mcpServers": {}}' > ~/.claude_minimal.json
    echo "✅ Created minimal MCP config"
else
    echo "✅ Minimal config exists"
fi

# Create output directory
mkdir -p output
echo "✅ Output directory ready"

echo ""
echo "Setup complete! You can now run:"
echo "  python3 run.py"
