# Critical Patterns Analysis - Multi-Agent Reference

## 🚨 MUST-IMPLEMENT Patterns (Critical for Success)

### 1. **LangGraph Send API for Parallel Execution**
**File:** `oamat-sd/execution_engine.py`
**Performance:** 3-5x speedup proven
```python
# CRITICAL: Use add_conditional_edges, NOT add_edge
workflow.add_conditional_edges(
    "distribute_agents",
    self._create_send_objects,  # Returns Send objects
    ["execute_agent"]
)
```
**Why Critical:**
- Enables true parallel agent execution
- Avoids asyncio.gather (forbidden by Rule 997)
- Production-tested with 20+ reversions prevented

### 2. **Token Pool with Round-Robin Rotation**
**File:** `multi-agent-monitor/orchestration/token_pool.py`
**Pattern:** Thread-safe token management
```python
class SecureTokenPool:
    def get_token(self) -> Tuple[str, str]:
        with self._lock:
            token = self._tokens[self._token_index]
            self._token_index = (self._token_index + 1) % len(self._tokens)
            return token, token_hash
```
**Why Critical:**
- Enables 15+ parallel Claude Code agents
- Thread-safe for concurrent access
- Usage tracking and statistics

### 3. **Git Worktree Isolation**
**File:** `multi-agent-monitor/orchestration/worktree_manager.py`
**Pattern:** Agent workspace isolation
```python
def create_agent_worktree(self, agent_id: str, agent_type: str):
    branch_name = f"agent/{agent_type}/{agent_id}"
    worktree_path = self.worktrees_base / agent_id
    subprocess.run(["git", "worktree", "add", "-b", branch_name, worktree_path])
```
**Why Critical:**
- Prevents merge conflicts between agents
- Enables true parallel file modifications
- Clean rollback on failures

## ⚠️ HIGH-VALUE Patterns (Strongly Recommended)

### 4. **Agent Registry Pattern**
**File:** `additional-resources/auto-forge-factory/agent_registry.py`
**Pattern:** Dynamic agent type management
```python
class AgentRegistry:
    def register_agent(self, agent_type: AgentType, agent_class: Type[BaseAgent]):
        self._agents[agent_type] = agent_class

    def create_agent_instance(self, agent_type: AgentType, job_id: str):
        return self._agents[agent_type](job_id=job_id)
```
**Benefits:**
- Extensible agent types without code changes
- Centralized agent lifecycle management
- Type safety with enums

### 5. **SDLC Phase Management**
**File:** `claude-integration/sdlc.md`, `sdlc-execute-phase.py`
**Pattern:** Phase-based execution with gates
```python
phases = ["discovery", "design", "planning", "development", "testing", "deployment"]
for phase in phases:
    if not run_preflight(phase):
        break
    result = execute_phase(phase)
    if not check_quality_gate(phase, result):
        break
```
**Benefits:**
- Structured workflow progression
- Quality gates prevent bad propagation
- Clear phase boundaries

### 6. **Progressive Autonomy**
**File:** `oamat-sd/agent_factory.py`
**Pattern:** Increasing agent freedom over time
```python
def get_agent_prompt(self, workflow_stage: int):
    if workflow_stage < 3:
        return "strict_template"  # High guidance
    elif workflow_stage < 5:
        return "guided_template"  # Medium guidance
    else:
        return "autonomous_template"  # Full autonomy
```
**Benefits:**
- Reduces early-stage hallucination
- Increases creativity when context is established
- Adaptive agent behavior

## 💡 VALUABLE Patterns (Consider for Advanced Features)

### 7. **Meta-Agent Coordination**
**File:** `vendor-patterns/openai-mcp-swarm/meta_agent.py`
**Pattern:** Agent that manages other agents
```python
class MetaAgent:
    def delegate_task(self, task, available_agents):
        best_agent = self.evaluate_agent_capabilities(task, available_agents)
        return best_agent.execute(task)
```

### 8. **Swarm Task Decomposition**
**File:** `additional-resources/swarm-patterns/swarm_executor.py`
**Pattern:** Breaking tasks into parallel subtasks
```python
def decompose_task(main_task) -> List[SubTask]:
    subtasks = analyze_dependencies(main_task)
    parallel_groups = identify_parallel_opportunities(subtasks)
    return schedule_optimal_execution(parallel_groups)
```

### 9. **Agent Message Broker**
**File:** `additional-resources/multi_agent_orchestration/communication/message_broker.py`
**Pattern:** Pub/sub communication between agents
```python
class MessageBroker:
    async def publish(self, topic: str, message: Any):
        for subscriber in self.topics[topic]:
            await subscriber.handle_message(message)
```

