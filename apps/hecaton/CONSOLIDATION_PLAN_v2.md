# HECATON Consolidation Plan v2: Send API Architecture

## Executive Summary
**Major Change**: Send API pattern (via LangGraph) should be the DEFAULT architecture for HECATON, not a secondary option. This enables true parallel multi-agent execution with 3-5x performance improvement.

## Architectural Principle: Send API First

### Why Send API is Superior
1. **True Parallelism**: Send API enables genuine parallel agent execution without asyncio limitations
2. **Proven Performance**: 3-5x improvement documented from oamat-sd pattern
3. **Designed for Multi-Agent**: LangGraph's Send API is specifically built for orchestrating multiple agents
4. **Production Ready**: Battle-tested pattern, not experimental

### Core Architecture

```
┌─────────────────────────────────────────┐
│         LangGraphOrchestrator           │ ← PRIMARY (Default)
│         (Send API Pattern)              │
└─────────────┬───────────────────────────┘
              │
              ▼ Creates Send objects
    ┌─────────┴────────┬─────────┬─────────┐
    │                  │         │         │
    ▼                  ▼         ▼         ▼
[Agent 1]         [Agent 2]  [Agent 3]  [Agent N]  ← TRUE PARALLEL
    │                  │         │         │
    ▼                  ▼         ▼         ▼
RealClaude        RealClaude RealClaude RealClaude
Subprocess        Subprocess Subprocess Subprocess
Executor          Executor   Executor   Executor
```

## Consolidated Architecture

### Primary Components (Send API Path)

#### 1. **SendAPIOrchestrator** (Rename from LangGraphOrchestrator)
**Purpose**: Primary orchestration using Send API pattern
**Location**: `src/hecaton/orchestration/send_api.py`
**Features**:
- Workflow with conditional edges
- Send object creation for parallel routing
- State management across parallel agents
- 3-5x performance improvement

#### 2. **ParallelExecutor** (Enhanced RealClaudeSubprocessExecutor)
**Purpose**: Executor optimized for Send API coordination
**Location**: `src/hecaton/execution/parallel_executor.py`
**Features**:
- Subprocess management per agent
- Integration with Send API state
- Token pool coordination for parallel execution
- Worktree isolation per agent

### Fallback Components (Simple Mode)

#### 1. **SimpleOrchestrator** (Current EnhancedOrchestrator)
**Purpose**: Fallback for debugging/testing without LangGraph
**Location**: `src/hecaton/orchestration/simple.py`
**When Used**: `--mode simple` flag

### Resource Components (Shared)

1. **SecureTokenPool**: Thread-safe token rotation
2. **WorktreeManager**: Git isolation for agents
3. **ClaudeCommandFactory**: Command optimization
4. **PerformanceMonitor**: Metrics tracking

## Implementation Plan

### Phase 1: Establish Send API as Primary

```python
# src/hecaton/__main__.py
class HecatonApp:
    def __init__(self, mode: str = "send-api", verbose: bool = False):
        if mode == "send-api":
            # DEFAULT PATH
            from .orchestration.send_api import SendAPIOrchestrator
            self.orchestrator = SendAPIOrchestrator(
                executor=ParallelExecutor(self.token_pool, self.worktree_manager)
            )
        elif mode == "simple":
            # FALLBACK PATH
            from .orchestration.simple import SimpleOrchestrator
            self.orchestrator = SimpleOrchestrator(
                executor=RealClaudeSubprocessExecutor(self.token_pool, self.worktree_manager)
            )
```

### Phase 2: Optimize Send API Integration

1. **Create SendAPIOrchestrator** from LangGraphOrchestrator
   - Enhance Send object creation
   - Add agent-specific state management
   - Implement proper error handling for parallel failures

2. **Create ParallelExecutor** from RealClaudeSubprocessExecutor
   - Add Send API state integration
   - Optimize for parallel subprocess management
   - Implement result aggregation

### Phase 3: Deprecation

**DELETE These Files**:
```
❌ src/hecaton/agents/claude_executor.py          # MCP-based, not Send API compatible
❌ src/hecaton/execution/headless_executor.py     # Not integrated with Send API
❌ src/hecaton/execution/optimized_headless_executor.py  # Wrong optimization path
❌ src/hecaton/orchestration/self_improving_orchestrator.py  # Built on wrong base
❌ src/hecaton/orchestration/__init__.py (SendAPIOrchestrator stub)  # Replace with real
```

**KEEP But Rename**:
```
✓ langgraph_orchestrator.py → send_api.py  # Make it primary
✓ enhanced_orchestrator.py → simple.py     # Make it fallback
```

## Usage Patterns

### Default (Send API - Production)
```bash
# Uses Send API by default
python -m hecaton run "Build a web app" --agents 5

# Explicit Send API mode
python -m hecaton run "Complex task" --mode send-api --agents 10
```

### Fallback (Simple - Debug/Test)
```bash
# Simple mode for debugging
python -m hecaton run "Test task" --mode simple --agents 2
```

## Performance Expectations

### Send API Mode (Default)
- **Agents**: 5-15 parallel agents
- **Performance**: 3-5x faster than sequential
- **Token Usage**: Efficient rotation across parallel agents
- **Example**: 5 agents complete in ~20 seconds vs ~90 seconds sequential

### Simple Mode (Fallback)
- **Agents**: 2-5 with limited parallelism
- **Performance**: Standard asyncio.gather() speed
- **Token Usage**: Sequential rotation
- **Use Case**: Debugging, development, simple tasks

## Migration Steps

### Week 1: Core Implementation
1. Rename and enhance LangGraphOrchestrator → SendAPIOrchestrator
2. Create ParallelExecutor optimized for Send API
3. Update __main__.py to use Send API by default
4. Add --mode flag for simple fallback

### Week 2: Testing & Optimization
1. Test parallel execution with 5, 10, 15 agents
2. Optimize Send object creation
3. Verify token pool handles parallel load
4. Benchmark Send API vs Simple mode

### Week 3: Cleanup
1. Delete deprecated files
2. Update all imports
3. Clean documentation
4. Update USAGE.md

## Success Criteria

1. ✅ Send API is the default execution mode
2. ✅ 3-5x performance improvement verified
3. ✅ Parallel execution works with 10+ agents
4. ✅ Simple mode available as fallback
5. ✅ Clean architecture with clear primary/fallback paths

## Key Architectural Decision

**Send API is not just another orchestrator - it IS the architecture**. Everything else should support or provide fallback to this primary pattern. This aligns HECATON with its core value: true parallel multi-agent orchestration.

## Next Steps

1. Begin Phase 1: Make Send API primary in __main__.py
2. Test with real parallel workloads
3. Document Send API patterns for developers
