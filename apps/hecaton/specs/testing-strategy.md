# HECATON Testing Strategy

## Version: 1.0.0
## Status: Ready for Implementation
## Last Updated: 2025-08-26

---

## 1. Testing Philosophy

### Core Principles
1. **Test Before Merge**: No code without tests
2. **100% Critical Path Coverage**: Send API, Token Pool, Worktrees
3. **Fast Feedback**: Tests run in <30 seconds
4. **Real Integration Tests**: Actually execute Claude Code (in Phase 0 verification)
5. **Progressive Testing**: Each phase tests the next phase's bootstrap

## 2. Test Pyramid

```
         /\
        /E2E\        (5%)  - Full system, real Claude execution
       /------\
      /Integration\  (25%) - Component interactions
     /------------\
    / Unit Tests   \ (70%) - Individual components
   /________________\
```

## 3. Phase 0 Test Requirements

### 3.1 Critical Components (100% Coverage Required)

#### Send API Orchestrator Tests
```python
# tests/unit/test_send_api.py

def test_uses_add_conditional_edges():
    """REQ-004: Verify correct LangGraph pattern"""
    orchestrator = SendAPIOrchestrator()
    # Inspect workflow structure
    assert "conditional_edges" in orchestrator.workflow._edges
    assert not "regular_edges" in str(orchestrator.workflow)

def test_returns_send_objects():
    """REQ-001: Verify Send objects created"""
    orchestrator = SendAPIOrchestrator()
    sends = orchestrator._create_send_objects({"tasks": [task1, task2]})
    assert len(sends) == 2
    assert all(isinstance(s, Send) for s in sends)

def test_parallel_execution_nodes():
    """REQ-001: Verify parallel node setup"""
    orchestrator = SendAPIOrchestrator()
    # Both agents should target same "execute" node
    sends = orchestrator._create_send_objects({"tasks": [task1, task2]})
    assert all(s.node == "execute" for s in sends)
```

#### Token Pool Tests
```python
# tests/unit/test_token_pool.py

def test_loads_exactly_two_tokens():
    """REQ-002: Phase 0 has exactly 2 tokens"""
    pool = TokenPool()
    assert len(pool._tokens) == 2
    assert pool._tokens[0] is not None
    assert pool._tokens[1] is not None

def test_round_robin_rotation():
    """REQ-002: Tokens rotate in order"""
    pool = TokenPool()
    token1 = pool.get_token()
    token2 = pool.get_token()
    token3 = pool.get_token()
    assert token1 != token2  # Different tokens
    assert token1 == token3  # Back to first

def test_thread_safety():
    """REQ-002: Concurrent access is safe"""
    pool = TokenPool()
    tokens = []

    def get_token():
        tokens.append(pool.get_token())

    threads = [Thread(target=get_token) for _ in range(100)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(tokens) == 100
    assert len(set(tokens)) == 2  # Only 2 unique tokens
```

#### Worktree Manager Tests
```python
# tests/unit/test_worktree.py

def test_creates_unique_worktree():
    """REQ-003: Each agent gets unique space"""
    manager = WorktreeManager()
    wt1 = manager.create("agent1")
    wt2 = manager.create("agent2")
    assert wt1 != wt2
    assert wt1.exists()
    assert wt2.exists()

def test_uses_git_branch_not_checkout():
    """REQ-003: Critical pattern compliance"""
    manager = WorktreeManager()
    with patch('subprocess.run') as mock_run:
        manager.create("test")
        # Verify 'git branch' called, not 'git checkout -b'
        calls = [str(call) for call in mock_run.call_args_list]
        assert any("git', 'branch'" in call for call in calls)
        assert not any("checkout" in call for call in calls)

def test_cleanup_removes_worktree():
    """REQ-016: Resource cleanup"""
    manager = WorktreeManager()
    wt = manager.create("test")
    assert wt.exists()
    manager.cleanup("test")
    assert not wt.exists()
```

### 3.2 Integration Tests

```python
# tests/integration/test_parallel_execution.py

@pytest.mark.integration
async def test_two_agents_execute_simultaneously():
    """REQ-001: Primary requirement - parallel execution"""
    orchestrator = HecatonOrchestrator()

    # Create tasks with timing markers
    task1 = {
        "id": "agent1",
        "prompt": "import time; time.sleep(5); print('Agent 1 done')"
    }
    task2 = {
        "id": "agent2",
        "prompt": "import time; time.sleep(5); print('Agent 2 done')"
    }

    start = time.time()
    results = await orchestrator.execute_parallel([task1, task2])
    duration = time.time() - start

    # Should take ~5s not 10s
    assert duration < 7  # Allow 2s overhead
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)

@pytest.mark.integration
def test_no_resource_conflicts():
    """REQ-003: Agents don't interfere"""
    orchestrator = HecatonOrchestrator()

    # Both create same filename
    task1 = {"id": "agent1", "prompt": "Create output.txt with 'Agent 1'"}
    task2 = {"id": "agent2", "prompt": "Create output.txt with 'Agent 2'"}

    results = orchestrator.execute_parallel([task1, task2])

    # Each should succeed in their own worktree
    assert all(r["status"] == "success" for r in results)
    # Files should exist in separate worktrees
    assert Path(results[0]["worktree"]) != Path(results[1]["worktree"])
```

### 3.3 End-to-End Test (Manual Verification)

