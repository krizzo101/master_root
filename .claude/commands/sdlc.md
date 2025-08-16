# SDLC Project Initialization with Agent Support

This command initiates a new project following strict SDLC phases with appropriate agent support.

## 🎯 Core Principles

### Mandatory Requirements
1. **Check for existing implementations first** - Always use libs/ packages when available
2. **Build reusable components** - Everything goes in libs/ or apps/ with proper structure
3. **Follow current best practices** - Research 2025 patterns, not outdated approaches
4. **Complete each phase fully** - No skipping or partial deliverables
5. **Test everything thoroughly** - Components must actually work, not "mostly work"

## Usage
```
/sdlc <project description>
```

## 🤖 Agent Strategy for SDLC Phases

### Phase-Specific Agent Profiles
Each SDLC phase has a dedicated agent profile that should be loaded:

| Phase | Agent Profile | Purpose |
|-------|------------|---------|
| **DISCOVERY** | `sdlc-discovery` | Understand requirements, research solutions |
| **DESIGN** | `sdlc-design` | Create robust, scalable architecture |
| **PLANNING** | `sdlc-planning` | Break down into actionable tasks |
| **DEVELOPMENT** | `sdlc-development` | Implement clean, tested code |
| **TESTING** | `sdlc-testing` | Validate all requirements met |
| **DEPLOYMENT** | `sdlc-deployment` | Prepare for production |
| **PRODUCTION** | `sdlc-production` | Final review and handover |

**Loading Phase Profiles**: Read the appropriate profile from `.claude/agents/` at the start of each phase to align your approach with phase-specific requirements.

