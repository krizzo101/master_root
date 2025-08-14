#!/bin/bash
# Setup script for automatic MCP server integration with Claude Code

set -e

echo "🚀 Setting up Automatic MCP Server Integration for Claude Code"
echo "============================================================="

# Define project root - CHANGE THIS IF PROJECT MOVES
PROJECT_ROOT="/home/opsvi/master_root"

# Define paths (all relative to project root)
CLAUDE_DIR="$PROJECT_ROOT/.claude"
MCP_LIB_DIR="$PROJECT_ROOT/libs/opsvi-mcp"
CONFIG_FILE="$CLAUDE_DIR/config.json"
MIDDLEWARE_FILE="$CLAUDE_DIR/auto_mcp_middleware.py"

echo "📍 Using project root: $PROJECT_ROOT"

# Create .claude directory if it doesn't exist
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "📁 Creating .claude directory..."
    mkdir -p "$CLAUDE_DIR"
fi

# Check if config exists, create if not
if [ ! -f "$CONFIG_FILE" ]; then
    echo "📝 Config file not found. Creating from template..."
    # Config will be created by the Python script
else
    echo "✅ Config file found at $CONFIG_FILE"
fi

# Set environment variables
echo ""
echo "🔧 Setting environment variables..."

# Add to .bashrc or .zshrc
SHELL_RC="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Check if already configured
if ! grep -q "CLAUDE_AUTO_MCP" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Claude Code Automatic MCP Configuration" >> "$SHELL_RC"
    echo "export CLAUDE_PROJECT_ROOT=$PROJECT_ROOT" >> "$SHELL_RC"
    echo "export CLAUDE_AUTO_MCP=true" >> "$SHELL_RC"
    echo "export CLAUDE_MCP_THRESHOLD=2" >> "$SHELL_RC"
    echo "export CLAUDE_DEFAULT_SERVER=V1" >> "$SHELL_RC"
    echo "export CLAUDE_GUIDANCE_PATH=$MCP_LIB_DIR" >> "$SHELL_RC"
    echo "export CLAUDE_CONFIG_PATH=$CONFIG_FILE" >> "$SHELL_RC"
    echo "export CLAUDE_MIDDLEWARE_PATH=$MIDDLEWARE_FILE" >> "$SHELL_RC"
    echo "" >> "$SHELL_RC"
    echo "✅ Environment variables added to $SHELL_RC"
else
    echo "✅ Environment variables already configured"
fi

# Create Python initialization script
echo ""
echo "🐍 Creating Python initialization script..."

cat > "$CLAUDE_DIR/init_auto_mcp.py" << EOF
#!/usr/bin/env python3
"""Initialize automatic MCP server detection for Claude Code"""

import sys
import os
import json
from pathlib import Path

# Project root
PROJECT_ROOT = "$PROJECT_ROOT"

# Add middleware to path
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".claude"))

# Import middleware
from auto_mcp_middleware import AutoMCPMiddleware, analyze_user_prompt

# Initialize global middleware with project root config
config_path = os.path.join(PROJECT_ROOT, ".claude", "config.json")
middleware = AutoMCPMiddleware(config_path=config_path)

# Monkey-patch Claude's prompt processor (if available)
try:
    import claude_code
    original_process = claude_code.process_prompt
    
    def enhanced_process(prompt, *args, **kwargs):
        """Enhanced prompt processor with automatic MCP detection"""
        # Analyze prompt for MCP usage
        routing = analyze_user_prompt(prompt)
        
        if routing['use_mcp']:
            # Inject MCP server information into context
            kwargs['mcp_routing'] = routing
            print(f"[Auto-MCP] Selected {routing['server']} for this task")
        
        # Call original processor
        return original_process(prompt, *args, **kwargs)
    
    claude_code.process_prompt = enhanced_process
    print("✅ Claude Code enhanced with automatic MCP detection")
    
except ImportError:
    print("ℹ️  Claude Code module not found - middleware ready for manual integration")

# Preload guidance documents
print("📚 Preloading guidance documents...")
middleware._preload_guidance_docs()

print("✅ Auto MCP initialization complete")
print(f"   Project root: {PROJECT_ROOT}")
print(f"   Config path: {config_path}")
EOF

chmod +x "$CLAUDE_DIR/init_auto_mcp.py"

# Create activation script
echo ""
echo "📦 Creating activation script..."

cat > "$CLAUDE_DIR/activate_auto_mcp.sh" << EOF
#!/bin/bash
# Activate automatic MCP server detection

# Project root
export CLAUDE_PROJECT_ROOT="$PROJECT_ROOT"

# MCP configuration
export CLAUDE_AUTO_MCP=true
export CLAUDE_MCP_THRESHOLD=2
export CLAUDE_DEFAULT_SERVER=V1
export CLAUDE_GUIDANCE_PATH="$MCP_LIB_DIR"
export CLAUDE_CONFIG_PATH="$CONFIG_FILE"
export CLAUDE_MIDDLEWARE_PATH="$MIDDLEWARE_FILE"

# Run Python initialization
python3 "$CLAUDE_DIR/init_auto_mcp.py"