```python
# tests/e2e/test_phase0_complete.py

@pytest.mark.e2e
@pytest.mark.skipif(not os.getenv("RUN_E2E"), reason="E2E tests require tokens")
def test_phase0_with_real_claude():
    """Complete Phase 0 validation with real Claude Code"""

    # This test actually calls Claude Code CLI
    orchestrator = HecatonOrchestrator()

    tasks = [
        {
            "id": "fibonacci",
            "prompt": "Create a fibonacci.py with a function to calculate fibonacci"
        },
        {
            "id": "prime",
            "prompt": "Create a prime.py with a function to check if a number is prime"
        }
    ]

    results = orchestrator.execute_parallel(tasks)

    # Verify both completed
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)

    # Verify files created
    fib_file = Path(results[0]["worktree"]) / "fibonacci.py"
    prime_file = Path(results[1]["worktree"]) / "prime.py"
    assert fib_file.exists()
    assert prime_file.exists()

    # Could even test the generated code works
    # exec(fib_file.read_text())
    # assert fibonacci(10) == 55
```

## 4. Test Execution Strategy

### 4.1 Test Commands

```bash
# Unit tests only (fast, no tokens needed)
pytest tests/unit -v

# Integration tests (requires git)
pytest tests/integration -v

# Full test suite
pytest tests/ -v --cov=hecaton --cov-report=html

# E2E tests (requires Claude tokens)
RUN_E2E=1 pytest tests/e2e -v

# Parallel test execution
pytest tests/ -n auto

# Watch mode for development
ptw -- tests/unit
```

### 4.2 CI/CD Pipeline

```yaml
# .github/workflows/test.yml (future)
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit tests/integration
      - run: black --check src/ tests/
      - run: mypy src/
```

## 5. Test Data & Fixtures

### 5.1 Fixtures

```python
# tests/conftest.py

@pytest.fixture
def mock_tokens(monkeypatch):
    """Mock tokens for testing without real tokens"""
    monkeypatch.setenv("CLAUDE_CODE_TOKEN", "test_token_1")
    monkeypatch.setenv("CLAUDE_CODE_TOKEN_1", "test_token_2")

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create temporary git repo for worktree tests"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo)
    (repo / "README.md").write_text("Test")
    subprocess.run(["git", "add", "."], cwd=repo)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo)
    return repo

@pytest.fixture
def orchestrator(mock_tokens, temp_git_repo):
    """Configured orchestrator for testing"""
    config = OrchestratorConfig(
        base_repo=temp_git_repo,
        token_pool_size=2
    )
    return HecatonOrchestrator(config)
```

## 6. Coverage Requirements

### Phase 0 Coverage Goals

| Component | Required | Current | Status |
|-----------|----------|---------|---------|
| Send API | 100% | 0% | ⏳ |
| Token Pool | 100% | 0% | ⏳ |
| Worktree Manager | 100% | 0% | ⏳ |
| CLI Runner | 80% | 0% | ⏳ |
| Integration | 90% | 0% | ⏳ |

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=hecaton --cov-report=term-missing

# HTML coverage report
pytest --cov=hecaton --cov-report=html
open htmlcov/index.html

# Fail if coverage below threshold
pytest --cov=hecaton --cov-fail-under=80
```

## 7. Test Documentation

### 7.1 Test Naming Convention

```python
def test_<component>_<behavior>_<expectation>():
    """
    REQ-XXX: Brief description

    Given: Initial state
    When: Action taken
    Then: Expected outcome
    """
```

### 7.2 Test Categories

- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - Component interaction tests
- `@pytest.mark.e2e` - Full system tests
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.requires_tokens` - Tests needing Claude tokens

## 8. Phase-Specific Testing

### Phase 0: Manual Testing
- Developer writes all tests
- Focus on critical path
- 100% coverage for core components

### Phase 1: Assisted Testing
- Agents help write additional tests
- Expand coverage to error paths
- Add performance benchmarks

### Phase 2: Automated Testing
- Agents generate test cases
- Property-based testing added
- Mutation testing introduced

### Phase 3: Self-Testing
- System tests its own improvements
- Automatic regression detection
- Performance regression tests

### Phase 4: Continuous Testing
- Tests evolve with system
- Automatic test generation
- Self-healing tests

## 9. Debugging & Troubleshooting

### Common Test Issues

**Issue**: Tests fail with "git: worktree not found"
**Solution**: Ensure git version > 2.5 (worktree support)

**Issue**: Token pool tests hang
**Solution**: Check threading.Lock() implementation

**Issue**: Send API tests fail
**Solution**: Verify LangGraph version matches requirements

### Debug Commands

```bash
# Run specific test with debugging
pytest -vv -s tests/unit/test_send_api.py::test_uses_add_conditional_edges

# Run with pdb on failure
pytest --pdb tests/

# Show test execution order
pytest --collect-only tests/

# Profile slow tests
pytest --durations=10 tests/
```

## 10. Success Criteria

Phase 0 testing is successful when:
- [ ] All unit tests pass (100%)
- [ ] Integration tests verify parallel execution
- [ ] No resource conflicts detected
- [ ] Coverage exceeds 80% overall
- [ ] Critical components have 100% coverage
- [ ] Performance targets met
- [ ] E2E test passes with real Claude (optional)

---

## Ready to Test!

Start with:
```bash
cd apps/hecaton
# Write first test
nano tests/unit/test_token_pool.py
# Run it
pytest tests/unit/test_token_pool.py -v
```
