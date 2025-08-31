# External Projects Reference Guide

## Repository Locations
All external projects cloned to: `/home/opsvi/master_root/external-projects/`

## High-Value Components to Extract

### 1. SuperClaude_Framework
**Location**: `external-projects/SuperClaude_Framework/`
**Key Components**:
- `SuperClaude/Core/` - Core command and mode structures
- `SuperClaude/MCP/configs/` - Pre-configured MCP server configs
- `SuperClaude/Tools/` - Tool implementations
- `SuperClaude/CORE.md` - Complete framework documentation

**What to Extract**:
```python
# Command structure from Core/
from SuperClaude.Core import commands, modes, personas

# MCP configurations
configs = {
    "context7": "MCP/configs/context7.json",
    "playwright": "MCP/configs/playwright.json",
    "sequential": "MCP/configs/sequential.json"
}
```

### 2. claude-code-proxy (1rgs)
**Location**: `external-projects/claude-code-proxy/`
**Key Components**:
- `server.py` - Complete proxy implementation
- `tests.py` - Test suite for validation
- `.env.example` - Configuration template

**What to Extract**:
```python
# Main proxy server implementation
# Key functions: convert_to_anthropic_format(), handle_streaming()
# Model mapping: BIG/SMALL to specific models
# Provider routing through LiteLLM
```

### 3. Claude-Code-Usage-Monitor
**Location**: `external-projects/Claude-Code-Usage-Monitor/`
**Key Components**:
- `src/claude_monitor/` - Core monitoring implementation
- `src/claude_monitor/core/` - Usage tracking
- `src/claude_monitor/ui/` - Dashboard components

**What to Extract**:
```python
# Usage tracking from core/monitor.py
# Cost calculation from core/cost_calculator.py
# Session management from core/session_manager.py
```

## Pattern Mining Sources

### 4. claude-flow
**Location**: `external-projects/claude-flow/`
**Pattern Sources**:
- Session memory schema (SQLite)
- Swarm orchestration patterns
- Hook system implementation

**DO NOT use directly** - Alpha quality, mine for ideas only

### 5. claude-code-hooks-mastery
**Location**: `external-projects/claude-code-hooks-mastery/`
**Pattern Sources**:
- Pre/post action hooks
- Context hydration examples
- Safety rail patterns

### 6. claude-code-workflows
**Location**: `external-projects/claude-code-workflows/`
**Pattern Sources**:
- Playwright MCP integration
- Design review automation
- PR gate workflows

## Integration Commands

### Quick Setup Commands
```bash
# Copy SuperClaude command structure
cp -r external-projects/SuperClaude_Framework/SuperClaude/Core/* .claude/commands/

# Set up proxy server
cp external-projects/claude-code-proxy/server.py .claude/proxy/
cp external-projects/claude-code-proxy/.env.example .claude/proxy/.env

# Install usage monitor
cp -r external-projects/Claude-Code-Usage-Monitor/src/claude_monitor .claude/monitor/
```

### Pattern Extraction Commands
```bash
# Extract hook patterns
grep -r "hook" external-projects/claude-code-hooks-mastery/ --include="*.py"

# Find memory patterns
grep -r "sqlite\|memory" external-projects/claude-flow/ --include="*.py"

# Extract workflow patterns
find external-projects/claude-code-workflows -name "*.yml" -o -name "*.yaml"
```

## Priority Integration Order

1. **Week 1 - Foundation**
   - [ ] SuperClaude command structure
   - [ ] claude-code-proxy setup
   - [ ] Usage monitor integration

2. **Week 2 - Enhancement**
   - [ ] Hook patterns from hooks-mastery
   - [ ] Memory patterns from claude-flow
   - [ ] Workflow patterns from workflows

## Notes
- Always check licenses before integration
- Test in isolation before production deployment
- Keep our CLAUDE.md as override for any conflicts
- Document any modifications made to external code