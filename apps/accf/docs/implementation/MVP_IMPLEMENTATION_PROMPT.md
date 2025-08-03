<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"ACCF Research Agent - MVP Implementation Prompt","description":"Comprehensive implementation prompt detailing the MVP cleanup and restructuring plan for the ACCF Research Agent project, including objectives, phased implementation plan, quality gates, technical details, and deployment workflow.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to extract a clear hierarchical structure reflecting the MVP implementation plan for the ACCF Research Agent. Identify major thematic sections such as project context, objectives, phased plans, quality gates, technical details including code snippets, and deployment workflows. Ensure line numbers are precise and sections do not overlap. Highlight key elements like code blocks, configuration examples, and critical concepts to facilitate navigation and comprehension. Provide a JSON map that supports efficient referencing of implementation phases, technical details, and success criteria.","sections":[{"name":"Document Title and Introduction","description":"Title and initial heading introducing the ACCF Research Agent MVP implementation prompt.","line_start":7,"line_end":8},{"name":"MVP Cleanup & Restructuring Overview","description":"Overview section containing session context, current state analysis, and MVP objectives to set the stage for the implementation plan.","line_start":9,"line_end":29},{"name":"Implementation Plan","description":"Detailed phased plan outlining the steps for MVP cleanup and restructuring, including kickoff, core refactor, security hardening, testing, and release phases.","line_start":30,"line_end":104},{"name":"Quality Gates","description":"Defines mandatory quality gates that must pass to ensure code quality, security, and performance standards are met.","line_start":105,"line_end":113},{"name":"Technical Implementation Details","description":"Technical section providing code examples and configuration details for refactor patterns, configuration management, Neo4j vector search, and CI workflow.","line_start":114,"line_end":183},{"name":"Success Criteria","description":"Criteria defining the successful completion of the MVP implementation including objectives, quality gates, and deployment success.","line_start":184,"line_end":190},{"name":"Risk Mitigation","description":"Strategies to mitigate risks during implementation such as incremental PRs, smoke tests, rollback plans, and monitoring.","line_start":191,"line_end":196},{"name":"Next Steps","description":"Actionable next steps to begin execution of the MVP plan including phase initiation, project management setup, and meeting cadence.","line_start":197,"line_end":205},{"name":"Closing Call to Action","description":"Final prompt encouraging immediate start with Phase 0 and baseline assessment.","line_start":206,"line_end":208}],"key_elements":[{"name":"Session Context","description":"Defines project details, goals, and focus areas for the MVP implementation.","line":11},{"name":"Current State Analysis","description":"Summary of the existing system architecture, critical issues, and technical debt.","line":16},{"name":"MVP Objectives","description":"List of five key objectives guiding the MVP cleanup and production readiness.","line":23},{"name":"Phase 0: Kick-off & Baseline","description":"Initial phase focused on repository hygiene, baseline assessments, and feature freeze.","line":32},{"name":"Phase 1: Core Refactor","description":"Phase detailing code splitting, quality setup, and dead code removal.","line":44},{"name":"Phase 2: Security & Config Hardening","description":"Phase covering configuration management, secrets handling, and security scanning integration.","line":59},{"name":"Phase 3: Testing & Performance","description":"Phase focused on async testing, mutation testing, Neo4j optimization, and performance validation.","line":74},{"name":"Phase 4: Documentation & Release","description":"Final phase for documentation setup, release tagging, deployment monitoring, and release notes creation.","line":93},{"name":"Quality Gates List","description":"Enumerates all required quality gates including style, formatting, typing, testing, mutation, security, and secrets checks.","line":105},{"name":"Refactor Pattern Code Block","description":"Python code snippet illustrating the AgentOrchestrator class and async workflow execution.","line":116},{"name":"Configuration Management Code Block","description":"Python code snippet showing Pydantic Settings class for environment variable management.","line":129},{"name":"Neo4j Vector Search Code Block","description":"Cypher commands for creating vector indexes and performing vector similarity searches.","line":144},{"name":"GitHub Actions Workflow Code Block","description":"YAML configuration for CI pipeline including linting, testing, mutation testing, security scanning, and Docker build.","line":158},{"name":"Success Criteria Checklist","description":"Checklist confirming completion of objectives, quality gates, performance, security, and deployment success.","line":184},{"name":"Risk Mitigation Strategies","description":"List of risk mitigation tactics including incremental PRs, smoke tests, rollback plans, and monitoring.","line":191},{"name":"Next Steps Action List","description":"Enumerated next steps for project execution and management.","line":197}]}
-->
<!-- FILE_MAP_END -->

