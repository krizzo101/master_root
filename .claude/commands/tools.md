---
description: Complete overview of available tools, apps, and capabilities
allowed-tools: Read, Bash
---

## 🛠️ Complete Tools & Capabilities Overview

### 📦 MCP Servers (Configured in .mcp.json)
- **firecrawl** - Web scraping/crawling with Firecrawl API
- **tech_docs** - Technical documentation access
- **web_search** - Brave search API integration
- **knowledge** - Neo4j-backed knowledge base
- **thinking** - AI reasoning/thinking server
- **time** - Time utilities and operations
- **shell_exec** - Shell command execution

### 🚀 Major Apps (/home/opsvi/master_root/apps/)

**Core Infrastructure:**
- **agent-orchestrator** - Coordinate 15+ parallel agents with checkpoints
- **dpo** - Development Process Orchestrator for SDLC workflows
- **hecaton** - Multi-agent coordination system
- **project-intelligence** - Codebase analysis with O(1) lookups

**Monitoring & Analysis:**
- **claude-monitor** - Monitor Claude interactions
- **multi-agent-monitor** - Track multi-agent workflows
- **sleuth-intel** - People/business discovery tool
- **session-optimizer** - Optimize Claude sessions

**Development Tools:**
- **autonomous_coder** - Autonomous coding assistant
- **wbs-documenter** - Work breakdown structure docs
- **kb-auto-docs** - Auto-generate knowledge base docs
- **claude-code-clone** - Claude Code functionality clone

**Specialized Tools:**
- **context_isolation_specialist** - Manage context isolation
- **error_capture_specialist** - Error handling specialist
- **unified_orchestrator_fixes** - Orchestrator repair tools
- **razer** - Rapid development framework

### ⚡ Quick Access Commands

**Orchestrator Commands:**
- `/orchestrator-quickstart` - Quick onboarding
- `/orchestrator-document` - Generate full docs
- `/orchestrator-analyze` - System analysis
- `/orchestrator-resume` - Resume from checkpoint

**Project Intelligence:**
- `/proj-intel-quickstart` - Quick start guide
- `/proj-intel-generate` - Generate intelligence
- `/proj-intel-analyze` - Analyze codebase
- `/proj-intel-search` - Search code elements
- `/proj-intel-refresh` - Refresh after changes

**SDLC & Development:**
- `/sdlc` - Full SDLC workflow
- `/xarchitecture` - Architecture documentation
- `/commit` - Smart git commits
- `/tdd` - Test-driven development

### 📊 Project Intelligence
```bash
# Generate intelligence for any project
cd /path/to/project
project-intelligence full-package

# Read with specialized script
python /home/opsvi/master_root/scripts/proj_intel_reader.py --help
```

### 🤖 Agent Orchestrator
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator

# Generate docs for any project
python run_orchestrator_task.py --task-type system-documentation

# Run analysis
python run_system_analysis.py

# Monitor dashboard
python production_dashboard.py
```

### 🔧 System Paths
- **Python**: `/home/opsvi/miniconda/bin/python`
- **Scripts**: `/home/opsvi/master_root/scripts/`
- **Apps**: `/home/opsvi/master_root/apps/`
- **Commands**: `/home/opsvi/master_root/.claude/commands/`

### 📚 Documentation
- Full commands inventory: `.claude/COMMANDS_AND_HOOKS_INVENTORY.md`
- Agent guide: `apps/agent-orchestrator/docs/AI_AGENT_GUIDE.md`
- Over 120+ specialized slash commands available

### 💡 Key Insights
- This environment is heavily customized for AI-assisted development
- Multiple orchestration layers for complex workflows
- Extensive SDLC automation and quality gates
- Project intelligence provides instant codebase understanding
- MCP servers extend capabilities to external services

Use `/help` for general help or check specific app README files for detailed documentation.
