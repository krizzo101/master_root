# Claude Code Optimization Checklist

## ✅ Active Optimizations
- [x] CLAUDE.md updated with parallel execution rules
- [x] Git worktree support for parallel sessions
- [x] MCP tool prioritization over Bash
- [x] Agent tool awareness instructions
- [x] Hooks configuration for automation
- [x] Output filtering rules enforced
- [x] Task tool parallel agent usage (4-7)
- [x] Grep→Read pattern enforced

## 🔧 Quick Wins
- Use `git worktree` for parallel Claude sessions
- Run `Task` with 4-7 agents for exploration
- Always list MCP tools in agent prompts
- Filter ALL output with head/tail/redirect
- Use MultiEdit for batch file changes

## 📊 Tool Priority
1. MCP tools > Bash for external ops
2. Grep/Glob > find/grep commands
3. MultiEdit > multiple Edits
4. Task agents > sequential work
5. Specialized agents > general Claude

## 🚀 Commands
```bash
git worktree add ../feature -b feature-name
claude --continue  # Resume last
/agents           # Configure agents
/permissions      # Manage tools
```