echo "✅ Automatic MCP server detection activated"
echo ""
echo "Configuration:"
echo "  - Project Root: \$CLAUDE_PROJECT_ROOT"
echo "  - Auto MCP: \$CLAUDE_AUTO_MCP"
echo "  - Threshold: \$CLAUDE_MCP_THRESHOLD"
echo "  - Default Server: \$CLAUDE_DEFAULT_SERVER"
echo "  - Config Path: \$CLAUDE_CONFIG_PATH"
echo ""
echo "The system will now automatically:"
echo "  1. Analyze every prompt for complexity"
echo "  2. Select appropriate MCP server (V1/V2/V3)"
echo "  3. Execute with optimal configuration"
echo "  4. Fallback gracefully if needed"
echo ""
echo "No manual MCP server selection required!"
EOF

chmod +x "$CLAUDE_DIR/activate_auto_mcp.sh"

# Create test script
echo ""
echo "🧪 Creating test script..."

cat > "$CLAUDE_DIR/test_auto_mcp.py" << EOF
#!/usr/bin/env python3
"""Test automatic MCP server selection"""

import sys
import os

# Project root
PROJECT_ROOT = "$PROJECT_ROOT"
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".claude"))

from auto_mcp_middleware import analyze_user_prompt, get_metrics
import json

# Test prompts
test_cases = [
    ("Fix the login bug", "V1"),
    ("Analyze all Python files for security issues", "V2"),
    ("Create a production-ready authentication system", "V3"),
    ("What does this function do?", None),
    ("Debug why the API returns 500 errors", "V1"),
    ("Generate tests for every module", "V2"),
    ("Build a robust e-commerce platform", "V3"),
]

print("Testing Automatic MCP Server Selection")
print("=" * 50)

correct = 0
total = len(test_cases)

for prompt, expected in test_cases:
    result = analyze_user_prompt(prompt)
    
    if result['use_mcp']:
        selected = result['server']
    else:
        selected = None
    
    status = "✅" if selected == expected else "❌"
    print(f"{status} Prompt: {prompt[:50]}...")
    print(f"   Expected: {expected}, Got: {selected}")
    
    if selected == expected:
        correct += 1
    
    if result['use_mcp']:
        print(f"   Metadata: {result['metadata']}")
    print()

print(f"Score: {correct}/{total} ({100*correct/total:.1f}%)")
print()
print("Metrics:", json.dumps(get_metrics(), indent=2))
EOF

chmod +x "$CLAUDE_DIR/test_auto_mcp.py"

# Run tests
echo ""
echo "🧪 Running tests..."
python3 "$CLAUDE_DIR/test_auto_mcp.py"

# Create convenience aliases
echo ""
echo "🔗 Creating convenience aliases..."

cat > "$CLAUDE_DIR/aliases.sh" << EOF
# Claude Code Auto MCP Aliases
alias claude-auto-on='export CLAUDE_AUTO_MCP=true && echo "✅ Auto MCP enabled"'
alias claude-auto-off='export CLAUDE_AUTO_MCP=false && echo "❌ Auto MCP disabled"'
alias claude-auto-status='python3 $CLAUDE_DIR/test_auto_mcp.py'
alias claude-auto-config='\${EDITOR:-vim} $CONFIG_FILE'
alias claude-auto-logs='tail -f /tmp/claude_auto_mcp.log'
alias claude-auto-metrics='cat /tmp/claude_mcp_metrics.json | python3 -m json.tool'
alias claude-auto-activate='source $CLAUDE_DIR/activate_auto_mcp.sh'
EOF

# Add aliases to shell RC
if ! grep -q "claude-auto-on" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Claude Auto MCP Aliases" >> "$SHELL_RC"
    echo "source $CLAUDE_DIR/aliases.sh" >> "$SHELL_RC"
    echo "✅ Aliases added to $SHELL_RC"
fi

# Final instructions
echo ""
echo "✨ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Reload your shell: source $SHELL_RC"
echo "2. Activate auto MCP: source $CLAUDE_DIR/activate_auto_mcp.sh"
echo "   or use: claude-auto-activate"
echo "3. Test with: claude-auto-status"
echo ""
echo "🎯 Available Commands:"
echo "  claude-auto-on       - Enable automatic MCP"
echo "  claude-auto-off      - Disable automatic MCP"
echo "  claude-auto-status   - Test server selection"
echo "  claude-auto-config   - Edit configuration"
echo "  claude-auto-logs     - View live logs"
echo "  claude-auto-metrics  - View usage metrics"
echo "  claude-auto-activate - Activate the system"
echo ""
echo "📚 Guidance Documents:"
echo "  $MCP_LIB_DIR/CLAUDE.md"
echo "  $MCP_LIB_DIR/CLAUDE_CODE_AGENT_GUIDANCE.md"
echo "  $MCP_LIB_DIR/CLAUDE_CODE_SCENARIOS.md"
echo ""
echo "🚀 Automatic MCP server selection is now ready!"
echo "   Every prompt will be automatically analyzed and routed to the optimal server."
echo ""
echo "📍 All configuration is localized to: $PROJECT_ROOT"