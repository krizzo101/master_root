# Design to Implementation Mapping

## Purpose
This document provides direct mapping from design specifications to actual implemented code, ensuring development agents can quickly find working examples.

---

## Design Document → Implementation Status

### 1. MULTI_AGENT_TECHNICAL_SPEC_V2.md

#### Section 1.1: LangGraph Send API Orchestrator
**Design Location**: Lines 11-100
**Implementation Status**: ✅ Partially Implemented
**Actual Code**:
- `src/hecaton/orchestration/langgraph_orchestrator.py` (planned)
- Currently using: `src/hecaton/agents/real_claude_executor.py`
**Reference Pattern**: `multi-agent-reference/oamat-sd/execution_engine.py`

```python
# Critical pattern from reference:
workflow.add_conditional_edges(
    "distribute_agents",
    self._create_send_objects,  # MUST return Send objects
    ["execute_agent"]
)
```

#### Section 2: Token Pool
**Design**: Thread-safe round-robin with 15 tokens
**Implementation**: ✅ Complete (5 tokens, expandable to 15)
**Actual Code**: `src/hecaton/resources/token_pool.py`
**Reference**: `multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py`

#### Section 3: Worktree Manager
**Design**: Git isolation per agent
**Implementation**: ✅ Complete
**Actual Code**: `src/hecaton/resources/worktree.py`
**Reference**: `multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py`
**Critical Rule**: Use `git branch` NOT `git checkout -b`

---

### 2. MULTI_AGENT_ARCHITECTURE_V2.md

#### Three-Plane Architecture
**Design**: Control, Execution, Resource planes
**Implementation Status**: ✅ Implemented differently

| Design Plane | Actual Implementation |
|-------------|----------------------|
| Control Plane | `src/hecaton/orchestration/self_improving_orchestrator.py` |
| Execution Plane | `src/hecaton/agents/real_claude_executor.py` |
| Resource Plane | `src/hecaton/resources/` (token_pool, worktree) |

#### Agent Types
**Design**: 5 specialized types
**Implementation**: ✅ Complete

| Agent Type | Implementation | Location |
|-----------|----------------|----------|
| Code Agent | ✅ | `src/hecaton/agents/specialized/code_agent.py` |
| Test Agent | ✅ | `src/hecaton/agents/specialized/test_agent.py` |
| Research Agent | ✅ | `src/hecaton/agents/specialized/research_agent.py` |
| Review Agent | Planned | Use `code_agent.py` as template |
| Refactor Agent | Planned | Use `code_agent.py` as template |

---

### 3. MULTI_AGENT_IMPLEMENTATION_GUIDE.md

#### Message Broker
**Design**: Inter-agent communication
**Implementation**: ✅ Complete
**Actual Code**: `src/hecaton/messaging/message_broker.py`
**Pattern**: AsyncIO Queue-based pub/sub

#### Agent Registry
**Design**: Discovery and management
**Implementation**: ✅ Complete
**Actual Code**: `src/hecaton/agents/agent_registry.py`
**Reference**: `multi-agent-reference/additional-resources/auto-forge-factory/agent_registry.py`

---

### 4. MULTI_AGENT_CLAUDE_INTEGRATION.md

#### Claude Process Execution
**Design**: Subprocess management
**Implementation**: ✅ Complete with issues
**Actual Code**: `src/hecaton/agents/real_claude_executor.py`

**Current Issues**:
```python
# WRONG - Current implementation
cmd = ["claude", "code", "@task_file"]  # Slow, wrong command

# CORRECT - Should be
cmd = ["claude", "-p", "--strict-mcp-config", "--mcp-config", "minimal.json", ...]
```

**Fix Location**: `src/hecaton/execution/optimized_headless_executor.py` (Phase 4)

---

### 5. BOOTSTRAPPING_IMPLEMENTATION_PLAN.md

#### Phase Progression
**Design**: 0→1→2→3→4
**Implementation**: ✅ Phase 0-3 Complete

