# File Reorganization Plan for Project Root

## Overview
The project root contains many files that should be organized into appropriate directories for better structure and maintainability.

## Files to Keep in Root
These files should remain in the project root:
- `UNIFIED_CONTEXT_SYSTEM.md` - Core architecture document (as requested)
- `.env`, `.env.example` - Environment configuration
- `.gitignore` - Git configuration
- `.editorconfig` - Editor configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `pyproject.toml` - Python project configuration
- `uv.lock` - UV package lock file
- `README.md` - Main project README
- `CLAUDE.md` - Agent bootstrap instructions (critical)
- `.mcp.json`, `.mcp-enhanced.json` - MCP server configurations

## Documentation Files → `/docs/`

### Architecture & Design Documents → `/docs/architecture/`
- `AGENT_CAPABILITY_MATRIX.md`
- `AGENT_ONBOARDING_SDLC.md`
- `CODEBASE_INTELLIGENCE_REPORT.md`
- `ECOSYSTEM_MATURATION_BLUEPRINT.md`
- `PATTERN_ENGINE_EXTRACTION_SUMMARY.md`

### Knowledge System Documentation → `/docs/knowledge/`
- `KNOWLEDGE_BASE_PATTERNS.md`
- `KNOWLEDGE_SYSTEM_ANALYSIS.md`
- `KNOWLEDGE_TOOL_CURRENT_STATUS.md`
- `KNOWLEDGE_TOOL_ENHANCEMENT_PROPOSAL.md`
- `KNOWLEDGE_TOOL_FIX_PLAN.md`
- `KNOWLEDGE_TOOL_SOLUTION_SUMMARY.md`
- `2025-08-24-knowledge_KB_master_root_migration_etc.txt`

### MCP Documentation → `/docs/mcp/`
- `MCP_PARAMETER_ANALYSIS.md`
- `MCP_SERVER_FIX_REQUIREMENTS.md`
- `mcp_e2e_test_20250825.md`

### Operations & Maintenance → `/docs/operations/`
- `CLEANUP_PLAN.md`
- `CLEANUP_RESULTS.md`
- `CONTEXT_STATE.md`
- `MERGE_PLAN.md`
- `MONITORING_QUICK_START.md`
- `QUICK_START.md`
- `SYNC_REPORT.md`
- `TEST_COVERAGE_MAP.md`

### Reports → `/docs/reports/`
- `PR_DESCRIPTION.md`
- `hook_test_report.md`

### Legacy/Backup → `/docs/legacy/`
- `CLAUDE-ENHANCED.md`
- `CLAUDE copy.md`
- `CLAUDE.md.backup.20250824_123411`
- `CLAUDE.local.md` (empty file)

## Test Files → `/tests/`

### MCP Tests → `/tests/mcp/`
- `test_mcp_direct.py`
- `test_mcp_init.py`
- `test_mcp_params.py`
- `test_mcp_store.py`
- `test_mcp_validation.py`
- `test_complete_mcp_parameters.py`
- `test_fastmcp_direct.py`
- `test_fastmcp_coercion.py`
- `test_coercion_fix.py`

### Agent Tests → `/tests/agents/`
- `test_coder_agent.py`
- `test_coder_comprehensive.py`
- `test_devils_advocate.py`
- `test_parallel_agents.py`
- `test_agent_monitoring.py`
- `test_enhanced_sdlc.py`

### Hook Tests → `/tests/hooks/`
- `test_hook.py`
- `test_hooks.py`
- `test_hook_minimal.py`

### Knowledge System Tests → `/tests/knowledge/`
- `test_smart_query.py`
- `test_smart_verbose.py`
- `test_smart_enrichment.py`
- `test_enrichment_debug.py`
- `test_enrichment_path.py`

### Integration Tests → `/tests/integration/`
- `test_phase2_integration.py`
- `test_enhanced_context.py`
- `test_session_detection.py`

### API Tests → `/tests/api/`
- `test_simple_api.py`
- `test_simple_responses.py`

### Misc Tests → `/tests/misc/`
- `test_gpt5_nano.py`
- `test_fixed_nano.py`
- `test_hello_world.py`
- `test_ok.py`

