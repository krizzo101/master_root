# Claude Agent Startup Checklist

## ✅ Session Start (MANDATORY)

```python
# Run in this exact order:
1. mcp__time__current_time(format="YYYY-MM-DD HH:mm:ss")  # Check current date
2. Create git worktree for isolation
3. mcp__knowledge__knowledge_query(query_type="recent", limit=5)
4. Read .claude/MODEL_AWARENESS_2025.md if using OpenAI
```

## ⚠️ Model Awareness (2025+)

### CORRECT Models (as of 2025)
- **GPT-4o** - Complex reasoning (1M tokens/day)
- **GPT-4o-mini** - High-volume tasks (10M tokens/day)

### OUTDATED/FORBIDDEN Models
- ❌ GPT-5, GPT-5-mini (don't exist yet)
- ❌ O3, O4-mini (don't exist yet)
- ❌ GPT-4, GPT-3.5 (outdated)

## 🚀 Parallel Execution

### WRONG (Sequential)
```python
Task(...)
# later...
Task(...)
```

### CORRECT (Parallel)
```python
# Multiple Tasks in ONE message
Task(subagent_type="qa-testing-guru", prompt="Test A")
Task(subagent_type="qa-testing-guru", prompt="Test B")
Task(subagent_type="qa-testing-guru", prompt="Test C")
```

## 📁 File Management Rules

1. **NEVER** create new versions (no _v2, _fixed, _updated)
2. **ALWAYS** update existing files in place
3. **CHECK** file exists before creating: `test -f filename`

## 🧠 Thinking Requirements

### Before EVERY action:
```python
mcp__thinking__sequentialthinking(
    thought="What I'm about to do and why",
    nextThoughtNeeded=True/False,
    thoughtNumber=N,
    totalThoughts=M
)
```

## 💾 Knowledge Storage

### After ANY discovery/solution:
```python
mcp__knowledge__knowledge_store(
    content="What I learned",
    knowledge_type="ERROR_SOLUTION",
    tags=["relevant", "tags"]
)
```

## 🎯 Task Routing

| Task Count | Action |
|------------|--------|
| 1 task | Direct execution |
| 2+ similar | Task tool (parallel) |
| 3+ steps | TodoWrite first |

## 🔍 Common Subagents

- `development-specialist` - Implementation
- `qa-testing-guru` - Testing
- `test-remediation-specialist` - Fix tests
- `refactoring-master` - Refactor code
- `code-analyzer` - Review code
- `solution-architect` - Design
- `excellence-optimizer` - Complex problems
- `research-genius` - Information gathering

## 📚 Required Reading

1. `.claude/MODEL_AWARENESS_2025.md` - Current models
2. `.claude/TASK_TOOL_USAGE.md` - Parallel patterns
3. `.claude/CLAUDE_AGENT_SYSTEM_PROMPT.md` - Standards
4. `.claude/config.json` - Configuration

## ⛔ Never Do

- Use wildcards in shell commands (*, ?, [])
- Work directly on main/master branch
- Skip thinking before acting
- Create duplicate file versions
- Assume models from training data

## 🔄 Session End

```python
# Recommend (don't execute):
print(f"git merge claude-{SESSION_ID} --no-ff")
print(f"git worktree remove {WORKTREE_DIR}")
```

---

**CRITICAL**: Check current date first - your training IS outdated!
