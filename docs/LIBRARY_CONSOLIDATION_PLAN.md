# Library Consolidation Plan

## Executive Summary

We have 36 opsvi libraries, but only 1 is complete (opsvi-mcp) and only 3 have setup.py files. Given our standardization on claude-code agent and opsvi-llm interfaces, we can consolidate to ~15 essential libraries.

## Current State Analysis

### 📊 Statistics
- **Total Libraries**: 36
- **Total Python Files**: 4,102
- **Complete Libraries**: 1/36 (opsvi-mcp)
- **Libraries with setup.py**: 3/36
- **Test Coverage**: 398 test files across all libs

### 🎯 Key Findings
1. **Heavy Duplication**: Multiple libraries serve similar purposes
2. **Incomplete Development**: Most libraries lack setup.py and proper structure
3. **Large Monoliths**: opsvi-docs (1590 files), opsvi-ecosystem (1126 files), opsvi-asea (381 files)
4. **Standardization Opportunity**: Can consolidate around claude-code + opsvi-llm

## Consolidation Strategy

### ✅ KEEP - Core Infrastructure (5 libraries)

| Library | Purpose | Action Required |
|---------|---------|-----------------|
| **opsvi-core** | Core abstractions and base classes | Add setup.py, complete tests |
| **opsvi-data** | Data models and schemas | Add setup.py, integrate with Neo4j |
| **opsvi-fs** | File system operations | Add setup.py, complete implementation |
| **opsvi-auth** | Authentication and authorization | Add setup.py, complete OAuth2 |
| **opsvi-api** | API client and server utilities | Add setup.py, add FastAPI support |

### ✅ KEEP - Standardized Interfaces (3 libraries)

| Library | Purpose | Action Required |
|---------|---------|-----------------|
| **opsvi-llm** | Unified LLM interfaces (Anthropic, OpenAI, etc.) | Complete providers, add setup.py |
| **opsvi-mcp** | Claude-code MCP server | ✓ Already complete |
| **opsvi-interfaces** | CLI and config interfaces | Complete implementation |

### ✅ KEEP - Essential Utilities (4 libraries)

| Library | Purpose | Action Required |
|---------|---------|-----------------|
| **opsvi-visualization** | DOT, HTML, diagram generation | Add setup.py |
| **opsvi-monitoring** | Metrics, logging, observability | Add setup.py, integrate OpenTelemetry |
| **opsvi-docker** | Container management | Add setup.py, complete Docker SDK integration |
| **opsvi-security** | Security utilities, secrets management | Add setup.py, add HashiCorp Vault support |

### ⚠️ MERGE - Redundant Libraries

| Merge These | Into This | Reason |
|-------------|-----------|---------|
| opsvi-comm, opsvi-communication | opsvi-core | Basic communication patterns belong in core |
| opsvi-coord, opsvi-coordination | opsvi-core | Coordination patterns belong in core |
| opsvi-orch, opsvi-orchestration, opsvi-orchestrator | opsvi-mcp | Use claude-code for orchestration |
| opsvi-memory | Neo4j KB | Direct Neo4j integration |
| opsvi-agents | opsvi-mcp | All agents → claude-code profiles |
| opsvi-auto-forge | opsvi-mcp | Forge capabilities → claude-code |

### ❌ REMOVE - Incomplete Stubs

These have <5 files and no real implementation:
- opsvi-communication (0 files)
- opsvi-coordination (0 files)
- opsvi-orchestration (0 files)
- opsvi-sdlc-enhancements (0 files)
- opsvi-orchestrator (2 files)
- opsvi-workers (3 files)

### 🔍 REVIEW - Large/Unknown Libraries

| Library | Files | Recommendation |
|---------|-------|----------------|
| **opsvi-ecosystem** | 1126 | Extract useful components → relevant libs, then remove |
| **opsvi-docs** | 1590 | Keep documentation, move code → other libs |
| **opsvi-asea** | 381 | Review for salvageable components → opsvi-mcp |
| **opsvi-shared** | 301 | Distribute utilities → appropriate libs |
| **opsvi-meta** | 10 | Merge self-improvement → opsvi-mcp profiles |
| **opsvi-pipeline** | 21 | Evaluate if needed or use opsvi-mcp |
| **opsvi-rag** | 12 | Merge RAG capabilities → opsvi-llm |