# ACCF Research Agent - MVP Implementation Prompt

## 🚀 ACCF Research Agent – MVP Cleanup & Restructuring

### **Session Context**
- **Project**: ACCF Research Agent (Python 3.11, Neo4j GraphRAG, FastAPI, MCP)
- **Goal**: Transform from prototype to production-ready MVP in 4 weeks
- **Focus**: High-impact, low-effort improvements for production readiness

### **Current State Analysis**
- Multi-agent system with 15+ specialized agents
- Neo4j GraphRAG integration with vector search capabilities
- FastAPI async backend with Docker containerization
- MCP (Model Context Protocol) integration
- **Critical Issues**: Large files (consult_agent.py 51KB), scattered configs, hard-coded secrets, missing quality gates

### **MVP Objectives**
1. **O1**: Remove Critical technical-debt hotspots (`consult_agent.py` ≤ 400 LOC)
2. **O2**: Eliminate hard-coded secrets & CVEs (0 secrets in repo, 0 Critical/High CVEs)
3. **O3**: Guarantee baseline performance (P95 latency ≤ 250 ms @ 250 RPS)
4. **O4**: Establish automated SDLC quality gates (CI ≤ 8 min, Ruff/MyPy/pytest-asyncio/mutmut/CodeQL/Safety)
5. **O5**: Enable clear, minimal documentation (Getting Started & Architecture pages)

### **Implementation Plan**

#### **Phase 0: Kick-off & Baseline (½ week)**
1. **Clone repo & create `mvp-cleanup` branch**
2. **Repository Hygiene**:
   - Add comprehensive `.gitignore` rules for Python, logs, secrets
   - Purge `*.log` files using BFG Repo-Cleaner
   - Remove duplicate workspace configurations
3. **Baseline Assessment**:
   - Capture current performance metrics (k6 baseline)
   - Security scan baseline (CodeQL, Safety, Trivy)
   - Code quality baseline (Ruff, MyPy, coverage)
4. **Freeze feature development** - focus only on cleanup/restructuring

#### **Phase 1: Core Refactor (1 week)**
1. **Split `consult_agent.py` (51KB, 1008 lines)**:
   - Create `accf_agents/core/orchestrator.py` (async class)
   - Implement `AgentBase` ABC in `accf_agents/agents/__init__.py`
   - Extract shared utilities to `accf_agents/core/utils.py`
   - Registry auto-discovers agents via entry points
2. **Code Quality Setup**:
   - Add Ruff & Black pre-commit hooks
   - Configure MyPy with strict settings
   - Set up pytest-asyncio for async testing
3. **Remove dead/duplicate code**:
   - Consolidate knowledge update files
   - Remove unused imports and functions
   - Clean up duplicate configurations

#### **Phase 2: Security & Config Hardening (1 week)**
1. **Configuration Management**:
   - Implement Pydantic Settings with environment validation
   - Create `.env.sample` with all required variables
   - Remove hard-coded credentials from code
2. **Secrets Management**:
   - Integrate AWS Secrets Manager for production secrets
   - Local dev uses `.env`; prod fetches secrets via task role
   - Add GitLeaks pre-commit hook
3. **Security Scanning**:
   - Enable CodeQL in GitHub Actions
   - Add Safety for dependency vulnerability scanning
   - Integrate Trivy for container image scanning
   - Configure Dependabot for automated updates

