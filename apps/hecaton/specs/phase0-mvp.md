# HECATON Phase 0: Minimum Viable Parallelism

## Version: 1.0.0
## Status: Ready for Implementation
## Target Completion: 2 Days

---

## 1. Phase 0 Objectives

### Primary Goal
Build the absolute minimum required for 2-agent parallel execution using proven patterns from `multi-agent-reference/`.

### Success Criteria
- [ ] 2 agents execute simultaneously (not sequentially)
- [ ] Total execution time < sum of individual task times
- [ ] No conflicts between agents
- [ ] 100% test coverage for critical components

## 2. Scope Definition

### IN SCOPE
✅ Send API orchestrator with LangGraph
✅ 2-token pool with round-robin
✅ Basic worktree isolation
✅ Simple CLI for testing
✅ Core component tests

### OUT OF SCOPE
❌ Error recovery (Phase 1)
❌ Agent registry (Phase 2)
❌ Inter-agent messaging (Phase 2)
❌ Performance monitoring (Phase 3)
❌ Self-modification (Phase 3+)

## 3. Component Specifications

### 3.1 Send API Orchestrator

**File**: `src/hecaton/orchestration/send_api.py`
**Source**: Copy from `multi-agent-reference/oamat-sd/execution_engine.py`
**Critical Code**:

```python
# MUST HAVE: add_conditional_edges pattern
workflow.add_conditional_edges(
    "distribute",
    lambda state: [
        Send("execute", {"agent_id": "agent1", ...}),
        Send("execute", {"agent_id": "agent2", ...})
    ],
    ["execute"]
)
```

**Acceptance Test**:
```python
def test_parallel_execution():
    orchestrator = SendAPIOrchestrator()
    start = time.time()
    results = orchestrator.execute_parallel([task1, task2])
    duration = time.time() - start
    assert duration < (TASK1_TIME + TASK2_TIME) * 0.8  # 20% margin
```

### 3.2 Token Pool

**File**: `src/hecaton/resources/token_pool.py`
**Source**: Simplify from `multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py`
**Requirements**:
- Exactly 2 tokens
- Thread-safe access
- Round-robin rotation

**Implementation**:
```python
class MinimalTokenPool:
    def __init__(self):
        self.tokens = [
            os.getenv("CLAUDE_CODE_TOKEN"),
            os.getenv("CLAUDE_CODE_TOKEN_1")
        ]
        self.index = 0
        self.lock = threading.Lock()

    def get_token(self) -> str:
        with self.lock:
            token = self.tokens[self.index]
            self.index = (self.index + 1) % 2
            return token
```

### 3.3 Worktree Manager

**File**: `src/hecaton/resources/worktree.py`
**Source**: Adapt from `multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py`
**Critical Pattern**: Use `git branch` NOT `git checkout -b`

**Implementation**:
```python
def create_worktree(agent_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    branch = f"hecaton/phase0/{agent_id}_{timestamp}"
    worktree_path = Path(f"/tmp/hecaton_{agent_id}")

    # Critical: branch without checkout
    subprocess.run(["git", "branch", branch])
    subprocess.run(["git", "worktree", "add", str(worktree_path), branch])

    return worktree_path
```

### 3.4 CLI Runner

**File**: `src/hecaton/cli/runner.py`
**Purpose**: Minimal CLI for testing parallel execution

**Implementation**:
```python
def test_parallel():
    """Test 2-agent parallel execution"""
    tasks = [
        {"id": "agent1", "prompt": "Create a hello.py file"},
        {"id": "agent2", "prompt": "Create a world.py file"}
    ]

    orchestrator = HecatonOrchestrator()
    results = orchestrator.execute_parallel(tasks)

    print(f"✅ Parallel execution complete")
    print(f"Agent 1: {results[0]['status']}")
    print(f"Agent 2: {results[1]['status']}")
```

## 4. File Structure for Phase 0

```
apps/hecaton/
├── src/hecaton/
│   ├── orchestration/
│   │   └── send_api.py          # Send API orchestrator
│   ├── resources/
│   │   ├── token_pool.py        # 2-token pool
│   │   └── worktree.py          # Worktree manager
│   └── cli/
│       └── runner.py             # Test CLI
└── tests/
    ├── test_send_api.py          # Send API tests
    ├── test_token_pool.py        # Token pool tests
    ├── test_worktree.py          # Worktree tests
    └── test_parallel.py          # Integration test
```