## Script Files → `/scripts/`

### Deployment Scripts → `/scripts/deployment/`
- `START_AUTONOMOUS.sh`
- `LAUNCH_MATURATION.sh`
- `run_monitored_sdlc.sh`

### Testing Scripts → `/scripts/testing/`
- `run_tests.sh`
- `run_test.sh`
- `test_hooks.sh`
- `test_all_hooks.sh`
- `test_hook_environment.sh`
- `comprehensive_hook_test.sh`
- `final_hook_verification.sh`
- `test_bypass.sh`
- `test_optimizer_modes.sh`

### Utility Scripts → `/scripts/utils/`
- `configure_tokens.sh`
- `fix_neo4j_config.sh`
- `quiet_commit.sh`

### Demo Scripts → `/scripts/demo/`
- `true_power_demo.sh`

## Other Files

### Python Cache/Coverage → Remove
- `.coverage`
- `=1.40.0` (empty file)

### IDE Configuration → Keep in root
- `.cursorignore`
- `.fileignore`
- `.mcp.recovered.json`

## Implementation Commands

```bash
# Create directory structure
mkdir -p docs/{architecture,knowledge,mcp,operations,reports,legacy}
mkdir -p tests/{mcp,agents,hooks,knowledge,integration,api,misc}
mkdir -p scripts/{deployment,testing,utils,demo}

# Move documentation files
mv AGENT_CAPABILITY_MATRIX.md AGENT_ONBOARDING_SDLC.md CODEBASE_INTELLIGENCE_REPORT.md \
   ECOSYSTEM_MATURATION_BLUEPRINT.md PATTERN_ENGINE_EXTRACTION_SUMMARY.md \
   docs/architecture/

mv KNOWLEDGE_*.md 2025-08-24-knowledge_*.txt docs/knowledge/

mv MCP_*.md mcp_e2e_test_*.md docs/mcp/

mv CLEANUP_*.md CONTEXT_STATE.md MERGE_PLAN.md MONITORING_QUICK_START.md \
   QUICK_START.md SYNC_REPORT.md TEST_COVERAGE_MAP.md docs/operations/

mv PR_DESCRIPTION.md hook_test_report.md docs/reports/

mv CLAUDE-ENHANCED.md "CLAUDE copy.md" CLAUDE.md.backup.* CLAUDE.local.md docs/legacy/

# Move test files
mv test_mcp*.py test_*mcp*.py test_fastmcp*.py test_coercion*.py tests/mcp/
mv test_coder*.py test_devils*.py test_parallel*.py test_agent*.py test_enhanced_sdlc.py tests/agents/
mv test_hook*.py tests/hooks/
mv test_smart*.py test_enrichment*.py tests/knowledge/
mv test_phase2*.py test_enhanced_context.py test_session*.py tests/integration/
mv test_simple*.py tests/api/
mv test_gpt5*.py test_fixed*.py test_hello*.py test_ok.py tests/misc/

# Move script files
mv START_AUTONOMOUS.sh LAUNCH_MATURATION.sh run_monitored_sdlc.sh scripts/deployment/
mv run_test*.sh test_*.sh comprehensive_*.sh final_*.sh scripts/testing/
mv configure_tokens.sh fix_neo4j_config.sh quiet_commit.sh scripts/utils/
mv true_power_demo.sh scripts/demo/

# Clean up unnecessary files
rm -f .coverage "=1.40.0"
```

## Benefits of This Organization

1. **Clear Structure**: Files are logically grouped by purpose
2. **Easy Navigation**: Developers can quickly find what they need
3. **Maintainability**: Related files are kept together
4. **Clean Root**: Only essential configuration files remain in root
5. **Scalability**: Easy to add new categories as the project grows

## Notes

- The `UNIFIED_CONTEXT_SYSTEM.md` stays in root as requested
- `CLAUDE.md` must stay in root as it's the bootstrap instructions
- MCP configuration files stay in root for tool discovery
- All test files are organized by their testing domain
- Scripts are categorized by their purpose
- Documentation is organized by topic area