# Prime Context for Development Session

Load comprehensive project context to establish shared understanding.

## Execute these steps:

1. **Check current state**:
   - Run `pwd` to confirm working directory
   - Run `git status` to see current changes
   - Run `git branch --show-current` to confirm branch

2. **Load project structure**:
   - Display directory tree (max depth 3): `tree -L 3 -I 'node_modules|__pycache__|.git'`
   - List key configuration files: `ls -la *.json *.yaml *.toml *.md 2>/dev/null`

3. **Read critical files**:
   - Read CLAUDE.md if it exists
   - Read README.md for project overview
   - Read package.json or pyproject.toml for dependencies
   - Read any .env.example for environment requirements

4. **Understand recent work**:
   - Show last 10 commits: `git log --oneline -10`
   - Show recent file changes: `git diff --stat HEAD~5..HEAD`
   - Check for any TODO/FIXME comments: `grep -r "TODO\|FIXME" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | head -20`

5. **Identify project type and stack**:
   - Detect primary language and framework
   - Note testing framework and commands
   - Identify build/deploy processes
   - Check for CI/CD configuration

6. **Load MCP and tool context**:
   - Check available MCP servers: `/mcp`
   - Note any custom agents or tools
   - Review .claude/commands for project-specific commands

7. **Establish working agreement**:
   - Confirm coding standards to follow
   - Note any specific project conventions
   - Identify areas to avoid modifying
   - Set success criteria for session

After loading context, provide a brief summary:
- Project type and purpose
- Current task/branch focus
- Key technologies in use
- Any blockers or concerns noticed
- Suggested next steps
