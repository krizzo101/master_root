# MINIMAL AGENT CONFIGURATION

## Core Instructions
- **Be concise** - Minimal explanations, maximum action
- **Follow requirements exactly** - No interpretation or modification
- **Use evidence-based answers** - No guessing or assumptions

## File Organization
- **Agent workspace**: Use current directory for all work
- **No project root access** - Work only within assigned directory

## Terminal Access
- **CRITICAL**: Use `mcp__shell_exec__shell_exec` tool for ALL terminal operations
- **NEVER use built-in Bash tool** - It fails with wildcards and globs
- **Shell commands** should be passed to shell_exec tool for safe execution

## Tools Available
- **File operations**: Read, Write, Edit (built-in tools)
- **Terminal access**: mcp__shell_exec__shell_exec (MCP tool)
- **Text search**: Grep (built-in tool)

## Success Criteria
- Complete assigned task efficiently
- Use minimal tokens and context
- Provide clear status updates

**This is a minimal test environment. Focus on core functionality only.**
