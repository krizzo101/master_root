# HECATON Implementation Cross-Reference Guide

This document links design specifications to actual implementations and reference code, enabling development agents to quickly find and reuse existing patterns.

## Core Patterns Reference Map

### 1. Token Pool Management

**Design Doc**: `docs/design/MULTI_AGENT_TECHNICAL_SPEC_V2.md` → Section 3.2
**Implementation**: `src/hecaton/resources/token_pool.py`
**Reference Pattern**: `multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py`

```python
# CRITICAL PATTERN: Thread-safe round-robin rotation
class TokenPool:
    def __init__(self):
        self._lock = threading.Lock()  # MUST have for thread safety

    def acquire(self):
        with self._lock:  # Rule from reference
            token = self._tokens[self._token_index]
            self._token_index = (self._token_index + 1) % len(self._tokens)
```

### 2. Git Worktree Isolation

**Design Doc**: `docs/design/MULTI_AGENT_ARCHITECTURE_V2.md` → Section 4.3
**Implementation**: `src/hecaton/resources/worktree.py`
**Reference Pattern**: `multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py`

```python
# CRITICAL PATTERN: Use git branch, NOT git checkout -b (Rule 997)
subprocess.run(["git", "branch", branch_name], ...)  # CORRECT
# NOT: subprocess.run(["git", "checkout", "-b", ...])  # WRONG
```

### 3. LangGraph Send API

**Design Doc**: `docs/design/MULTI_AGENT_ORCHESTRATION_ANALYSIS.md` → Section 5
**Implementation**: `src/hecaton/orchestration/langgraph_orchestrator.py`
**Reference Pattern**: `multi-agent-reference/oamat-sd/execution_engine.py`

```python
# CRITICAL PATTERN: Must use add_conditional_edges for parallelism
workflow.add_conditional_edges(
    "distribute_agents",
    self._create_send_objects,  # Returns Send objects
    ["execute_agent"]
)
# NOT: workflow.add_edge(...)  # This would be sequential!
```

### 4. Message Broker

**Design Doc**: `docs/design/MULTI_AGENT_IMPLEMENTATION_GUIDE.md` → Section 3.4
**Implementation**: `src/hecaton/messaging/message_broker.py`
**Reference Pattern**: `multi-agent-reference/multi-agent-monitor/orchestration/`

### 5. Real Claude Execution

**Design Doc**: `docs/design/MULTI_AGENT_CLAUDE_INTEGRATION.md`
**Implementation**: `src/hecaton/agents/real_claude_executor.py`
**Reference Pattern**: `multi-agent-reference/claude-code-server/job_manager.py`

```python
# Pattern: Subprocess management for Claude CLI
cmd = ["claude", "-p", "--strict-mcp-config", ...]
process = await asyncio.create_subprocess_exec(*cmd, ...)
```

## Phase Implementation Map

### Phase 0: Foundation (✅ Complete)

| Component | Design Location | Implementation | Reference Code |
|-----------|----------------|----------------|----------------|
| Token Pool (2 tokens) | `HECATON_PHASE_0_IMPLEMENTATION.md` | `src/hecaton/resources/token_pool.py` | `multi-agent-monitor/orchestration/token_pool.py` |
| Worktree Manager | `HECATON_PHASE_0_IMPLEMENTATION.md` | `src/hecaton/resources/worktree.py` | `multi-agent-monitor/orchestration/worktree_manager.py` |
| Basic Orchestrator | `MULTI_AGENT_ARCHITECTURE_V2.md` | `src/hecaton/core/orchestrator.py` | `oamat-sd/execution_engine.py` |

### Phase 1: Self-Amplification (✅ Complete)

| Component | Design Location | Implementation | Reference Code |
|-----------|----------------|----------------|----------------|
| Token Expansion (2→5) | `BOOTSTRAPPING_IMPLEMENTATION_PLAN.md` | `phase1_modifications/expand_token_pool.py` | N/A (self-generated) |
| Error Handling | `BOOTSTRAPPING_IMPLEMENTATION_PLAN.md` | `phase1_modifications/add_error_handling.py` | `multi-agent-monitor/orchestration/enhanced_orchestrator.py` |
| Enhanced Orchestrator | `MULTI_AGENT_TECHNICAL_SPEC_V2.md` | `src/hecaton/orchestration/enhanced_orchestrator.py` | `additional-resources/orchestrator.py` |

### Phase 2: Real Execution (✅ Complete)

| Component | Design Location | Implementation | Reference Code |
|-----------|----------------|----------------|----------------|
| Message Broker | `MULTI_AGENT_IMPLEMENTATION_GUIDE.md` | `src/hecaton/messaging/message_broker.py` | Custom AsyncIO implementation |
| Agent Registry | `MULTI_AGENT_TECHNICAL_SPEC_V2.md` | `src/hecaton/agents/agent_registry.py` | `additional-resources/auto-forge-factory/agent_registry.py` |
| Specialized Agents | `MULTI_AGENT_ARCHITECTURE_V2.md` | `src/hecaton/agents/specialized/*.py` | `metagpt/*.py` patterns |
| Performance Monitor | `UNIFIED_IMPLEMENTATION_ROADMAP.md` | `src/hecaton/monitoring/performance_monitor.py` | Custom implementation |

### Phase 3: Autonomous Improvement (✅ Complete)

