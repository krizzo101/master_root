# Phase 4: Performance Optimization Plan

## Mission: 10x Performance Improvement

Transform HECATON from 30-60s per agent to 3-5s per agent through environment optimization and headless execution patterns.

## Current State (Phase 3)

### Performance Bottlenecks
1. **MCP Server Loading**: 15-20s overhead per agent
2. **Generic Configurations**: 500+ line CLAUDE.md
3. **Permission Prompts**: 5-10s interaction delays
4. **Heavy Environment**: All tools, all commands loaded

### Metrics
- Single agent: 30-60 seconds
- 5 parallel agents: 40-80 seconds
- Memory per agent: 500MB
- Cost per task: ~$0.05

## Target State (Phase 4)

### Optimized Architecture
1. **No MCP for most agents**: 0s overhead
2. **Minimal configurations**: 10-20 line CLAUDE.md
3. **Permission bypass**: `--permission-mode acceptEdits`
4. **Lightweight environment**: Only needed tools

### Target Metrics
- Single agent: 3-5 seconds (10x faster)
- 5 parallel agents: 5-10 seconds
- Memory per agent: 100MB (80% reduction)
- Cost per task: ~$0.01 (same API, faster execution)

## Implementation Plan

### Week 1: Core Optimization

#### Day 1-2: Integrate Optimized Executor
```python
# Replace in real_claude_executor.py
from hecaton.execution.optimized_headless_executor import OptimizedHeadlessExecutor

class RealClaudeExecutor:
    def __init__(self):
        self.executor = OptimizedHeadlessExecutor()
```

**Files to modify:**
- `src/hecaton/agents/real_claude_executor.py`
- `src/hecaton/orchestration/self_improving_orchestrator.py`

**Reference code:**
- `multi-agent-reference/claude_headless_agents/claude_agent_orchestrator.py`

#### Day 3-4: Deploy Agent Environment Optimizer
```python
# Create minimal environments per agent type
optimizer = AgentEnvironmentOptimizer()
config = optimizer.create_agent_environment(
    agent_type="code",  # No MCP needed
    worktree_path=worktree
)
```

**Files to create:**
- `src/hecaton/config/minimal_profiles/code.json`
- `src/hecaton/config/minimal_profiles/test.json`
- `src/hecaton/config/minimal_profiles/research.json`

#### Day 5: Benchmark and Validate
```bash
# Run performance tests
python tests/performance/benchmark_phase4.py

# Expected results:
# Old: 35s average
# New: 4s average
# Improvement: 8.75x
```

### Week 2: Scale Testing

#### Day 6-7: 100-Agent Stress Test
```python
# Test massive parallelism
tasks = [{"id": f"task-{i}", "type": "code"} for i in range(100)]
results = await executor.execute_parallel_optimized(tasks, max_parallel=20)
```

**Create test:**
- `tests/stress/test_100_agents.py`

#### Day 8-9: Production Hardening
- Add retry logic for failed agents
- Implement circuit breakers
- Add health checks
- Create rollback mechanism

#### Day 10: Documentation and Release
- Update all design documents
- Create migration guide
- Record performance metrics
- Tag release v4.0

## Technical Implementation Details

### 1. Optimized Command Structure
```python
def build_optimized_command(agent_type, task):
    return [
        "claude", "-p",
        "--model", "sonnet",  # Often fastest!
        "--strict-mcp-config",  # Skip default MCP
        "--mcp-config", "minimal.json",  # Empty or minimal
        "--permission-mode", "acceptEdits",  # No prompts
        "--output-format", "json",
        "--", task
    ]
```

### 2. Agent Profile System
```python
AGENT_PROFILES = {
    "code": {
        "mcp_servers": {},  # None needed
        "tools": ["Write", "Read", "Edit"],
        "model": "sonnet",
        "timeout": 10
    },
    "research": {
        "mcp_servers": {"web_search": {...}},  # Only search
        "tools": ["WebSearch", "WebFetch"],
        "model": "sonnet",
        "timeout": 30
    }
}
```

