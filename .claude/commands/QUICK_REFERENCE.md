# Claude Code Quick Reference

## Parallel Work
```bash
# Create worktrees for parallel Claude sessions
git worktree add ../feature-a -b feature-a
git worktree add ../bugfix-b bugfix-123
cd ../feature-a && claude  # Session 1
cd ../bugfix-b && claude   # Session 2
```

## Essential Commands
```bash
/agents              # Manage subagents & tools
/permissions         # Manage tool permissions
/approved-tools      # View/edit approved tools
/memory             # Edit memory files
/mcp                # MCP server management
claude --continue   # Resume last session
claude --resume     # Pick session to resume
```

## Tool Patterns
- Grep→Read (never Read without Grep)
- MultiEdit>Edit (batch changes)
- MCP>Bash (external operations)
- Task(4-7 agents) for parallel work

## MCP Tool Names
```
mcp__<server>__<tool>
mcp__firecrawl__firecrawl_scrape
mcp__knowledge__knowledge_store
mcp__claude-code-wrapper__claude_run
```

## Performance Tips
- Filter output: | head -20, > /tmp/log
- Suppress errors: 2>/dev/null
- Git concise: --oneline -10
- Search limits: head_limit param
