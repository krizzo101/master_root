# CLAUDE.md - Dynamic Instruction System

## CRITICAL: Your instructions are in the Knowledge Base, NOT this file.

### MANDATORY STARTUP SEQUENCE (IN THIS ORDER - NO EXCEPTIONS)
1. **THINK FIRST**: `mcp__thinking__sequentialthinking` or `mcp__thinking__metacognitivethinking` - ALWAYS, NO EXCEPTIONS
2. **Check time**: `mcp__time__current_time("YYYY-MM-DD HH:mm:ss")`
3. **Query instructions** (MCP servers may still be initializing):
   ```python
   # If "No such tool available" error → Continue with fallback rules below
   mcp__knowledge__knowledge_query(query_type="search", search_text="GLOBAL OPERATIONAL INSTRUCTIONS", limit=1)
   mcp__knowledge__knowledge_query(query_type="recent", limit=10)
   ```
4. **Check git**: Use `mcp__shell_exec__shell_exec("git branch --show-current")` if available, else `Bash("git branch --show-current")`
   - If on main/master → CREATE feature branch immediately
5. **Follow retrieved instructions EXACTLY** - they contain critical operational rules
6. **If KB was unavailable**: Use the CRITICAL FALLBACK RULES below

### CRITICAL FALLBACK RULES (When KB Unavailable)

#### WILDCARD/GLOB OPERATIONS - NEVER USE BASH
**⚠️ CRITICAL**: ANY command with wildcards MUST use shell_exec or mcp__shell_exec__shell_exec:
```bash
# ❌ WRONG - WILL FAIL:
Bash("ls *.py")
Bash("find . -name '*.py'")
Bash("grep pattern *.js")

# ✅ CORRECT:
mcp__shell_exec__shell_exec("ls *.py")
mcp__shell_exec__shell_exec("find . -name '*.py'")
mcp__shell_exec__shell_exec("grep pattern *.js")
```
**Bash tool returns "glob: No such file or directory" for ANY wildcard usage!**

#### STOP CHECKS (Before ANY Action)
1. **Before file operations**: Check file exists first
2. **Before creating files**: Consider editing existing files
3. **Multiple operations**: Use parallel execution in ONE message
4. **3+ step tasks**: Create TodoWrite list FIRST

#### METACOGNITIVE QUESTIONS (Ask Yourself)
- "Is there redundancy here?"
- "What assumptions am I making?"
- "Is this a recurring pattern?"
- "Am I solving the real problem or just symptoms?"

### PERIODIC REFRESH (MANDATORY)
**Context Decay Warning**: You forget instructions as the session progresses.

**Refresh triggers** (query KB instructions again when):
- After 20+ tool invocations
- Before major operations (file creation, deletions, refactoring)
- When switching between different parts of the codebase
- If you catch yourself not following protocols (e.g., using Bash for globs)
- After encountering errors or unexpected behavior
- Every 30 minutes of session time

**Quick refresh**: `mcp__knowledge__knowledge_query(query_type="search", search_text="GLOBAL OPERATIONAL", limit=1)`

### WHY THIS APPROACH
- Instructions can be updated without file changes
- Different projects have different instructions
- Scoped instructions (global → project → app)
- Self-improving system through KB updates
- You MUST query KB for operational instructions

### PROJECT-SPECIFIC FACTS
- Location: /home/opsvi/master_root
- Python: /home/opsvi/miniconda/bin/python (ALWAYS use this explicit path)
- Knowledge system: apps/knowledge_system/
- ACCF: apps/ACCF/
- Project-intelligence: apps/project-intelligence/

**Remember**: This file is just a bootstrap. Your REAL instructions are in the KB.
Query them EVERY session start. NO EXCEPTIONS.
