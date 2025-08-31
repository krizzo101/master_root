# HECATON Technical Design Specification

## Version: 1.0.0
## Status: Draft
## Last Updated: 2025-08-26

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   USER INTERFACE                        │
│                 (CLI / API / Dashboard)                 │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Orchestrator │  │Agent Registry│  │Phase Manager │ │
│  │  (Send API)  │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   EXECUTION PLANE                       │
│      ┌────────────────────────────────────────┐       │
│      │         Agent Execution Pool           │       │
│      │    (1-15 Parallel Claude Code Agents)  │       │
│      └────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   RESOURCE PLANE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Token Pool   │  │   Worktree   │  │   Storage    │ │
│  │              │  │   Manager    │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Component Interactions

```python
# Sequence for parallel execution (REQ-001)
1. User submits tasks via CLI
2. Orchestrator receives tasks
3. Orchestrator requests tokens from TokenPool
4. Orchestrator requests worktrees from WorktreeManager
5. Orchestrator creates Send objects via LangGraph
6. Send API triggers parallel agent execution
7. Agents execute in isolated worktrees
8. Results collected and returned
```

## 2. Detailed Component Design

### 2.1 Orchestrator Component (REQ-001, REQ-004)

```python
class HecatonOrchestrator:
    """
    Main orchestrator implementing Send API pattern
    Location: src/hecaton/core/orchestrator.py
    References: multi-agent-reference/oamat-sd/execution_engine.py
    """

    def __init__(self, config: OrchestratorConfig):
        self.workflow = StateGraph(dict)  # LangGraph state
        self.token_pool = TokenPool()
        self.worktree_manager = WorktreeManager()
        self._setup_workflow()

    def _setup_workflow(self):
        """Critical: Must use add_conditional_edges"""
        self.workflow.add_node("distribute", self.distribute_tasks)
        self.workflow.add_node("execute", self.execute_agent)

        # CRITICAL: Send API pattern
        self.workflow.add_conditional_edges(
            "distribute",
            self._create_send_objects,  # Returns List[Send]
            ["execute"]
        )

    def _create_send_objects(self, state: Dict) -> List[Send]:
        """
        Creates Send objects for parallel execution.
        Each Send object contains:
        - Target node ("execute")
        - Agent configuration
        - Token assignment
        - Worktree path
        """
        sends = []
        for task in state.get("tasks", []):
            sends.append(Send("execute", {
                "task": task,
                "token": self.token_pool.acquire(),
                "worktree": self.worktree_manager.create(task["id"])
            }))
        return sends
```

### 2.2 Token Pool Component (REQ-002)

```python
class TokenPool:
    """
    Thread-safe token pool with round-robin rotation
    Location: src/hecaton/resources/token_pool.py
    References: multi-agent-reference/multi-agent-monitor/orchestration/token_pool.py
    """

    def __init__(self):
        self._tokens = self._load_tokens()  # From environment
        self._index = 0
        self._lock = threading.Lock()  # Thread safety
        self._usage = defaultdict(int)  # Usage tracking

    def acquire(self) -> Token:
        """Thread-safe token acquisition"""
        with self._lock:
            token = self._tokens[self._index]
            self._index = (self._index + 1) % len(self._tokens)
            self._usage[token.id] += 1
            return token

    def release(self, token: Token):
        """Token release (for future enhancement)"""
        pass  # Phase 0: No-op
```

### 2.3 Worktree Manager Component (REQ-003)

```python
class WorktreeManager:
    """
    Git worktree isolation manager
    Location: src/hecaton/resources/worktree.py
    References: multi-agent-reference/multi-agent-monitor/orchestration/worktree_manager.py
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.active_worktrees = {}

    def create(self, agent_id: str) -> Path:
        """
        Creates isolated worktree for agent.
        Critical: Uses 'git branch' not 'git checkout -b'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch = f"hecaton/{timestamp}/{agent_id}"
        worktree_path = self.base_path / f"{agent_id}_{timestamp}"

        # Create branch WITHOUT checkout (avoids conflicts)
        subprocess.run(["git", "branch", branch], check=True)

        # Add worktree
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch],
            check=True
        )

        self.active_worktrees[agent_id] = worktree_path
        return worktree_path

    def cleanup(self, agent_id: str):
        """Remove worktree and branch"""
        if agent_id in self.active_worktrees:
            path = self.active_worktrees[agent_id]
            subprocess.run(
                ["git", "worktree", "remove", str(path), "--force"]
            )
```

### 2.4 Agent Wrapper Component

```python
class ClaudeAgent:
    """
    Wrapper for Claude Code CLI execution
    Location: src/hecaton/agents/claude_agent.py
    """

    def __init__(self, agent_id: str, token: Token, worktree: Path):
        self.agent_id = agent_id
        self.token = token
        self.worktree = worktree

    async def execute(self, task: Dict) -> Dict:
        """Execute task using Claude Code CLI"""
        env = {
            "CLAUDE_CODE_TOKEN": self.token.value,
            # Remove conflicting env vars
            "ANTHROPIC_API_KEY": None,
            "OPENAI_API_KEY": None
        }

        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--output-format", "json",
            "-p", self._build_prompt(task)
        ]

        result = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            cwd=self.worktree,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await result.communicate()
        return self._parse_result(stdout, stderr, result.returncode)
```

## 3. Data Flow Design

### 3.1 Task Processing Pipeline

