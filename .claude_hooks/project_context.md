# Project Context Auto-Injection Hook

## Purpose
Automatically inject full project context when user gives simple commands like "build X" or "create Y"

## Trigger Patterns
- `build/create/implement/develop/make/start + app/service/api/system/feature`
- `new/another + app/service/api/system/feature`  
- `need/want/require + app/service/api/system/feature`
- Commands starting with `build/create/implement/develop/make`

## What Gets Injected
1. **Mandatory Reading** - CLAUDE.md, SDLC guidelines, monorepo standards
2. **Knowledge System** - Check for existing patterns
3. **Resource Discovery** - Find reusable components in libs/
4. **SDLC Phases** - Discovery → Design → Planning → Development
5. **Project Structure** - Where things go (libs/ vs apps/)
6. **Agent Strategy** - Use Claude Code for everything
7. **Development Standards** - Testing, docs, commits

## Example Transformation

**User says:** "build a payment service"

**Hook transforms to:** 
```
[SYSTEM CONTEXT INJECTION]
- Read standards documents
- Check knowledge system
- Check existing resources
- Follow SDLC phases
- Use proper structure
[END SYSTEM CONTEXT]

USER REQUEST: build a payment service
```

## Configuration
This hook should be registered in your MCP server configuration or as a system prompt modifier.