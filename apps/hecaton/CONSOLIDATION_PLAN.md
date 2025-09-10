# HECATON Consolidation Plan

## Executive Summary
The HECATON codebase has evolved through multiple phases, resulting in significant redundancy. This plan consolidates the system to a single, clear architecture while preserving all functional capabilities.

## Current State Analysis

### Redundancy Identified
- **5 Executor implementations** doing similar subprocess/API management
- **4+ Orchestrator implementations** with overlapping coordination logic
- **2 Token pool implementations** with similar functionality
- **2 Worktree manager versions** (original and "fixed")
- **3 CLI entry points** with duplicate command handling

### Core Value Components
1. **RealClaudeSubprocessExecutor**: Production-tested subprocess management
2. **SecureTokenPool**: Thread-safe token rotation with stats
3. **WorktreeManager (fixed)**: Proven git isolation
4. **ClaudeCommandFactory**: Sophisticated command optimization
5. **PerformanceMonitor**: Metrics and tracking

## Consolidation Strategy

### 1. Executor Consolidation
**Keep**: `RealClaudeSubprocessExecutor`
**Deprecate**:
- `claude_executor.py` (MCP-based, less direct)
- `headless_executor.py` (not integrated)
- `optimized_headless_executor.py` (premature optimization)
- `optimized_real_claude_executor.py` (unnecessary layer)

**Rationale**: The subprocess executor is battle-tested and provides direct control.

### 2. Orchestrator Consolidation
**Create**: `UnifiedOrchestrator` combining:
- Base coordination from `HecatonOrchestrator`
- Error handling from `EnhancedOrchestrator`
- Performance monitoring (already integrated)

**Deprecate**:
- `SendAPIOrchestrator` (empty stub)
- `LangGraphOrchestrator` (unnecessary dependency)
- `SelfImprovingOrchestrator` (incomplete, over-engineered)

**Rationale**: Simple, working orchestration without external dependencies.

### 3. Resource Consolidation
**Keep**:
- `secure_token_pool.py` → rename to `token_pool.py`
- `worktree_fixed.py` → rename to `worktree_manager.py`

**Deprecate**:
- Original `token_pool.py` (less secure)
- Original `worktree.py` (had issues)

### 4. CLI Consolidation
**Keep**: `__main__.py` as single entry point
**Integrate**: Best features from `hecaton_cli_enhanced.py`
**Deprecate**: `hecaton_cli.py` (redundant)

## Target Architecture

```
apps/hecaton/
├── src/
│   └── hecaton/
│       ├── __main__.py              # Single CLI entry point
│       ├── orchestrator.py          # Unified orchestrator
│       ├── executor.py              # Single executor (subprocess)
│       ├── resources/
│       │   ├── token_pool.py        # Secure token management
│       │   └── worktree_manager.py  # Git isolation
│       ├── agents/
│       │   ├── command_factory.py   # Command optimization
│       │   └── registry.py          # Agent type registry
│       ├── monitoring/
│       │   └── performance.py       # Metrics tracking
│       └── utils/
│           ├── logger.py            # Logging utilities
│           └── session.py           # Session tracking
├── config/
│   └── claude_tokens.json          # Token configuration
└── USAGE.md                         # User documentation
```

## Implementation Steps

### Phase 1: Create Unified Components (Day 1)
1. Create `orchestrator.py` merging best features
2. Rename `real_claude_executor.py` → `executor.py`
3. Rename resource files to final names
4. Update imports in all files

### Phase 2: Update Entry Points (Day 2)
1. Consolidate CLI commands in `__main__.py`
2. Remove mock/dry-run code paths
3. Integrate enhanced CLI features
4. Update configuration handling

### Phase 3: Remove Deprecated Code (Day 3)
1. Delete redundant executor files
2. Delete redundant orchestrator files
3. Delete old resource versions
4. Clean up unused imports

### Phase 4: Testing & Documentation (Day 4)
1. Test all execution paths
2. Verify token rotation works
3. Test worktree creation/cleanup
4. Update USAGE.md with final architecture

## Benefits

### Immediate Benefits
- **50% code reduction**: From ~15 files to ~8 core files
- **Clear architecture**: One way to do each thing
- **Reduced dependencies**: No LangGraph, simplified requirements
- **Faster startup**: Less module loading

### Long-term Benefits
- **Easier onboarding**: New developers see clear structure
- **Reduced bugs**: Less code = fewer places for bugs
- **Better performance**: Removed abstraction layers
- **Maintainability**: Single source of truth for each function

## Risks & Mitigation

### Risk 1: Breaking Existing Workflows
**Mitigation**: Keep all command-line interfaces compatible

### Risk 2: Lost Functionality
**Mitigation**: Carefully review each deprecated file for unique features

### Risk 3: Integration Issues
**Mitigation**: Incremental migration with testing at each phase

## Success Criteria

1. ✅ System runs with single orchestrator and executor
2. ✅ All existing CLI commands work
3. ✅ Token rotation and worktree isolation functional
4. ✅ No duplicate code patterns
5. ✅ Clear import hierarchy
6. ✅ Documentation reflects actual architecture

## Timeline

- **Week 1**: Implementation (Phases 1-3)
- **Week 2**: Testing and documentation (Phase 4)
- **Week 3**: Production deployment
- **Week 4**: Monitor and address issues

## Approval

This consolidation will transform HECATON from a multi-phase prototype into a production-ready system with clear architecture and maintainable codebase.

**Next Step**: Begin Phase 1 implementation by creating the unified orchestrator.