| Phase | Design Goal | Implementation Status | Evidence |
|-------|------------|----------------------|----------|
| 0 | 2-agent foundation | ✅ Complete | `docs/PHASE_0_COMPLETE.md` |
| 1 | Self-amplify to 5 | ✅ Complete | `docs/PHASE_1_COMPLETE.md` |
| 2 | Real execution | ✅ Complete | `docs/PHASE_2_COMPLETE.md` |
| 3 | Autonomous improvement | ✅ Complete | `docs/PHASE_3_COMPLETE.md` |
| 4 | Performance optimization | 🚧 Ready | `docs/PHASE_4_OPTIMIZATION_PLAN.md` |

---

### 6. UNIFIED_IMPLEMENTATION_ROADMAP.md

#### Timeline vs Reality

| Milestone | Planned | Actual | Status |
|-----------|---------|--------|--------|
| Phase 0 | 1 day | 1 day | ✅ On time |
| Phase 1 | 2 days | 1 day | ✅ Ahead |
| Phase 2 | 3 days | 2 days | ✅ Ahead |
| Phase 3 | 1 week | 3 days | ✅ Ahead |
| Phase 4 | 2 weeks | Starting | 🚧 |

---

## Quick Reference for Development Agents

### When implementing a new component:

1. **Find the Design Section**:
   ```bash
   grep -n "component_name" docs/design/*.md
   ```

2. **Check Implementation Status**:
   Look in this document for current status

3. **Find Reference Code**:
   ```bash
   # Check cross-reference
   grep "component_name" docs/IMPLEMENTATION_CROSS_REFERENCE.md

   # Find in reference
   find multi-agent-reference -name "*.py" | xargs grep "pattern"
   ```

4. **Use Exact Pattern**:
   Copy from reference, don't recreate

### Critical Patterns to Always Follow:

```python
# 1. Token Pool - Thread safety
with self._lock:
    token = self._tokens[self._token_index]

# 2. Worktree - Git branch
subprocess.run(["git", "branch", branch_name])  # YES
# NOT: subprocess.run(["git", "checkout", "-b"])  # NO

# 3. Send API - Conditional edges
workflow.add_conditional_edges(...)  # YES
# NOT: workflow.add_edge(...)  # NO

# 4. Claude Command - Optimized
cmd = ["claude", "-p", "--strict-mcp-config", ...]  # YES
# NOT: cmd = ["claude", "code", ...]  # NO
```

---

## Missing Implementations

### High Priority (Phase 4)
1. **LangGraph Integration**: Design exists, not implemented
   - Design: `MULTI_AGENT_TECHNICAL_SPEC_V2.md` lines 11-100
   - Create: `src/hecaton/orchestration/langgraph_orchestrator.py`
   - Reference: `multi-agent-reference/oamat-sd/execution_engine.py`

2. **Optimized Executor Integration**: Created, not integrated
   - Design: `docs/AGENT_ENVIRONMENT_OPTIMIZATION.md`
   - Integrate: `src/hecaton/execution/optimized_headless_executor.py`
   - Into: `src/hecaton/agents/real_claude_executor.py`

### Medium Priority
1. **Review Agent**: Design exists, not implemented
2. **Refactor Agent**: Design exists, not implemented
3. **Health Monitoring**: Reference exists, not implemented

### Low Priority
1. **Visualization Dashboard**: Nice to have
2. **Cost Optimizer**: Can use performance monitor
3. **Report Generator**: Can be added later

---

## How to Update This Document

When you implement something:

1. Find the design section
2. Update implementation status
3. Add actual code location
4. Note any deviations from design
5. Add reference code used

Example:
```markdown
#### Component Name
**Design**: Brief description
**Implementation**: ✅ Complete / ⚠️ Partial / ❌ Missing
**Actual Code**: `src/hecaton/path/to/file.py`
**Reference**: `multi-agent-reference/path/to/reference.py`
**Notes**: Any deviations or issues
```

---

**Last Updated**: 2025-08-27
**Current Phase**: 3 Complete, 4 Starting
**Next Priority**: Integrate optimized executor for 10x performance
