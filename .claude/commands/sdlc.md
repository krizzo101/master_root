# SDLC Project Initialization

This command initiates a new project following strict SDLC phases and monorepo standards.

## Usage
```
/sdlc <project description>
```

## What This Command Does
1. **Initializes SDLC tracking** for your project
2. **Enforces phase progression** (can't skip ahead)
3. **Creates project structure** in the correct location
4. **Tracks deliverables** for each phase
5. **Ensures standards compliance** throughout

You are about to start a new project. Follow these mandatory requirements:

## 📚 Required Reading
First, familiarize yourself with these critical documents:
1. `/home/opsvi/master_root/CLAUDE.md` - Your behavioral directives (BE THE EXPERT)
2. `/docs/guidelines/AGENT_SDLC_GUIDELINES.md` - SDLC phases to follow
3. `/docs/standards/MONOREPO_PROJECT_STANDARDS.md` - Project structure standards
4. `/docs/standards/AGENT_INVOCATION_STANDARDS.md` - You are Claude Code, handle everything
5. `/docs/standards/GIT_WORKFLOW_STANDARDS.md` - Git branching and commit standards

## 🌿 Git Setup (MANDATORY FIRST STEP)
```bash
# Start from main branch
git checkout main
git pull origin main

# Create feature branch for this project
git checkout -b feature/<project-name>

# Verify branch
git branch --show-current
```

## 🔍 Pre-Development Checks
Before writing ANY code:
1. **Knowledge System**: Query for existing solutions
   ```python
   # Check for existing knowledge using Knowledge MCP tools
   result = mcp__knowledge__knowledge_query(
       query_type="search",
       query_text="your search terms",
       knowledge_type="WORKFLOW"  # or ERROR_SOLUTION, CODE_PATTERN, etc.
   )
2. **Resource Discovery**: Check what exists in libs/
   ```python
   from opsvi_mcp.tools.resource_discovery import ResourceDiscovery
   discovery = ResourceDiscovery()
   discovery.find_resources_for_need("[your functionality]")
   ```

## 📋 SDLC Phases (MANDATORY)
You MUST follow these phases in order and produce concrete deliverables.

### Phase Tracking with SDLC Enforcer
```python
# Initialize enforcer and create project at start
from libs.opsvi_mcp.tools.sdlc_enforcer_scoped import ScopedSDLCEnforcer
enforcer = ScopedSDLCEnforcer()
project = enforcer.create_project(
    project_name="[project-name]",
    description="[project description]",
    root_path="apps/[project-name]"
)

# Progress through phases
enforcer.advance_phase(project.project_id)  # After completing each phase
enforcer.get_project_status(project.project_id)  # Check current status
```

### 1️⃣ DISCOVERY (Research & Requirements)
- Research current technology (2025 best practices)
- Use tools:
  - `mcp__mcp_web_search__brave_web_search()` - Search for current info
  - `mcp__tech_docs__get-library-docs()` - Get library documentation
  - `mcp__firecrawl__firecrawl_scrape()` - Scrape official docs
- **Deliverable**: Requirements document with:
  - Problem statement
  - User stories/use cases
  - Functional requirements
  - Non-functional requirements (performance, security)
  - Success criteria (measurable)
- **Git Commit**:
  ```bash
  git add docs/requirements/<project>.md
  git commit -m "docs: add requirements for <project>
  
  - Problem statement defined
  - User stories documented
  - Success criteria established"
  ```

### 2️⃣ DESIGN (Architecture)
- Create solution architecture
- Design component boundaries
- Define interfaces
- **Deliverable**: Design document with:
  - Architecture diagram
  - Component descriptions
  - Data flow diagrams
  - API specifications
  - Technology choices with justification

### 3️⃣ PLANNING (Task Breakdown)
- Break into <2 hour tasks
- Define test strategy
- Plan rollback approach
- Set success metrics

### 4️⃣ DEVELOPMENT (Implementation)
- Follow TDD (test first)
- Implement incrementally
- **Commit after EACH working piece**:
  ```bash
  # After each feature/component
  git add -A
  git commit -m "feat: implement <specific-feature>
  
  - Added X functionality
  - Integrated with Y
  - Handles Z edge cases"
  ```
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
- Update knowledge system:
  ```python
  # Store successful patterns and workflows
  result = mcp__knowledge__knowledge_store(
      knowledge_type="WORKFLOW",
      content="Description of successful implementation pattern",
      confidence_score=0.95
  )
  ```

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

### SDLC Enforcement
- `/libs/opsvi_mcp/tools/sdlc_enforcer_scoped.py` - Enforces SDLC phases
  ```python
  from libs.opsvi_mcp.tools.sdlc_enforcer_scoped import ScopedSDLCEnforcer
  enforcer = ScopedSDLCEnforcer()
  # Create project with SDLC tracking
  project = enforcer.create_project(
      project_name="your-project",
      description="Project description",
      root_path="apps/your-project"
  )
  ```

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