### 10. **Autonomous Evolution**
**File:** `additional-resources/knowledge-system/autonomous_evolution.py`
**Pattern:** Self-improving system
```python
class AutonomousEvolutionEngine:
    def hypothesis_testing_cycle(self):
        hypothesis = generate_hypothesis()
        result = test_hypothesis(hypothesis)
        if successful:
            implement_improvement(hypothesis)
```

## 🛡️ SAFETY Patterns (Essential for Production)

### 11. **Rollback Mechanism**
**File:** `multi-agent-monitor/safety/safe_orchestrator.py`
**Pattern:** Checkpoint and rollback
```python
def checkpoint_before_execution(self):
    self.save_state()
    try:
        result = execute()
    except:
        self.rollback_to_checkpoint()
```

### 12. **Error Propagation Control**
**File:** `additional-resources/accf-orchestrators/`
**Pattern:** Error boundaries
```python
async def execute_with_boundary(self, agent):
    try:
        return await agent.execute()
    except CriticalError:
        raise  # Propagate critical
    except Exception as e:
        return ErrorResult(e)  # Contain non-critical
```

## 📊 Performance Patterns

### 13. **Batch Processing**
**Pattern:** Group operations for efficiency
```python
# Instead of individual operations
for item in items:
    await process(item)

# Batch operations
batches = chunk(items, batch_size=10)
await asyncio.gather(*[process_batch(b) for b in batches])
```

### 14. **Resource Pooling**
**Pattern:** Reuse expensive resources
```python
class ResourcePool:
    def acquire(self):
        if self.available:
            return self.available.pop()
        return self.create_new()
```

## 🔄 Communication Patterns

### 15. **Agent Handoff Protocol**
**File:** `vendor-patterns/openai-cookbook/`
**Pattern:** Structured agent transitions
```python
class AgentHandoff:
    def prepare_handoff(self, from_agent, to_agent, context):
        handoff_package = {
            "context": context,
            "completed_work": from_agent.get_results(),
            "next_steps": from_agent.recommend_next(),
        }
        to_agent.receive_handoff(handoff_package)
```

## 📝 Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)
- [ ] Implement LangGraph Send API
- [ ] Set up Token Pool (15 tokens)
- [ ] Configure Git Worktree isolation
- [ ] Create Agent Registry

### Phase 2: Orchestration (Week 2)
- [ ] Build SDLC phase manager
- [ ] Implement progressive autonomy
- [ ] Add meta-agent coordinator
- [ ] Set up message broker

### Phase 3: Safety & Optimization (Week 3)
- [ ] Add rollback mechanisms
- [ ] Implement error boundaries
- [ ] Set up resource pooling
- [ ] Add performance monitoring

### Phase 4: Advanced Features (Week 4)
- [ ] Implement swarm decomposition
- [ ] Add autonomous evolution
- [ ] Set up agent handoff protocols
- [ ] Create quality gates

## ⚠️ Anti-Patterns to AVOID

### ❌ DO NOT USE:
1. **asyncio.gather()** - Violates Rule 997, use Send API
2. **Sequential agent execution** - Destroys performance
3. **Shared file access without locks** - Causes conflicts
4. **Hardcoded agent types** - Use registry pattern
5. **Single token for all agents** - Causes rate limiting

### ❌ COMMON MISTAKES:
1. **Using add_edge instead of add_conditional_edges** - Breaks Send API
2. **Not implementing worktree isolation** - Merge conflicts
3. **Skipping progressive autonomy** - Increased hallucination
4. **No rollback mechanism** - Can't recover from failures
5. **Missing error boundaries** - Cascade failures

## 🎯 Quick Start Recommendation

Start with this minimal viable implementation:

```python
# 1. Token Pool (enables parallelism)
token_pool = SecureTokenPool(tokens=CLAUDE_TOKENS)

# 2. LangGraph Send API (3-5x performance)
workflow = StateGraph(AgentState)
workflow.add_conditional_edges("distribute", create_send_objects, ["execute"])

# 3. Worktree Isolation (prevents conflicts)
worktree_mgr = WorktreeManager()
worktree_mgr.create_agent_worktree(agent_id, agent_type)

# 4. Agent Registry (extensibility)
registry = AgentRegistry()
registry.register_agent(AgentType.CODER, CoderAgent)

# 5. Basic Safety
checkpoint()
try:
    result = execute()
except:
    rollback()
```

This gives you parallel execution, isolation, extensibility, and safety - the four pillars of a robust multi-agent system!
