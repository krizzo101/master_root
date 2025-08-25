#!/bin/bash
# VSCode Integration Setup for Claude Code

echo "=== VSCode Claude Code Integration Setup ==="
echo ""

# Check if VSCode is installed
if ! command -v code &> /dev/null; then
    echo "VSCode not found. Please install VSCode first."
    echo "Visit: https://code.visualstudio.com/"
    exit 1
fi

# Install Claude Code VSCode extension
echo "Installing Claude Code VSCode extension..."
code --install-extension anthropic.claude-code 2>/dev/null || echo "Extension may already be installed"

# Create VSCode settings for project
cat > .vscode/settings.json << 'EOF'
{
  "claude.projectRoot": "${workspaceFolder}",
  "claude.autoStart": true,
  "claude.showInStatusBar": true,
  "claude.shortcuts": {
    "openChat": "cmd+shift+c",
    "runCommand": "cmd+shift+r",
    "showAgents": "cmd+shift+a"
  },
  "claude.defaultAgent": "general-purpose",
  "claude.hooks.enabled": true,
  "claude.mcp.autoConnect": true,
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black"
}
EOF

# Create keybindings
cat > .vscode/keybindings.json << 'EOF'
[
  {
    "key": "cmd+esc",
    "command": "claude.open",
    "when": "editorTextFocus"
  },
  {
    "key": "cmd+shift+enter",
    "command": "claude.sendToChat",
    "when": "editorHasSelection"
  },
  {
    "key": "cmd+shift+/",
    "command": "claude.explainCode",
    "when": "editorHasSelection"
  }
]
EOF

# Create tasks for Claude workflows
cat > .vscode/tasks.json << 'EOF'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Claude: Run Tests",
      "type": "shell",
      "command": "${workspaceFolder}/scripts/claude-workflows/full-test-suite.sh",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Claude: Code Review",
      "type": "shell",
      "command": "${workspaceFolder}/scripts/claude-workflows/code-review.sh",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Claude: Deploy",
      "type": "shell",
      "command": "${workspaceFolder}/scripts/claude-workflows/deploy-pipeline.sh",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
EOF

echo "✅ VSCode integration configured!"
echo ""
echo "Shortcuts configured:"
echo "  Cmd+Esc         - Open Claude Code"
echo "  Cmd+Shift+C     - Open chat"
echo "  Cmd+Shift+R     - Run command"
echo "  Cmd+Shift+A     - Show agents"
echo "  Cmd+Shift+Enter - Send selection to Claude"
echo "  Cmd+Shift+/     - Explain selected code"
echo ""
echo "Restart VSCode to apply changes."