## What This Command Does
1. **Initializes SDLC tracking** for your project
2. **Enforces phase progression** (can't skip ahead)
3. **Creates project structure** in the correct location
4. **Tracks deliverables** for each phase
5. **Ensures standards compliance** throughout
6. **Leverages specialized agents** for each phase

## 📚 Required Reading
First, familiarize yourself with these critical documents:
1. `/home/opsvi/master_root/CLAUDE.md` - Your behavioral directives (BE THE EXPERT)
2. `/home/opsvi/master_root/docs/guidelines/AGENT_SDLC_GUIDELINES.md` - SDLC phases to follow
3. `/home/opsvi/master_root/docs/standards/MONOREPO_PROJECT_STANDARDS.md` - Project structure standards
4. `/home/opsvi/master_root/docs/standards/AGENT_INVOCATION_STANDARDS.md` - You are Claude Code, handle everything
5. `/home/opsvi/master_root/docs/standards/GIT_WORKFLOW_STANDARDS.md` - Git branching and commit standards

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

## 🔍 MANDATORY Pre-Development Checks (CANNOT SKIP)

### 1. Knowledge System Query
```python
# Check for existing knowledge using Knowledge MCP tools
result = mcp__knowledge__knowledge_query(
    query_type="search",
    query_text="your search terms",
    knowledge_type="WORKFLOW"  # or ERROR_SOLUTION, CODE_PATTERN, etc.
)
```

### 2. Resource Discovery - Check Existing Code

**IMPORTANT**: The resource discovery MCP server must be configured in your MCP settings to use these tools.

```python
# MANDATORY: Search for existing functionality in libs/
result = mcp__resource_discovery__search_resources(
    functionality="description of what you need",
    search_depth=2,
    include_tests=False
)
# IF FOUND: You MUST use it or document why it won't work

# Check if specific package exists
package_info = mcp__resource_discovery__check_package_exists("opsvi-llm")
# IF EXISTS: You MUST use this package

# Find similar code patterns
similar = mcp__resource_discovery__find_similar_functionality(
    code_snippet="def authenticate_user(username, password):",
    language="python"
)
# IF SIMILAR EXISTS: You MUST extend/compose, not duplicate

### ⛔ STOP GATE: Duplication Check
If similar functionality exists:
1. You MUST use the existing implementation
2. OR extend it to add missing features
3. OR explicitly document why it cannot be used
4. NEVER create a parallel implementation
```

**Note**: These are MCP tools provided by the resource_discovery server. Do NOT try to import Python modules directly.

### 3. External Research and Parallel Processing

#### Research Current Best Practices (MANDATORY)
```python
# Use MCP tools for research - don't skip this!
mcp__mcp_web_search__brave_web_search(
    query="[technology] best practices 2025",
    count=10
)

mcp__tech_docs__get-library-docs(
    context7CompatibleLibraryID="/org/library",
    topic="specific feature"
)
```

#### Parallel Agent Spawning with Task Tool
**Use the Task tool to spawn multiple agents for parallel work:**

```python
# Spawn parallel research agents
Task(
    description="Research authentication patterns",
    subagent_type="research-genius",  # Or use claude-code for complex tasks
    prompt="Find current best practices for JWT authentication in 2025"
)

# For production work
mcp__claude-code__claude_run(
    task="Create JWT authentication with refresh tokens",
    outputFormat="json",
    permissionMode="bypassPermissions"
)
```

**Remember**: Use Task tool whenever you have independent work that can be parallelized. This significantly speeds up development.

## 📋 SDLC Phases with Agent Support

### Phase Tracking and Project Management

**DO NOT import Python modules directly!** Use MCP tools and TodoWrite for tracking.

```python
# Track your progress through SDLC phases
TodoWrite(todos=[
    {"id": "1", "content": "DISCOVERY: Gather requirements", "status": "in_progress"},
    {"id": "2", "content": "DESIGN: Create architecture", "status": "pending"},
    {"id": "3", "content": "PLANNING: Break down tasks", "status": "pending"},
    {"id": "4", "content": "DEVELOPMENT: Implement code", "status": "pending"},
    {"id": "5", "content": "TESTING: Validate solution", "status": "pending"},
    {"id": "6", "content": "DEPLOYMENT: Prepare production", "status": "pending"},
    {"id": "7", "content": "PRODUCTION: Final review", "status": "pending"}
])

# Each phase has specific deliverables - mark complete when done
```

### 1️⃣ DISCOVERY (Research & Requirements)

#### Phase Entry Checklist
- [ ] Git feature branch created
- [ ] Knowledge system queried
- [ ] Resource discovery completed
- [ ] Current best practices researched

#### Load Phase Profile
```python
# Read the SDLC phase profile to align your approach
Read(".claude/agents/sdlc-discovery.md")
```

#### Agent Support
```python
# For parallel research tasks
Task(
    description="Research phase",
    subagent_type="research-genius",  # Can also use claude-code
    prompt="""
    Research current best practices for [technology/framework] in 2025.
    Find:
    - Latest versions and breaking changes
    - Security best practices
    - Performance optimization techniques
    - Common pitfalls to avoid
    - Industry standard patterns
    """
)
```

#### Activities
- Research current technology (2025 best practices)
- Use tools:
  - `mcp__mcp_web_search__brave_web_search()` - Search for current info
  - `mcp__tech_docs__get-library-docs()` - Get library documentation
  - `mcp__firecrawl__firecrawl_scrape()` - Scrape official docs

#### Required Deliverables (MUST complete all)
- [ ] `docs/requirements/<project>.md` created with:
  - Problem statement
  - User stories/use cases
  - Functional requirements
  - Non-functional requirements
  - Interface specifications
  - Success criteria
- [ ] Existing solutions documented (if found)
- [ ] Decision to reuse or build new justified
- [ ] 2025 best practices researched and documented

#### Git Commit
```bash
git add docs/requirements/<project>.md
git commit -m "docs: add requirements for <project>

- Problem statement defined
- User stories documented
- Success criteria established"
```

### 2️⃣ DESIGN (Architecture)

#### Phase Gate: Cannot proceed unless
- [ ] Requirements document exists and is complete
- [ ] Existing solutions have been evaluated
- [ ] Decision to build new or extend existing is documented

#### Agent Support
```python
Task(
    description="Architecture design",
    subagent_type="solution-architect",
    prompt="""
    Design the architecture for [project description].
    Include:
    - Component architecture diagram
    - Technology stack selection with justification
    - Interface specifications
    - Data flow diagrams
    - Integration points
    - Scalability considerations
    """
)
```

#### Activities
- Create solution architecture
- Design component boundaries
- Define interfaces

#### Required Deliverables (MUST complete all)
- [ ] `docs/design/<project>.md` created with:
  - Architecture diagram (mermaid or similar)
  - Public API specifications
  - Component descriptions
  - Data flow diagrams
  - Integration examples (min 2)
  - Technology stack with justification
- [ ] Design reviewed (use reviewer-critic agent)
- [ ] Interfaces validated for reusability

#### Git Commit
```bash
git add docs/design/<project>.md
git commit -m "docs: add architecture design for <project>

- Component architecture defined
- Technology stack selected
- Interfaces specified"
```

### 3️⃣ PLANNING (Task Breakdown)

#### Agent Support
```python
Task(
    description="Task planning",
    subagent_type="business-analyst",
    prompt="""
    Break down the implementation into manageable tasks.
    Create:
    - Task list with time estimates (<2 hours each)
    - Dependencies between tasks
    - Test strategy for each component
    - Risk assessment and mitigation plans
    - Success metrics for each task
    """
)
```

#### Activities
- Break into <2 hour tasks
- Define test strategy
- Plan rollback approach
- Set success metrics

### 4️⃣ DEVELOPMENT (Implementation)

#### Phase Gate: Cannot proceed unless
- [ ] Design document complete and reviewed
- [ ] Task breakdown complete (<2 hour tasks)
- [ ] Test strategy defined

#### 🚨 IMPORTANT: For AI-Powered Applications
**When building applications that need AI/agent capabilities:**
- Claude Code can handle all agent needs via MCP tools
- Call `mcp__claude-code__claude_run` for synchronous tasks
- Call `mcp__claude-code__claude_run_async` for parallel execution
- These tools handle all AI agent functionality needed

#### Load Phase Profile
```python
# Read the SDLC phase profile to align your approach
Read(".claude/agents/sdlc-development.md")
```

#### Agent Support
```python
# For development tasks
mcp__claude-code__claude_run(
    task="""
    Implement [specific component/feature].
    Requirements:
    - Follow TDD (write tests first)
    - Use type hints throughout
    - Add comprehensive docstrings
    - Follow project coding standards
    - Implement error handling
    - Add logging where appropriate
    """,
    outputFormat="json",
    permissionMode="bypassPermissions"
)
```

#### Activities
- Follow TDD (test first)
- Implement incrementally
- **Commit after EACH working piece**:
  ```bash
  git add -A
  git commit -m "feat: implement <specific-feature>

  - Added X functionality
  - Integrated with Y
  - Handles Z edge cases"
  ```
- Document as you go

### 5️⃣ TESTING (Validation)

#### Phase Gate: Cannot proceed unless
- [ ] All code implemented
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests written
- [ ] All tests passing

#### Agent Support
```python
Task(
    description="Comprehensive testing",
    subagent_type="qa-testing-guru",
    prompt="""
    Create and execute comprehensive tests for [project].
    Include:
    - Unit tests with >80% coverage
    - Integration tests for component interactions
    - E2E tests for complete workflows
    - Performance benchmarks
    - Security vulnerability scanning
    - Edge case testing
    """
)
```

#### Activities
- Unit tests (>80% coverage)
- Integration tests (component interactions)
- End-to-end tests (complete workflows)
- Performance benchmarks
- Security validation
- Build sample integration to validate usability

### 6️⃣ DEPLOYMENT (Release Prep)

#### Agent Support
```python
Task(
    description="Deployment preparation",
    subagent_type="solution-architect",
    prompt="""
    Prepare deployment strategy for [project].
    Include:
    - Containerization (Dockerfile)
    - CI/CD pipeline configuration
    - Environment configurations
    - Monitoring and alerting setup
    - Rollback procedures
    - Documentation for operators
    """
)
```

#### Activities
- Prepare deployment package
- Setup monitoring
- Create runbook
- Plan gradual rollout

### 7️⃣ PRODUCTION (Operations)

#### Agent Support
```python
Task(
    description="Final review",
    subagent_type="reviewer-critic",
    prompt="""
    Perform final review of [project].
    Evaluate:
    - Code quality and maintainability
    - Documentation completeness
    - Test coverage and quality
    - Performance metrics
    - Security posture
    - Adherence to standards
    Provide actionable feedback for improvements.
    """
)
```

#### Activities
- Monitor performance
- Document lessons learned
- Create integration guide for future users
- Update knowledge system:
  ```python
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
  ```

### Task Tool for Agent Invocation
```python
# General pattern for using specialized agents
Task(
    description="Short description",
    subagent_type="agent-type",  # See agent list above
    prompt="Detailed instructions for the agent"
)
```

### Available Agent Types
- `general-purpose` - General tasks
- `research-genius` - Information discovery
- `solution-architect` - System design
- `business-analyst` - Requirements analysis
- `requirements-analyst` - Detailed requirements
- `development-specialist` - Code implementation
- `qa-testing-guru` - Testing strategies
- `reviewer-critic` - Code review
- `technical-writer` - Documentation
- `refactoring-master` - Code refactoring

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
7. **Use Agents**: Leverage specialized agents for each phase

## 🛑 Definition of "Done"

### Each phase must be complete before proceeding:
1. **All deliverables created** - No missing documents or code
2. **Tests pass** - All unit, integration, and e2e tests green
3. **Documentation complete** - README, API docs, examples included
4. **Code follows standards** - Linting, type hints, proper structure
5. **Peer review passed** - Use reviewer-critic agent if needed
6. **Integration verified** - Can be imported and used by other projects
7. **Knowledge captured** - Lessons learned documented in knowledge system

## Next Steps
After reading this document:
1. Begin with Phase 1: DISCOVERY
2. Complete ALL activities and deliverables for each phase
3. Do not proceed to next phase until current phase is complete
4. Use the specified MCP tools and agents for each phase

## Common Issues and Solutions

### Pre-commit Hook Errors
If you get pre-commit errors, ensure `.pre-commit-config.yaml` exists:
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Or bypass temporarily
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "message"
```

### Resource Discovery
Use the Task tool with research-genius agent instead of direct Python imports:
```python
# Don't use: from opsvi_mcp.tools.resource_discovery import ResourceDiscovery
# Use: Task tool as shown above
```

Now, what are we building?
