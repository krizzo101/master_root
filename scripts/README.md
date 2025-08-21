# Scripts Directory

## sync-claude-config.sh

Synchronize CLAUDE configuration files from master_root to other projects.

### Purpose
Ensures all projects have the latest CLAUDE instructions, agent profiles, and MCP configurations. This maintains consistency across your entire development environment.

### What Gets Synced
- `CLAUDE.md` - Main instructions and guidelines
- `.mcp.json` - MCP server configuration
- `.claude/` directory - Agent profiles, commands, model awareness
- `.cursor/` directory - Cursor rules and templates

### Usage

```bash
# Sync to a specific project
./sync-claude-config.sh /path/to/project

# Sync to all default projects
./sync-claude-config.sh --all

# Preview changes without applying (dry-run)
./sync-claude-config.sh --all --dry-run

# Get help
./sync-claude-config.sh --help
```

### Default Projects
The script includes these projects by default when using `--all`:
- `/home/opsvi/MetaGPT`
- `/home/opsvi/tool_research`
- `/home/opsvi/project-intelligence`
- `/home/opsvi/ARCANE_FOCUS`

### Features
- **Dry-run mode**: Preview changes before applying
- **Git integration**: Optionally commits changes in git repositories
- **Efficient sync**: Uses rsync when available for faster copying
- **Color output**: Clear visual feedback on operations
- **Safety checks**: Confirms before creating directories or committing

### Environment Variables
- `CLAUDE_SOURCE_DIR`: Override source directory (default: `/home/opsvi/master_root`)

### Examples

```bash
# Quick sync to all projects after updating CLAUDE.md
./sync-claude-config.sh --all

# Check what would change in a specific project
./sync-claude-config.sh /home/opsvi/MyProject --dry-run

# Sync and auto-commit changes
echo "y" | ./sync-claude-config.sh /home/opsvi/MetaGPT
```

### Verification
After syncing, verify the update:
```bash
grep -c 'EFFICIENCY & BATCHING' /home/opsvi/*/CLAUDE.md
```

### When to Use
Run this script after:
- Updating CLAUDE.md with new instructions
- Adding or modifying agent profiles
- Changing MCP server configurations
- Creating new cursor rules or templates
- Any significant change to CLAUDE's operational guidelines

### Automation
Add to your shell aliases for quick access:
```bash
alias claude-sync='/home/opsvi/master_root/scripts/sync-claude-config.sh --all'
```
