# Complete Inventory of Commands and Hooks

Generated: $(date)

## 📂 Slash Commands (.claude/commands/)

### Core Commands
- `audit.md` - Audit system functionality
- `doublecheck.md` - Double-check implementation
- `handoff.md` - Agent handoff procedures (26KB comprehensive guide)
- `review-accuracy.md` - Review accuracy checks
- `showme.md` - Show current state/info
- `verify.md` - Verification procedures
- `verify-all.md` - Comprehensive verification

### Session Management
- `session-start.md` - Start new session
- `session-end.md` - End current session
- `project-session-start.md` - Start project session
- `project-session-end.md` - End project session
- `project-session-current.md` - Show current session
- `project-session-list.md` - List all sessions
- `project-session-update.md` - Update session
- `project-session-help.md` - Session help

### Development Commands
- `commit.md` - Git commit helper (7.5KB)
- `dump.md` - Dump current state
- `context-prime.md` - Prime context
- `context-prime-enhanced.md` - Enhanced context priming
- `docs-comprehensive.md` - Generate comprehensive docs
- `tdd.md` - Test-driven development

### SDLC Commands (Software Development Life Cycle)
- `sdlc.md` - Main SDLC workflow (19KB)
- `sdlc-gates.md` - Quality gates
- `sdlc-task-enforcer.md` - Task enforcement
- `SDLC_DEBUG_LOGGING.md` - Debug logging guide
- `SDLC_PHASE_CHECKLIST.md` - Phase checklist

### SC Commands (Structured Commands)
- `sc-01_brainstorm-feature.md` - Feature brainstorming
- `sc-02_feature-proposal.md` - Feature proposals
- `sc-03_feature-to-prd.md` - Feature to PRD conversion
- `sc-04_feature-planning.md` - Feature planning (25KB)
- `sc-05_implement.md` - Implementation
- `sc-05_implement_v2.md` - Implementation v2
- `sc-add-react-feature.md` - Add React features
- `sc-create-command.md` - Create new commands
- `sc-e2e-mcp-test.md` - End-to-end MCP testing
- `sc-generate-react-app.md` - Generate React apps
- `sc-implement-next.md` - Next.js implementation
- `sc-mode-baseline.md` - Baseline mode
- `sc-mode-init.md` - Initialize mode
- `sc-mode-test.md` - Test mode
- `sc-mode-update.md` - Update mode
- `sc-root_cause.md` - Root cause analysis
- `sc-task_ui.md` - Task UI management

### X-Commands (Extended/Expert Commands)
- `xact.md` - Actions (23KB)
- `xanalytics.md` - Analytics
- `xanalyze.md` - Analysis
- `xapi.md` - API documentation
- `xarchitecture.md` - Architecture docs (20KB)
- `xatomic.md` - Atomic operations
- `xaws.md` - AWS operations
- `xcicd.md` - CI/CD pipelines (11KB)
- `xcommit.md` - Advanced commits
- `xcompliance.md` - Compliance checks
- `xconfig.md` - Configuration
- `xconstraints.md` - Constraints
- `xcoverage.md` - Code coverage
- `xdb.md` - Database operations
- `xdebug.md` - Debugging
- `xdesign.md` - Design docs
- `xdocs.md` - Documentation
- `xevaluate.md` - Evaluation
- `xfootnote.md` - Footnotes/annotations
- `xgenerate.md` - Code generation
- `xgit.md` - Git operations
- `xgovernance.md` - Governance
- `xgreen.md` - Green/sustainable
- `xiac.md` - Infrastructure as Code
- `xincident.md` - Incident management
- `xinfra.md` - Infrastructure
- `xknowledge.md` - Knowledge base
- `xmaturity.md` - Maturity assessment
- `xmetrics.md` - Metrics
- `xmonitoring.md` - Monitoring
- `xnew.md` - New features (29KB)
- `xobservable.md` - Observability
- `xoidc.md` - OIDC/Auth
- `xoptimize.md` - Optimization
- `xperformance.md` - Performance
- `xpipeline.md` - Pipeline management
- `xplanning.md` - Planning
- `xpolicy.md` - Policy management
- `xproduct.md` - Product features
- `xquality.md` - Quality assurance
- `xreadiness.md` - Readiness checks
- `xred.md` - Red/critical items
- `xrefactor.md` - Refactoring
- `xrelease.md` - Release management
- `xrisk.md` - Risk assessment
- `xrules.md` - Rules engine
- `xsandbox.md` - Sandbox environment
- `xscan.md` - Security scanning
- `xsecurity.md` - Security
- `xsetup.md` - Setup procedures
- `xspec.md` - Specifications
- `xtdd.md` - Test-driven development
- `xtemplate.md` - Templates
- `xtest.md` - Testing
- `xtrace.md` - Tracing (8KB)
- `xux.md` - User experience
- `xvalidate.md` - Validation
- `xworkflow.md` - Workflows

