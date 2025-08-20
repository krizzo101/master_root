# Claude Code Optimization Report
## Comprehensive Research Findings for CLAUDE.md & .claude/ Configuration

---

## 1. PARALLEL EXECUTION & WORKFLOW OPTIMIZATION

### Git Worktrees for Parallel Claude Sessions
```bash
# Setup parallel work environments
git worktree add ../project-feature-a -b feature-a
git worktree add ../project-bugfix bugfix-123
git worktree list
git worktree remove PATH

# Run independent Claude sessions
cd ../project-feature-a && claude
cd ../project-bugfix && claude
```

**Benefits:**
- Complete file isolation between Claude instances
- Shared Git history and remote connections
- No conflicts when working on multiple features
- Each worktree = independent Claude context

### Task Tool Parallelization
```markdown
# Optimal patterns for Task tool usage
- Run up to 7 parallel agents (recommended maximum)
- Each agent has independent context window
- Use for: codebase exploration, parallel testing, multi-component work

# Example prompts:
"Use 4 tasks to explore src/, tests/, docs/, lib/ in parallel"
"Run unit tests with agent 1, integration with agent 2, e2e with agent 3"
```

### Specialized Agent Types (Available in Task Tool)
- `test-remediation-specialist`: Testing and bug fixing
- `code-reviewer`: Security and quality checks
- `excellence-optimizer`: Production-ready solutions
- `research-genius`: Information synthesis
- `refactoring-master`: Code transformation
- `solution-architect`: System design
- `sdlc-*`: Phase-specific SDLC agents

---

## 2. MEMORY MANAGEMENT & CONTEXT OPTIMIZATION

### CLAUDE.md Best Practices
```markdown
# Memory Hierarchy (Higher precedence wins)
1. Enterprise Policy (system-wide)
2. Project Memory (team-level)
3. User Memory (personal)
4. Local Memory (deprecated)

# Optimization Rules
- Keep <2000 tokens per memory file
- Use imports: @path/to/import (5 levels deep max)
- Quick add with # shortcut
- Refresh with /memory command
- Auto-loads at session start (consumes context)
```

### Context Window Strategies
```markdown
# Chunking Guidelines
- 10 small files (<100 lines)
- 5 medium files (100-300 lines)
- 2 large files (300-1000 lines)
- 1 huge file (1000+ lines)

# Output Filtering (CRITICAL)
- Use: | head -20, | tail -20
- Redirect: > /tmp/log then grep
- Suppress: 2>/dev/null, --quiet flags
- Git: --oneline -10, --stat
- Searches: head_limit parameter
```

### Token Usage Reduction
1. **Delegate to subagents** - Each has independent context
2. **Grep before Read** - Filter first, read specific matches
3. **MultiEdit over Edit** - Batch changes
4. **Filter verbose output** - Always suppress/redirect
5. **Semantic search** - Retrieve only relevant context

---

## 3. HOOKS AUTOMATION

### Critical Hook Patterns
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "python3 -c \"import json,sys; d=json.load(sys.stdin); sys.exit(2 if '.env' in d.get('tool_input',{}).get('file_path','') else 0)\""
      }]
    }],
    "PostToolUse": [{
      "matcher": "Edit|MultiEdit|Write",
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format.sh"
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Current time:' $(date)"
      }]
    }]
  }
}
```

### Hook Events & Use Cases
- **PreToolUse**: Validation, security checks
- **PostToolUse**: Auto-format, lint, test
- **UserPromptSubmit**: Context injection, prompt validation
- **SessionStart**: Load state, run setup
- **Stop/SubagentStop**: Cleanup, save state

---

## 4. SUBAGENT CONFIGURATION

### Subagent Definition Template
```markdown
---
name: agent-name
description: When to use this agent
tools: ALL                    # or specific: Read, Edit, Bash, mcp__*
model: opus                    # optional model override
---

You are a specialized agent with these capabilities:

## Available Tools & Usage
- **Tool Name**: When and how to use
- **mcp__server__tool**: MCP tool usage patterns

## Core Methodology
[Specific approach for this agent type]

## Success Criteria
[What constitutes successful completion]
```

### Tool Permission Strategies
```yaml
# Default behavior
tools: ALL                    # Inherits everything

# Restricted access
tools: Read, Grep, Glob       # Only these tools

# Include MCP tools
tools: Read, Edit, mcp__firecrawl__*, mcp__knowledge__*

# Management commands
/agents                       # Interactive configuration
/permissions                  # Manage tool permissions
```

---

## 5. MCP INTEGRATION BEST PRACTICES

### MCP Server Configuration
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/name"],
      "env": {
        "API_KEY": "key-value"
      }
    }
  }
}
```

### MCP Tool Naming Convention
```
mcp__<serverName>__<toolName>

Examples:
- mcp__firecrawl__firecrawl_scrape
- mcp__knowledge__knowledge_store
- mcp__claude-code-wrapper__claude_run
- mcp__tech_docs__get-library-docs
```

### Essential MCP Servers
- **firecrawl**: Web scraping and search
- **tech_docs**: Library documentation
- **knowledge**: Knowledge base operations
- **db**: Database operations (Neo4j)
- **research_papers**: Academic content
- **claude-code-wrapper**: Recursive Claude execution
- **gemini-agent**: Alternative AI execution

---

## 6. AGENT TOOL USAGE OPTIMIZATION

### Instructing Agents About Tools
```markdown
# ALWAYS include in agent prompts:

You have access to these tools:
- Standard: Read, Write, Edit, MultiEdit, Bash, Grep, Glob
- MCP Web: mcp__firecrawl__* (web scraping)
- MCP Docs: mcp__tech_docs__* (documentation)
- MCP Knowledge: mcp__knowledge__* (knowledge base)
- MCP Database: mcp__db__* (Neo4j operations)

## Tool Usage Rules:
1. ALWAYS Grep before Read (search first)
2. Use MultiEdit for multiple changes
3. Prefer MCP tools over Bash for external operations
4. Batch similar operations together
5. Check tool responses before proceeding
```