| Component | Design Location | Implementation | Reference Code |
|-----------|----------------|----------------|----------------|
| Self-Improving Orchestrator | `BOOTSTRAPPING_IMPLEMENTATION_PLAN.md` | `src/hecaton/orchestration/self_improving_orchestrator.py` | `knowledge-system/autonomous_evolution.py` |
| Parallel Executor (15 agents) | `MULTI_AGENT_CLAUDE_INTEGRATION.md` | `src/hecaton/agents/real_claude_executor.py` | `claude-code-server/job_manager.py` |
| Improvement Validation | N/A (emergent) | `src/hecaton/validation/improvement_validator.py` | Custom implementation |

### Phase 4: Environment Optimization (🚧 Next)

| Component | Design Location | Implementation | Reference Code |
|-----------|----------------|----------------|----------------|
| Agent Environment Optimizer | `docs/AGENT_ENVIRONMENT_OPTIMIZATION.md` | `src/hecaton/config/agent_environment_optimizer.py` | `claude_headless_agents/claude_headless_complete_guide.md` |
| Minimal MCP Configs | `docs/AGENT_ENVIRONMENT_OPTIMIZATION.md` | `src/hecaton/config/minimal_profiles/` | `claude_headless_agents/performance_tests/` |
| Optimized Executor | `docs/PHASE_2_HEADLESS_INTEGRATION.md` | `src/hecaton/execution/optimized_headless_executor.py` | `claude_headless_agents/claude_agent_orchestrator.py` |

## Critical Patterns from Reference

### Must-Follow Rules (from `CRITICAL_PATTERNS_ANALYSIS.md`)

1. **Rule 997: Git Worktree Pattern**
   ```python
   # ALWAYS use:
   subprocess.run(["git", "branch", branch_name])
   # NEVER use:
   subprocess.run(["git", "checkout", "-b", branch_name])
   ```

2. **Send API Pattern**
   ```python
   # MUST use add_conditional_edges for parallelism
   workflow.add_conditional_edges("node", func, ["target"])
   # NOT add_edge (sequential)
   ```

3. **Thread Safety**
   ```python
   # ALWAYS use locks for shared resources
   with self._lock:
       # Access shared resource
   ```

4. **Token Rotation**
   ```python
   # Round-robin with modulo
   self._token_index = (self._token_index + 1) % len(self._tokens)
   ```

## Reference Code Quick Links

### Core Infrastructure
- **Token Pool**: `multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py`
- **Worktree**: `multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py`
- **Send API**: `multi-agent-reference/oamat-sd/execution_engine.py`

### Claude Integration
- **Job Manager**: `multi-agent-reference/claude-code-server/job_manager.py`
- **Parallel Enhancement**: `multi-agent-reference/claude-code-server/parallel_enhancement.py`
- **Headless Optimization**: `multi-agent-reference/claude_headless_agents/`

### Agent Patterns
- **Base Agent**: `multi-agent-reference/additional-resources/auto-forge-factory/base_agent.py`
- **Agent Registry**: `multi-agent-reference/additional-resources/auto-forge-factory/agent_registry.py`
- **Specialized Agents**: `multi-agent-reference/metagpt/`

### Orchestration
- **Enhanced Orchestrator**: `multi-agent-reference/multi-agent-monitor/orchestration/enhanced_orchestrator.py`
- **Team Orchestrator**: `multi-agent-reference/multi-agent-monitor/orchestration/team_orchestrator.py`
- **Swarm Executor**: `multi-agent-reference/multi-agent-monitor/swarm_executor.py`

## Development Agent Instructions

When implementing new features:

1. **Check this document first** for existing patterns
2. **Review the reference code** before creating new implementations
3. **Follow the critical patterns** from `CRITICAL_PATTERNS_ANALYSIS.md`
4. **Use the exact patterns** shown in reference code (don't reinvent)
5. **Link back to this document** in your implementation comments

### Example Implementation Comment:
```python
"""
Message Broker implementation for HECATON
Based on: multi-agent-reference/multi-agent-monitor/orchestration/
See: docs/IMPLEMENTATION_CROSS_REFERENCE.md → Section "Message Broker"
"""
```

## Missing Components to Implement

### High Priority
1. **Load Balancer**: Reference in `multi-agent-monitor/orchestration/`
2. **Health Checker**: Pattern in `claude-code-server/`
3. **Cost Optimizer**: Design needed

### Medium Priority
1. **Agent Communication Protocol**: Reference in `swarm-patterns/`
2. **Checkpoint System**: Pattern in `sdlc-patterns/`
3. **Rollback Manager**: Design needed

### Low Priority
1. **Visualization Dashboard**: Reference in `multi-agent-monitor/`
2. **Metrics Aggregator**: Pattern in `performance_monitor.py`
3. **Report Generator**: Design needed

## How to Use This Document

### For Development Agents:
```markdown
When tasked to implement [COMPONENT]:
1. Search this document for [COMPONENT]
2. Find the reference code location
3. Review the reference implementation
4. Follow the exact pattern (don't recreate)
5. Add cross-reference comment in your code
```

### For Human Developers:
1. Use Ctrl+F to find component references
2. Check "Critical Patterns" before implementing
3. Review reference code for best practices
4. Update this document when adding new components

---

**Last Updated**: 2025-08-27
**Phases Complete**: 0, 1, 2, 3
**Next Phase**: 4 (Environment Optimization)