## 5. Implementation Tasks

### Task 1: Setup Environment (30 min)
- [ ] Copy .env.example to .env
- [ ] Add CLAUDE_CODE_TOKEN values
- [ ] Run ./scripts/run.sh setup
- [ ] Verify Python 3.11+ installed

### Task 2: Implement Token Pool (1 hour)
- [ ] Create token_pool.py
- [ ] Copy pattern from reference
- [ ] Simplify to 2 tokens
- [ ] Add thread lock
- [ ] Write unit tests
- [ ] Verify thread safety

### Task 3: Implement Worktree Manager (1 hour)
- [ ] Create worktree.py
- [ ] Copy pattern from reference
- [ ] Use git branch (not checkout)
- [ ] Add cleanup method
- [ ] Write unit tests
- [ ] Test isolation

### Task 4: Implement Send API (2 hours)
- [ ] Create send_api.py
- [ ] Copy LangGraph pattern
- [ ] Use add_conditional_edges
- [ ] Return Send objects
- [ ] Write unit tests
- [ ] Verify parallel execution

### Task 5: Create CLI Runner (30 min)
- [ ] Create runner.py
- [ ] Add test_parallel command
- [ ] Wire up components
- [ ] Add progress output

### Task 6: Integration Testing (1 hour)
- [ ] Create test_parallel.py
- [ ] Test 2 agents simultaneously
- [ ] Verify no conflicts
- [ ] Measure performance
- [ ] Document results

### Task 7: Documentation (30 min)
- [ ] Update README with Phase 0 status
- [ ] Document test results
- [ ] Create Phase 1 plan
- [ ] Commit everything

## 6. Test Specifications

### 6.1 Unit Tests Required

**test_token_pool.py**:
- `test_loads_two_tokens`
- `test_round_robin_rotation`
- `test_thread_safety`
- `test_missing_token_error`

**test_worktree.py**:
- `test_creates_unique_worktree`
- `test_uses_git_branch_pattern`
- `test_cleanup_removes_worktree`
- `test_no_conflicts_between_agents`

**test_send_api.py**:
- `test_uses_conditional_edges`
- `test_returns_send_objects`
- `test_parallel_node_execution`
- `test_state_management`

### 6.2 Integration Test

**test_parallel.py**:
```python
async def test_two_agents_parallel():
    """Verify 2 agents run simultaneously"""
    orchestrator = HecatonOrchestrator()

    # Tasks that take ~10 seconds each
    tasks = [
        {"id": "agent1", "prompt": "Count to 10 slowly"},
        {"id": "agent2", "prompt": "Count to 10 slowly"}
    ]

    start = time.time()
    results = await orchestrator.execute_parallel(tasks)
    duration = time.time() - start

    # Should take ~10s, not 20s
    assert duration < 15  # Allow some overhead
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)
```

## 7. Definition of Done

### Phase 0 is DONE when:

- [x] All specifications written
- [x] Design approved
- [ ] Environment configured
- [ ] Token pool implemented and tested
- [ ] Worktree manager implemented and tested
- [ ] Send API orchestrator implemented and tested
- [ ] CLI runner functional
- [ ] Integration test passing
- [ ] 2 agents execute in parallel
- [ ] Performance target met (<15s for two 10s tasks)
- [ ] Code committed to git
- [ ] README updated

## 8. Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|---------|
| Parallel Agents | 2 | - | 🔄 |
| Execution Speedup | >1.5x | - | 🔄 |
| Test Coverage | 100% | - | 🔄 |
| Implementation Time | <2 days | - | 🔄 |

## 9. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| Token conflicts | Low | High | Thread locks |
| Worktree conflicts | Medium | High | Unique branches |
| Send API issues | Low | High | Use proven pattern |
| Environment issues | Medium | Medium | Clear setup docs |

## 10. Phase 1 Preview

Once Phase 0 is working, we'll immediately use it to:
1. Expand token pool to 5 tokens (agent 1 task)
2. Add error handling (agent 2 task)
3. Test with 5 agents
4. Document improvements

---

## Ready to Start!

All specifications are complete. Begin with:

```bash
cd apps/hecaton
cp .env.example .env
# Add tokens to .env
./scripts/run.sh setup
# Start Task 1
```
