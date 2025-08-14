# PROJECT DIRECTIVES

## File Management Rules (ALL FILES)

### APPLIES TO: Code, Documentation, Configuration, Scripts, Tests - EVERYTHING
1. **UPDATE existing files** - Do not create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One file per purpose
4. **Fix in place** - Correct errors in the original file
5. **No parallel versions** - Never have multiple versions of the same functionality
6. **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages

### Git Commit Requirements
- **Commit frequently** - After completing each logical unit of work
- **Descriptive messages** - Explain what changed and why
- **Atomic commits** - Each commit should be a single logical change
- **Check status regularly** - Use `git status` to track changes
- **Never rely on filenames for versioning** - That's what git is for

### Quality Standards
- All content must be tested and accurate
- Do not document/code assumptions or guesses as facts
- If something is untested, mark it as "NOT TESTED"
- Do not add meta-commentary about verification or corrections
- No comments about "fixing" or "updating" previous versions

## MCP Server Usage

**Before responding to ANY code or analysis task:**

1. CHECK if the task matches MCP criteria below
2. USE the appropriate MCP server tool
3. DO NOT use basic Read/List/Bash for tasks that match MCP patterns

## REQUIRED BEHAVIOR - YOU MUST DO THIS

### For ANY request containing these keywords → USE V1:
- **Keywords**: debug, fix, error, bug, why, investigate
- **MANDATORY TOOL**: `mcp__claude-code-wrapper__claude_run`
- **DO NOT**: Use Read/Grep/Bash to debug manually

### For ANY request containing these keywords → USE V2:
- **Keywords**: analyze all, analyze files, all files, every, multiple, entire project
- **MANDATORY TOOL**: `mcp__claude-code-v2__spawn_parallel_agents`
- **DO NOT**: Use List/Read to analyze files one by one

### For ANY request containing these keywords → USE V3:
- **Keywords**: production, robust, comprehensive, enterprise, build system
- **MANDATORY TOOL**: `mcp__claude-code-v3__claude_run_v3`
- **DO NOT**: Build manually with basic tools

## EXAMPLE OF CORRECT BEHAVIOR

When user says: "analyze the files in this project"
YOU MUST:
```python
# CORRECT - Use V2 for parallel analysis
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=["Analyze project structure", "Analyze core libraries", "Analyze configurations"],
    timeout=600
)
```

YOU MUST NOT:
```python
# WRONG - Don't use basic tools for bulk analysis
List("libs")  # NO!
Read("README.md")  # NO!
Bash("find...")  # NO!
```

## ENFORCEMENT CHECK

Before using ANY of these tools for code tasks:
- Read, List, Glob, Grep, Bash

Ask yourself: "Should this be using an MCP server instead?"
- If analyzing multiple files → Use V2
- If debugging → Use V1  
- If building production code → Use V3

## THIS IS NOT OPTIONAL

These are MANDATORY instructions for this project. Using the wrong tools for tasks that match MCP patterns is incorrect behavior.

## Quick Reference - Use These Tools

| User Says | YOU MUST USE | NOT These |
|-----------|--------------|-----------|
| "analyze files" | `mcp__claude-code-v2__spawn_parallel_agents` | List, Read |
| "debug error" | `mcp__claude-code-wrapper__claude_run` | Grep, Bash |
| "build system" | `mcp__claude-code-v3__claude_run_v3` | Write, Edit |

## VERIFICATION

If asked "Did you use the MCP servers for that task?", you should be able to say YES and show which tool you used.

Remember: This is MANDATORY for this project. Check EVERY task against these patterns.