#### **Phase 3: Testing & Performance (1 week)**
1. **Async Testing**:
   - Write pytest-asyncio tests for top 3 API endpoints
   - Add integration tests for Neo4j operations
   - Configure test coverage reporting (target ≥60%)
2. **Mutation Testing**:
   - Initialize mutmut baseline (target ≥60%)
   - Configure mutation testing in CI pipeline
   - Set quality gates for mutation score drops
3. **Neo4j Optimization**:
   - Switch to Neo4j vector similarity search (GraphRAG best practice)
   - Create vector indexes for embeddings
   - Optimize Cypher queries for performance
   - Add connection pooling and async driver usage
4. **Performance Validation**:
   - Run k6 smoke tests
   - Ensure P95 latency ≤ 250 ms @ 250 RPS
   - Monitor memory usage and optimize

#### **Phase 4: Documentation & Release (½ week)**
1. **Documentation Setup**:
   - Bootstrap MkDocs with Material theme
   - Create "Getting Started" guide
   - Document architecture overview
   - Publish to GitHub Pages
2. **Release Process**:
   - Tag `v0.5.0` using semantic-release
   - Monitor blue/green deployment
   - Validate all objectives met
   - Create release notes

### **Quality Gates (All Must Pass)**
- **Style/Lint**: Ruff (0 errors)
- **Formatting**: Black check (0 changes)
- **Typing**: MyPy (0 errors)
- **Unit + Async**: pytest-asyncio (coverage ≥60%)
- **Mutation**: mutmut (Δ coverage ≤2pp)
- **Security**: CodeQL, Safety, Trivy (0 Critical/High)
- **Secrets**: GitLeaks (0 secrets)

### **Technical Implementation Details**

#### **Refactor Pattern**
```python
# accf_agents/core/orchestrator.py
class AgentOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agents = self._discover_agents()

    async def execute_workflow(self, task: Task) -> Result:
        # Async workflow execution
        pass
```

#### **Configuration Management**
```python
# accf_agents/core/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    openai_api_key: str

    class Config:
        env_file = ".env"
```

#### **Neo4j Vector Search**
```cypher
-- Create vector index
CALL db.index.vector.createNodeIndex(
    'embeddings', 'Text', 'embedding', 1536, 'cosine'
);

-- Vector similarity search
MATCH (t:Text) WHERE id(t) = $id
CALL db.index.vector.queryNodes('embeddings', 5, $embedding)
YIELD node, score
RETURN node.text, score
```

#### **GitHub Actions Workflow**
```yaml
# .github/workflows/ci.yml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Install deps
        run: |
          pip install poetry
          poetry install
      - name: Lint & Type
        run: poetry run ruff . && poetry run mypy .
      - name: Test
        run: poetry run pytest -q --asyncio-mode=auto --cov=accf_agents
      - name: Mutate
        run: poetry run mutmut run --paths-to-mutate accf_agents
      - name: Security
        uses: github/codeql-action/init@v3
      - name: Build Image
        run: docker build -t accf/agent:pr-${{github.sha}} .
```

### **Success Criteria**
- ✅ All 5 objectives (O1-O5) completed
- ✅ Quality gates passing consistently
- ✅ Performance targets met
- ✅ Security vulnerabilities eliminated
- ✅ Production deployment successful

### **Risk Mitigation**
- **Incremental PRs**: Small, focused changes to avoid regressions
- **Smoke Tests**: 3 automated tests after each commit
- **Rollback Plan**: Automatic rollback on performance regression
- **Monitoring**: CloudWatch alarms for P95 latency

### **Next Steps**
1. Execute Phase 0 immediately
2. Create Jira board "ACCF-MVP" with swim-lanes per phase
3. Daily 10-min stand-ups
4. Weekly demo/review sessions
5. Close MVP when all objectives met

---

**Ready to execute? Start with Phase 0 and create the baseline assessment.**