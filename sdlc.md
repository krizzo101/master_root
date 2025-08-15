# SDLC Project Initialization

You are about to start a new project. Follow these mandatory requirements:

## 📚 Required Reading
First, familiarize yourself with these critical documents:
1. `/home/opsvi/master_root/CLAUDE.md` - Your behavioral directives (BE THE EXPERT)
2. `/docs/guidelines/AGENT_SDLC_GUIDELINES.md` - SDLC phases to follow
3. `/docs/standards/MONOREPO_PROJECT_STANDARDS.md` - Project structure standards
4. `/docs/standards/AGENT_INVOCATION_STANDARDS.md` - You are Claude Code, handle everything

## 🔍 Pre-Development Checks
Before writing ANY code:
1. **Knowledge System**: Query for existing solutions
   ```python
   knowledge_query("search", "[your project terms]")
   ```
2. **Resource Discovery**: Check what exists in libs/
   ```python
   from opsvi_mcp.tools.resource_discovery import ResourceDiscovery
   discovery = ResourceDiscovery()
   discovery.find_resources_for_need("[your functionality]")
   ```

## 📋 SDLC Phases (MANDATORY)
You MUST follow these phases in order:

### 1️⃣ DISCOVERY (Research & Requirements)
- Research current technology (2025 best practices)
- Use: `mcp_web_search`, `tech_docs`, `firecrawl`
- Document requirements
- Define success criteria

### 2️⃣ DESIGN (Architecture)
- Create solution architecture
- Design component boundaries
- Define interfaces
- Document design decisions

### 3️⃣ PLANNING (Task Breakdown)
- Break into <2 hour tasks
- Define test strategy
- Plan rollback approach
- Set success metrics

### 4️⃣ DEVELOPMENT (Implementation)
- Follow TDD (test first)
- Implement incrementally
- Commit after each working piece
- Document as you go

### 5️⃣ TESTING (Validation)
- Unit tests (>80% coverage)
- Integration tests
- Performance tests
- Security validation

### 6️⃣ DEPLOYMENT (Release Prep)
- Prepare deployment package
- Setup monitoring
- Create runbook
- Plan gradual rollout

### 7️⃣ PRODUCTION (Operations)
- Monitor actively
- Document lessons
- Update knowledge system

## 🏗️ Project Structure

### For Shared/Reusable Code → `libs/`
```
libs/opsvi-<functionality>/
├── opsvi_<functionality>/
│   ├── __init__.py
│   ├── core/
│   ├── models/
│   ├── services/
│   └── config.py
├── tests/
├── docs/
└── pyproject.toml
```

### For Applications → `apps/`
```
apps/<app-name>/
├── src/
│   └── <app_name>/
│       ├── __main__.py
│       ├── core/
│       ├── models/
│       ├── services/
│       ├── api/
│       └── config/
├── tests/
├── configs/
└── docs/
```

## 🛠️ Available Tools

### Project Scaffolding
- `project_initializer.py` - Creates standardized project structures
- `resource_discovery.py` - Finds existing components to reuse

### Existing Template System (for reference)
- `/libs/templates.yaml` - 2000+ lines of templates
- `/libs/generate_ecosystem_v2.py` - Mass scaffolding generator
- `/libs/recommended_structure.yaml` - Structure definitions

## ⚡ Key Principles
1. **Research First**: Always check current (2025) best practices
2. **Don't Reinvent**: Check libs/ before building anything
3. **Over-Modularize**: Many small modules > few large ones
4. **Test Everything**: TDD is mandatory, >80% coverage
5. **Document Always**: README, API docs, inline comments
6. **Commit Often**: After each logical unit of work

## 🎯 Remember
- **You are Claude Code** - You handle the entire workflow
- **Be the Expert** - Push back on suboptimal suggestions
- **Follow Standards** - They exist for good reasons
- **Knowledge System** - Query it, use it, update it

Now, what are we building?