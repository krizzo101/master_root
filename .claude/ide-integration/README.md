# IDE Integration Guide

## Supported IDEs

### 1. VSCode / Cursor / Windsurf
- **Setup**: Run `./vscode-setup.sh`
- **Extension**: Anthropic Claude Code extension
- **Shortcut**: Cmd+Esc (Mac) / Ctrl+Esc (Windows/Linux)

### 2. JetBrains IDEs (IntelliJ, PyCharm, WebStorm)
- **Plugin**: Claude Code Plugin
- **Install**: Settings → Plugins → Search "Claude Code"
- **Shortcut**: Ctrl+Shift+C

### 3. Neovim
- **Plugin**: `coder/claudecode.nvim`
- **Install**: Add to your plugin manager
```vim
Plug 'coder/claudecode.nvim'
```

### 4. Terminal Integration
Claude Code works natively in terminal:
```bash
# Start Claude Code
claude

# With specific task
claude "implement the user authentication feature"

# In specific directory
claude --cwd /path/to/project
```

## Quick Setup Commands

### VSCode
```bash
# Install extension
code --install-extension anthropic.claude-code

# Open with Claude Code
code . && claude
```

### Terminal Alias
Add to your shell profile:
```bash
alias cc='claude'
alias cct='claude "run tests"'
alias ccr='claude "review code"'
alias ccd='claude "debug this"'
```

## Features by IDE

| Feature | VSCode | JetBrains | Neovim | Terminal |
|---------|--------|-----------|--------|----------|
| Inline suggestions | ✅ | ✅ | ✅ | ❌ |
| Code explanation | ✅ | ✅ | ✅ | ✅ |
| Refactoring | ✅ | ✅ | ✅ | ✅ |
| Test generation | ✅ | ✅ | ✅ | ✅ |
| Debug assistance | ✅ | ✅ | ✅ | ✅ |
| Git integration | ✅ | ✅ | ❌ | ✅ |
| MCP support | ✅ | ✅ | ✅ | ✅ |

## Configuration Files

### Project Level
- `.claude/settings.json` - Project settings
- `.claude/commands/` - Custom commands
- `.claude/agents/` - Custom agents
- `CLAUDE.md` - Project instructions

### User Level
- `~/.claude/config.json` - Global settings
- `~/.claude/commands/` - Personal commands

## Best Practices

1. **Keep Claude Code running**: Better context retention
2. **Use shortcuts**: Faster than typing commands
3. **Configure project-specific settings**: Better results
4. **Use agents for specialized tasks**: More accurate outputs
5. **Set up hooks**: Automate repetitive tasks

## Troubleshooting

### VSCode Extension Not Working
```bash
# Reinstall
code --uninstall-extension anthropic.claude-code
code --install-extension anthropic.claude-code
```

### JetBrains Plugin Issues
1. Check IDE version (2023.1+)
2. Restart IDE after installation
3. Check Settings → Tools → Claude Code

### Terminal Issues
```bash
# Check installation
claude --version

# Update
npm update -g @anthropic/claude-code

# Reinstall
npm uninstall -g @anthropic/claude-code
npm install -g @anthropic/claude-code
```

## Advanced Integration

### Custom Keybindings (VSCode)
Edit `.vscode/keybindings.json`:
```json
{
  "key": "cmd+k cmd+c",
  "command": "claude.askAboutSelection"
}
```

### IDE Workflow Automation
Create `.vscode/tasks.json`:
```json
{
  "label": "Claude Review",
  "command": "claude",
  "args": ["review the current file"],
  "type": "shell"
}
```

### Multi-IDE Setup
Sync settings across IDEs:
```bash
# Link settings
ln -s ~/.claude/settings.json .claude/settings.json
```

## Resources

- [VSCode Extension](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
- [JetBrains Plugin](https://plugins.jetbrains.com/plugin/claude-code)
- [Neovim Plugin](https://github.com/coder/claudecode.nvim)
- [Official Docs](https://docs.anthropic.com/en/docs/claude-code/ide-integrations)