### Tool Selection Matrix
| Task | Use This | NOT This |
|------|----------|----------|
| Search code | Grep, Glob | find, Bash(grep) |
| Web content | mcp__firecrawl__ | Bash(curl), WebFetch |
| Documentation | mcp__tech_docs__ | Web search |
| Database | mcp__db__ | Bash SQL |
| Multiple edits | MultiEdit | Multiple Edits |
| Parallel work | Task tool | Sequential ops |

---

## 7. PERFORMANCE OPTIMIZATION

### Speed Improvements
1. **Parallel over Sequential** - Always prefer parallel execution
2. **Batch operations** - MultiEdit, multiple tool calls
3. **Filter early** - Grep → Read, not Read → Grep
4. **Use specialized agents** - Focused = faster
5. **Hooks automation** - Eliminate manual steps
6. **Direct MCP access** - Skip file operations

### Resource Management
```markdown
# Output control
- Suppress verbose: 2>/dev/null
- Limit output: | head -20, | tail -20
- Git concise: --oneline, --stat
- Search limits: head_limit parameter
- Redirect large: > /tmp/file then process

# Context preservation
- Use --continue for auto-resume
- Use --resume for session picker
- Export sessions for audit trails
```

---

## 8. RECOMMENDED CLAUDE.md UPDATES

### Core Rules to Add/Update
```markdown
# PARALLEL EXECUTION
WORKTREES: Use git worktrees for parallel work. Never multiple Claudes in same dir.
TASK_PARALLEL: Use Task tool with 4-7 agents for exploration/testing
AGENT_CHAIN: Chain specialists: analyzer→optimizer, reviewer→fixer

# TOOL USAGE
TOOL_HIERARCHY: Grep→Read, MultiEdit→Edit, MCP→Bash(external)
MCP_PRIORITY: Always use MCP tools for: web(firecrawl), docs(tech_docs), db(db), knowledge(knowledge)
TOOL_LISTING: Always list ALL available tools in agent prompts, especially mcp__*

# MEMORY OPTIMIZATION
TOKEN_LIMIT: CLAUDE.md <2000 tokens. Use @imports for modular context
OUTPUT_FILTER: ALWAYS: | head -20, 2>/dev/null, --quiet, > /tmp/log
CONTEXT_BATCH: 10small/5med/2large/1huge files per read

# AGENT INSTRUCTIONS
EXPLICIT_TOOLS: List all tools with usage patterns in every agent prompt
MCP_AWARENESS: Include "You have MCP tools: mcp__server__*" in prompts
TOOL_EXAMPLES: Provide tool chain examples in agent definitions
```

---

## 9. RECOMMENDED .claude/ STRUCTURE

```
.claude/
├── agents/
│   ├── [existing 22 agents]
│   └── custom-agents.md
├── hooks/
│   ├── pre-tool-validate.py
│   ├── post-edit-format.sh
│   └── session-start.sh
├── settings.json (hooks configuration)
├── settings.local.json (local overrides)
└── commands/
    └── SDLC_PHASE_CHECKLIST.md
```

### Settings.json Template
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-tool-validate.py"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-format.sh"
        }]
      }
    ]
  }
}
```

---

## 10. CRITICAL PATTERNS TO ENFORCE

### Always Do
1. **Parallel execution** when possible
2. **Filter before reading** (Grep→Read)
3. **Batch operations** (MultiEdit, parallel Tasks)
4. **Use MCP tools** for external operations
5. **List tools explicitly** in agent prompts
6. **Suppress verbose output** systematically

### Never Do
1. **Never** use find/grep commands (use tools)
2. **Never** Read without Grep first
3. **Never** sequential when parallel possible
4. **Never** assume agents know about MCP tools
5. **Never** let output flood context
6. **Never** use Bash for operations with dedicated tools

---

## 11. QUICK REFERENCE COMMANDS

```bash
# Session Management
claude --continue              # Resume last session
claude --resume                # Pick session to resume
claude --debug                 # Debug mode
claude --mcp-debug            # MCP debug mode

# Configuration
/agents                        # Manage subagents
/permissions                   # Manage tool permissions
/approved-tools               # View/edit approved tools
/memory                       # Edit memory files
/config                       # Configuration settings
/mcp                          # MCP server management

# Workflow
git worktree add PATH -b BRANCH  # Parallel work
claude mcp add                    # Add MCP server
claude config add VALUE           # Add config value
```

---

## 12. IMPLEMENTATION PRIORITY

### High Priority (Immediate Impact)
1. Update CLAUDE.md with parallel execution rules
2. Add MCP tool awareness to all agent prompts
3. Implement output filtering rules
4. Configure essential hooks for automation

### Medium Priority (Efficiency Gains)
1. Set up git worktrees for parallel work
2. Create specialized subagents for common tasks
3. Configure MCP servers for external data
4. Implement token optimization strategies

### Low Priority (Nice to Have)
1. Advanced hook scripts for complex workflows
2. Custom commands for team-specific needs
3. Telemetry and monitoring setup
4. Session export automation

---

This report consolidates all research findings for optimal Claude Code usage. Key takeaways:
- **Parallelization** is the biggest performance multiplier
- **MCP tools** should replace Bash for external operations
- **Explicit tool listing** ensures agents use all capabilities
- **Output filtering** prevents context overflow
- **Hooks** automate repetitive workflows

Use this as a reference when updating CLAUDE.md and .claude/ configurations.