### 3. Dynamic Environment Creation
```python
def create_minimal_environment(agent_id, agent_type, task):
    # Create .claude/mcp_config.json (empty or minimal)
    # Create CLAUDE.md (10-20 lines, task-focused)
    # Create .env (only required vars)
    # Return paths for command
```

## Performance Validation

### Benchmark Suite
```python
benchmarks = {
    "single_agent": {
        "old": 35,
        "target": 4,
        "threshold": 5  # Must be under 5s
    },
    "parallel_5": {
        "old": 45,
        "target": 8,
        "threshold": 10
    },
    "parallel_100": {
        "old": "timeout",
        "target": 60,
        "threshold": 90
    }
}
```

### Success Criteria
- [ ] Single agent < 5 seconds
- [ ] 5 parallel agents < 10 seconds
- [ ] 100 parallel agents < 90 seconds
- [ ] Memory usage < 100MB per agent
- [ ] All existing tests pass
- [ ] No regression in accuracy

## Risk Mitigation

### Potential Issues
1. **Too minimal config breaks agents**
   - Solution: Test each profile thoroughly
   - Fallback: Gradual rollout

2. **Race conditions at scale**
   - Solution: Enhanced locking
   - Fallback: Limit parallelism

3. **Token exhaustion**
   - Solution: Better token rotation
   - Fallback: Queue overflow tasks

## Rollout Strategy

### Phase 4.1: Limited Testing (Days 1-5)
- Deploy to test environment
- Run with 5 agents max
- Collect metrics

### Phase 4.2: Scale Testing (Days 6-9)
- Increase to 20 agents
- Test error scenarios
- Stress test infrastructure

### Phase 4.3: Production Deploy (Day 10+)
- Gradual rollout (10% → 50% → 100%)
- Monitor performance metrics
- Ready rollback plan

## Expected Outcomes

### Performance Gains
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Single Agent | 35s | 4s | 8.75x |
| 5 Agents | 45s | 8s | 5.6x |
| 15 Agents | 120s | 20s | 6x |
| 100 Agents | N/A | 60s | New capability |

### Resource Savings
- **Compute**: 80% reduction in CPU time
- **Memory**: 80% reduction (500MB → 100MB)
- **Cost**: 80% reduction in infrastructure
- **Time**: 90% faster development cycles

## Code References

### Must Review Before Implementation
1. `multi-agent-reference/claude_headless_agents/claude_headless_complete_guide.md`
2. `multi-agent-reference/claude_headless_agents/performance_tests/`
3. `multi-agent-reference/claude-code-server/parallel_enhancement.py`

### Patterns to Follow
1. Minimal MCP configuration pattern
2. Headless execution with `-p` flag
3. Environment variable isolation
4. Async subprocess management

## Success Metrics Dashboard

```python
# Real-time monitoring during Phase 4
metrics = {
    "avg_execution_time": 4.2,  # Target: <5s
    "parallel_efficiency": 0.85,  # Target: >0.8
    "memory_per_agent": 95,  # Target: <100MB
    "success_rate": 0.98,  # Target: >0.95
    "cost_per_task": 0.008  # Target: <$0.01
}
```

## Conclusion

Phase 4 will transform HECATON from a working prototype to a production-ready system through aggressive optimization. The 10x performance improvement is achievable through:

1. **Eliminating MCP overhead** (saves 15-20s)
2. **Minimal configurations** (saves 5-10s)
3. **Optimized commands** (saves 5-10s)
4. **Smart model selection** (saves 5-10s)

Total expected improvement: **30-60s → 3-5s** (10x)

---
**Start Date**: Immediately after Phase 3 completion
**Duration**: 2 weeks
**Priority**: Critical
**Impact**: Enables real-world production use