```
Input Tasks → Validation → Distribution → Parallel Execution → Collection → Output
     │             │            │               │                  │           │
     │             │            │               │                  │           │
  JSON/YAML    Schema      Send API      Claude Agents      Aggregation   JSON/File
             Validation                    (Isolated)
```

### 3.2 State Management

```python
@dataclass
class OrchestratorState:
    """Central state for orchestration"""
    task_id: str
    tasks: List[Task]
    agents: List[AgentState]
    results: Dict[str, Any]
    phase: Phase
    status: Status
    errors: List[Error]
    metrics: Metrics
```

### 3.3 Message Flow (Phase 2+)

```
Agent A → Message Queue → Topic/Direct → Message Queue → Agent B
             ↓                                ↑
        File Storage                    Priority Queue
```

## 4. Phase-Specific Design

### 4.1 Phase 0: Minimal Core (Current)

**Components:**
- Basic Orchestrator with Send API
- 2-Token Pool
- Simple Worktree Manager
- CLI Runner

**Limitations:**
- No error recovery
- No agent registry
- No messaging
- Fixed 2 agents

### 4.2 Phase 1: Self-Expansion

**New Components:**
- Bootstrap Manager
- Token Pool Expander
- Error Handler
- Retry Mechanism

**Key Method:**
```python
async def bootstrap_phase_1(self):
    """Use 2 agents to build 5-agent capability"""
    tasks = [
        {"id": "expand_tokens", "prompt": "Modify token_pool.py to support 5 tokens"},
        {"id": "add_retry", "prompt": "Add retry logic to orchestrator.py"}
    ]
    results = await self.execute_parallel(tasks)
    self._apply_modifications(results)
```

### 4.3 Phase 2: Feature Enhancement

**New Components:**
- Agent Registry
- Message Queue
- Phase Manager
- Template System

### 4.4 Phase 3: Autonomous Operation

**New Components:**
- Performance Monitor
- Bottleneck Analyzer
- Task Generator
- Self-Tester

### 4.5 Phase 4: Continuous Optimization

**New Components:**
- Optimization Loop
- Learning System
- Documentation Generator

## 5. Interface Design

### 5.1 CLI Interface

```bash
# Phase 0 commands
hecaton execute --tasks tasks.json
hecaton test-parallel
hecaton status

# Phase 1+ commands
hecaton bootstrap --phase 1
hecaton agent list
hecaton monitor
```

### 5.2 API Interface (Future)

```python
# REST API endpoints
POST   /api/v1/tasks          # Submit tasks
GET    /api/v1/tasks/{id}     # Get task status
GET    /api/v1/agents         # List agents
POST   /api/v1/bootstrap      # Trigger bootstrap
GET    /api/v1/metrics        # Get metrics
```

## 6. Error Handling Strategy

### 6.1 Error Categories

1. **Token Errors**: Retry with different token
2. **Worktree Errors**: Cleanup and recreate
3. **Agent Failures**: Retry up to 3 times
4. **System Errors**: Graceful shutdown

### 6.2 Recovery Mechanisms

```python
class ErrorRecovery:
    def handle_agent_failure(self, agent_id: str, error: Exception):
        if isinstance(error, TokenError):
            new_token = self.token_pool.acquire_different()
            return self.retry_with_token(agent_id, new_token)
        elif isinstance(error, WorktreeError):
            self.worktree_manager.cleanup(agent_id)
            return self.retry_with_new_worktree(agent_id)
        else:
            return self.mark_failed(agent_id, error)
```

## 7. Security Considerations

### 7.1 Token Security
- Never log token values
- Hash tokens for identification
- Store in environment variables
- Rotate on failure

### 7.2 Worktree Isolation
- Unique branches per agent
- No shared state
- Clean up on completion
- Prevent path traversal

### 7.3 Self-Modification Safety
- Immutable core files
- Changes tested in isolation
- Rollback capability
- Audit logging

## 8. Performance Design

### 8.1 Optimization Goals
- 3-5x speedup over sequential (REQ-013)
- Support 15 parallel agents (REQ-014)
- < 100ms message latency
- < 2s worktree creation

### 8.2 Bottleneck Mitigation
- Token pool prevents rate limiting
- Worktree creation parallelized
- Async I/O throughout
- Lazy loading of resources

## 9. Testing Strategy

### 9.1 Test Levels
1. **Unit Tests**: Individual components
2. **Integration Tests**: Component interactions
3. **System Tests**: End-to-end workflows
4. **Performance Tests**: Benchmarks

### 9.2 Test Coverage Requirements
- Phase 0: 80% coverage minimum
- Critical paths: 100% coverage
- Send API: 100% coverage
- Token Pool: 100% coverage

## 10. Implementation Priority

### Phase 0 (Immediate)
1. Send API Orchestrator
2. Token Pool (2 tokens)
3. Worktree Manager
4. CLI Runner
5. Basic Tests

### Phase 1 (After Phase 0 Works)
1. Bootstrap Manager
2. Token Expansion
3. Error Recovery
4. Retry Logic

### Phases 2-4 (Progressive)
- Built by the system itself
- Each phase enables the next

---

## Design Validation Checklist

- [x] All requirements addressed
- [x] Component interfaces defined
- [x] Data flow documented
- [x] Error handling specified
- [x] Security considered
- [x] Performance targets set
- [x] Testing strategy defined
- [ ] Design reviewed
- [ ] Design approved

## Next Steps

1. Review and approve design
2. Create implementation tasks
3. Write test specifications
4. Begin Phase 0 coding