### Monitoring Commands
- `monitor-debug.md` - Debug monitoring
- `five.md` - Quick five-point check
- `five-monitored.md` - Monitored five-point check

### Other Commands
- `implementation.md` - Implementation guide
- `security-audit.md` - Security auditing
- `v-add-new-resource.md` - Add new resources
- `AGENT_ONBOARDING.md` - Agent onboarding guide
- `QUICK_REFERENCE.md` - Quick reference

### Newly Created (This Session)
- `orchestrator-quickstart.md` - Agent Orchestrator quick start ✅

## 🔧 Executable Scripts in commands/
- `compact-with-export.sh` - Compact with export
- `handoff.py` - Python handoff script
- `plan-to-tasks.py` - Convert plans to tasks
- `sdlc-execute-phase.py` - Execute SDLC phases
- `sdlc-phase-executor-v2.py` - Phase executor v2
- `sdlc-phase-executor.sh` - Shell phase executor
- `sdlc-postmortem.sh` - Postmortem analysis (10KB)
- `sdlc-preflight.sh` - Preflight checks
- `sdlc-preflight-enhanced.sh` - Enhanced preflight
- `sdlc-session-exporter.py` - Export sessions
- `sdlc-tool-verification.py` - Verify tools
- `sdlc-violation-analyzer.py` - Analyze violations (19KB)
- `sdlc_mcp_debug_wrapper.py` - MCP debug wrapper
- `tdd-monitored.sh` - Monitored TDD
- `team-orchestrate.py` - Team orchestration (11KB)

## 🪝 Hooks Configuration

### Check for hooks:
```bash
find /home/opsvi/master_root/.claude -name "*hook*" -type f 2>/dev/null
```

### Hooks Created This Session (Not Found on Disk):
- `.claude/hooks/proj_intel_hooks.json` - Project intelligence hooks (missing)

## 📦 MCP Servers (.mcp.json)
- `firecrawl` - Web scraping with Firecrawl API
- `tech_docs` - Technical documentation (@upstash/context7-mcp)
- `web_search` - Brave search API
- `knowledge` - Knowledge base (Neo4j-backed, Python-based)
- `thinking` - Thinking/reasoning server (OpenAI-powered)
- `time` - Time utilities (time-mcp)
- `shell_exec` - Shell command execution

## 🤖 Subagents (.claude/subagents/)
- `project-analyst.md` - Project analysis specialist (created this session, missing)

## 📊 Statistics
- **Total Commands**: 120+ markdown files
- **Executable Scripts**: 16 scripts
- **X-Commands**: 44 extended commands
- **SC-Commands**: 16 structured commands
- **Largest Commands**:
  - xnew.md (29KB)
  - handoff.md (26KB)
  - sc-04_feature-planning.md (25KB)
  - xact.md (23KB)
  - xarchitecture.md (20KB)
  - sdlc.md (19KB)

## ⚠️ Missing Items (Created This Session)
These were created but are not found on disk:
1. Orchestrator commands (4 total):
   - orchestrator-quickstart.md ✅ (just recreated)
   - orchestrator-document.md ❌
   - orchestrator-analyze.md ❌
   - orchestrator-resume.md ❌

2. Project Intelligence commands (5 total):
   - proj-intel-quickstart.md ❌
   - proj-intel-generate.md ❌
   - proj-intel-analyze.md ❌
   - proj-intel-search.md ❌
   - proj-intel-refresh.md ❌

3. Integration files:
   - .claude/hooks/proj_intel_hooks.json ❌
   - .claude/subagents/project-analyst.md ❌
   - .claude/PROJ_INTEL_INTEGRATION.md ❌

4. Scripts:
   - /home/opsvi/master_root/scripts/proj_intel_mcp_server.py ❌
   - /home/opsvi/master_root/scripts/proj_intel_context_loader.py ❌

## 📝 Notes
- Commands use frontmatter for metadata (description, allowed-tools, etc.)
- Many commands support $ARGUMENTS parameter substitution
- X-commands appear to be expert/extended functionality
- SC-commands are structured/systematic workflows
- SDLC commands focus on development lifecycle management