## Migration Path

### Phase 1: Core Stabilization (Week 1)
```bash
# Add setup.py to core libraries
for lib in core data fs auth api; do
    python scripts/add_setup_py.py libs/opsvi-$lib
done

# Run tests and fix coverage
pytest libs/opsvi-core libs/opsvi-data libs/opsvi-fs
```

### Phase 2: Interface Standardization (Week 2)
```bash
# Complete opsvi-llm providers
# Complete opsvi-interfaces implementation
# Update all apps to use standardized interfaces
```

### Phase 3: Consolidation (Week 3)
```bash
# Merge redundant libraries
python scripts/merge_libraries.py

# Remove stub libraries
rm -rf libs/opsvi-{communication,coordination,orchestration,sdlc-enhancements,orchestrator,workers}
```

### Phase 4: App Migration (Week 4)
```bash
# Migrate all apps to use consolidated libraries
python scripts/migrate_apps.py

# Update import statements
python scripts/update_imports.py
```

## Implementation Checklist

### Immediate Actions
- [ ] Create setup.py for all KEEP libraries
- [ ] Remove 6 empty stub libraries
- [ ] Merge opsvi-comm and opsvi-communication
- [ ] Merge opsvi-coord and opsvi-coordination

### Short-term (This Week)
- [ ] Complete opsvi-llm provider implementations
- [ ] Migrate opsvi-agents → opsvi-mcp profiles
- [ ] Extract useful code from opsvi-ecosystem
- [ ] Add tests to core libraries

### Medium-term (Next 2 Weeks)
- [ ] Migrate auto-forge-factory to opsvi-mcp
- [ ] Replace opsvi-memory with Neo4j
- [ ] Consolidate orchestration into opsvi-mcp
- [ ] Complete opsvi-interfaces

### Long-term (Month)
- [ ] Full test coverage for KEEP libraries
- [ ] Documentation for all public APIs
- [ ] Performance optimization
- [ ] Security audit

## Expected Outcomes

### Before Consolidation
- 36 libraries (mostly incomplete)
- 3 with setup.py
- 1 complete
- Massive duplication
- Unclear dependencies

### After Consolidation
- **12 focused libraries** (all complete)
- 12 with setup.py
- 12 complete with tests
- Clear separation of concerns
- Standardized on claude-code + opsvi-llm

### Benefits
1. **Reduced Complexity**: 67% fewer libraries to maintain
2. **Better Quality**: All remaining libraries complete with tests
3. **Clear Architecture**: Each library has a specific purpose
4. **Standardization**: All apps use same interfaces
5. **Maintainability**: Easier to update and extend

## Code Impact Analysis

### Apps Using Deprecated Libraries
```python
affected_apps = {
    'proj-mapper': ['opsvi-agents'],  # → Migrated to opsvi-mcp
    'auto-forge-factory': ['opsvi-auto-forge', 'opsvi-agents'],  # → Needs migration
    # Add more as discovered
}
```

### Import Replacements
```python
replacements = {
    'from opsvi_agents': 'from opsvi_mcp.servers.claude_code',
    'from opsvi_memory': '# Use Neo4j directly',
    'from opsvi_comm': 'from opsvi_core.communication',
    'from opsvi_coord': 'from opsvi_core.coordination',
    'from opsvi_orchestration': 'from opsvi_mcp.orchestration',
}
```

## Monitoring Progress

Track consolidation progress with:
```bash
# Count remaining libraries
ls -d libs/opsvi-* | wc -l

# Check setup.py coverage
for lib in libs/opsvi-*/; do
    [ -f "$lib/setup.py" ] && echo "✓ $(basename $lib)" || echo "✗ $(basename $lib)"
done

# Test coverage
pytest libs/opsvi-* --cov --cov-report=term-missing
```

## Risk Mitigation

1. **Backup Everything**: Before any deletion/merge
2. **Gradual Migration**: One library at a time
3. **Test Continuously**: Run tests after each change
4. **Document Changes**: Update imports guide
5. **Rollback Plan**: Git branches for each phase

## Success Metrics

- [ ] All KEEP libraries have setup.py
- [ ] All KEEP libraries have >80% test coverage
- [ ] No duplicate functionality across libraries
- [ ] All apps successfully migrated
- [ ] CI/CD pipeline passes
- [ ] Documentation complete
