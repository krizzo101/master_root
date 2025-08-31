# Multi-Agent Architecture v2.0
## Production-Ready Claude Code Orchestration Framework

### Last Updated: 2025-08-26
### Status: Design Complete, Implementation Ready

---

## Executive Summary

This architecture document presents a **production-ready multi-agent orchestration framework** built on proven patterns from 135+ analyzed code files, successful POCs, and existing infrastructure. After extensive research and consolidation, we've identified that **we already possess 80% of required capabilities** through our existing Claude Code infrastructure, MCP servers, and .claude/ tooling.

**Key Decision**: Build on existing infrastructure with selective pattern adoption rather than adopting external frameworks (LangGraph, AutoGen, CrewAI).

## 🎯 Core Architecture Principles

### 1. **Leverage Existing Infrastructure**
- 15-token pool for parallel execution (already implemented)
- 87+ MCP tools (already integrated)
- 100+ .claude/ commands (already available)
- Git worktree isolation (proven in POC)

### 2. **Proven Patterns Only**
- LangGraph Send API (3-5x performance gain)
- Round-robin token rotation
- Phase-based SDLC progression
- Agent registry for extensibility

### 3. **Avoid Complexity**
- No external framework dependencies
- No O3/GPT-5 model requirements
- No asyncio.gather (violates Rule 997)
- No over-engineered meta-intelligence

## 🏗️ Three-Plane Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE                           │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Orchestrator   │  │    Agent     │  │  Phase Manager  │  │
│  │  - Send API     │  │   Registry   │  │  - SDLC Gates   │  │
│  │  - State Graph  │  │  - Dynamic   │  │  - Quality      │  │
│  │  - Routing      │  │  - Factory   │  │  - Progression  │  │
│  └─────────────────┘  └──────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Task Manager   │  │   Message    │  │    Session      │  │
│  │  - Decompose    │  │    Queue     │  │   Management    │  │
│  │  - Distribute   │  │  - Pub/Sub   │  │  - State        │  │
│  │  - Monitor      │  │  - Priority  │  │  - History      │  │
│  └─────────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         EXECUTION PLANE                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Agent Pool (1-15 concurrent)                 │ │
│  │                                                           │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │ │
│  │  │   Agent 1  │  │   Agent 2  │  │   Agent N  │  ...   │ │
│  │  │ Claude Code│  │ Claude Code│  │ Claude Code│        │ │
│  │  │ Worktree 1 │  │ Worktree 2 │  │ Worktree N │        │ │
│  │  └────────────┘  └────────────┘  └────────────┘        │ │
│  │                                                           │ │
│  │  Each agent:                                             │ │
│  │  - Isolated git worktree                                 │ │
│  │  - Dedicated token from pool                             │ │
│  │  - Specific role/capability                              │ │
│  │  - MCP tool access                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┐
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RESOURCE PLANE                          │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Token Pool    │  │ MCP Servers  │  │  Git Manager    │  │
│  │  - 15 tokens    │  │  - 87+ tools │  │  - Worktrees    │  │
│  │  - Round-robin  │  │  - FastMCP   │  │  - Branches     │  │
│  │  - Statistics   │  │  - Resources │  │  - Isolation    │  │
│  └─────────────────┘  └──────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Knowledge     │  │   Storage    │  │    Monitoring   │  │
│  │     Base        │  │  - SQLite    │  │  - Metrics      │  │
│  │  - Neo4j        │  │  - Files     │  │  - Logs         │  │
│  │  - Patterns     │  │  - Cache     │  │  - Traces       │  │
│  └─────────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔑 Critical Components

### 1. Orchestrator (Control Plane)
**Technology**: LangGraph StateGraph with Send API
```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        self.token_pool = SecureTokenPool()
        self.worktree_manager = WorktreeManager()
        self.agent_registry = AgentRegistry()

    def setup_workflow(self):
        # CRITICAL: Use add_conditional_edges for Send API
        self.workflow.add_conditional_edges(
            "distribute_agents",
            self._create_send_objects,  # Returns [Send(...), Send(...)]
            ["execute_agent"]
        )
```

### 2. Token Pool (Resource Plane)
**Implementation**: Thread-safe round-robin with 15 tokens
```python
class SecureTokenPool:
    def __init__(self, tokens: List[str]):
        self._tokens = tokens  # 15 Claude Code tokens
        self._token_index = 0
        self._lock = threading.Lock()

    def get_token(self) -> Tuple[str, str]:
        with self._lock:
            token = self._tokens[self._token_index]
            self._token_index = (self._token_index + 1) % len(self._tokens)
            return token, self._hash_token(token)
```

### 3. Worktree Manager (Resource Plane)
**Purpose**: Isolated execution environments
```python
class WorktreeManager:
    def create_agent_worktree(self, agent_id: str, agent_type: str):
        branch_name = f"agent/{timestamp}/{agent_type}/{agent_id}"
        worktree_path = Path(f"/home/opsvi/agent_worktrees/{agent_id}")

        # Create branch without checking out
        subprocess.run(["git", "branch", branch_name])

        # Add worktree
        subprocess.run(["git", "worktree", "add", worktree_path, branch_name])

        return worktree_path
```

### 4. Agent Registry (Control Plane)
**Design**: Dynamic agent type management
```python
class AgentRegistry:
    def __init__(self):
        self._agents = {}
        self._load_sdlc_agents()  # From .claude/agents/

    def register_agent(self, agent_type: str, config: AgentConfig):
        self._agents[agent_type] = config

    def create_agent(self, agent_type: str, job_id: str) -> ClaudeCodeAgent:
        config = self._agents[agent_type]
        return ClaudeCodeAgent(
            job_id=job_id,
            config=config,
            token=self.token_pool.get_token(),
            worktree=self.worktree_manager.create_agent_worktree(job_id, agent_type)
        )
```

## 📋 Agent Types & Capabilities

### Core SDLC Agents (from .claude/agents/)
| Agent Type | Primary Role | Key Tools | Phase |
|------------|--------------|-----------|-------|
| `sdlc-discovery` | Requirements & Research | search, analyze, document | Discovery |
| `sdlc-design` | Architecture & Design | diagram, spec, model | Design |
| `sdlc-planning` | Task Breakdown | estimate, schedule, assign | Planning |
| `sdlc-development` | Implementation | code, refactor, optimize | Development |
| `sdlc-testing` | Quality Assurance | test, validate, verify | Testing |
| `sdlc-deployment` | Production Prep | build, deploy, monitor | Deployment |
| `sdlc-production` | Final Review | review, document, handover | Production |
| `sdlc-postmortem` | Lessons Learned | analyze, report, improve | Postmortem |

### Specialized Agents (from multi-agent-reference)
| Agent Type | Specialization | Source Project |
|------------|----------------|----------------|
| `requirements-analyst` | Functional requirements | multi-agent-monitor |
| `business-analyst` | Business context | multi-agent-monitor |
| `security-architect` | Security design | ACCF |
| `solution-architect` | System architecture | ACCF |
| `test-remediation-specialist` | Bug fixing | claude-code |
| `performance-optimizer` | Performance tuning | ACCF |
| `technical-writer` | Documentation | ACCF |
| `code-analyzer` | Code review | ACCF |

## 🔄 Workflow Patterns

### 1. Parallel Task Distribution
```python
def distribute_tasks(self, tasks: List[Task]) -> List[Send]:
    """Create Send objects for parallel execution"""
    sends = []
    for task in tasks:
        agent = self.agent_registry.create_agent(task.agent_type, task.id)
        sends.append(Send("execute_agent", {
            "agent": agent,
            "task": task,
            "token": agent.token,
            "worktree": agent.worktree
        }))
    return sends  # All execute in parallel
```

### 2. SDLC Phase Progression
```python
def execute_sdlc_workflow(self, project: Project):
    phases = ["discovery", "design", "planning", "development", "testing", "deployment"]

    for phase in phases:
        # Quality gate check
        if not self.check_prerequisites(phase):
            return self.handle_gate_failure(phase)

        # Execute phase with appropriate agents
        agents = self.get_phase_agents(phase)
        results = self.orchestrator.execute_parallel(agents)

        # Phase validation
        if not self.validate_phase_outputs(phase, results):
            return self.handle_validation_failure(phase, results)

        # Progress to next phase
        self.record_phase_completion(phase, results)
```

### 3. Progressive Autonomy
```python
def get_agent_autonomy_level(self, phase: str, iteration: int) -> str:
    """Agents gain freedom as workflow progresses"""
    if phase in ["discovery", "design"] and iteration < 3:
        return "strict"  # High guidance, templates
    elif phase in ["planning", "development"] and iteration < 5:
        return "guided"  # Medium guidance
    else:
        return "autonomous"  # Full freedom
```

## 🚀 Implementation Strategy

### Phase 0: Foundation (Week 1)
- [ ] Set up LangGraph Send API orchestrator
- [ ] Configure 15-token pool
- [ ] Implement worktree isolation
- [ ] Basic 2-agent parallel POC

### Phase 1: Agent Management (Week 2)
- [ ] Build agent registry
- [ ] Integrate .claude/agents/ profiles
- [ ] Create agent factory
- [ ] Test 5-agent scenarios

### Phase 2: Workflow Engine (Week 3)
- [ ] Implement SDLC phase manager
- [ ] Add quality gates
- [ ] Create task decomposer
- [ ] Test phase transitions

### Phase 3: Communication (Week 4)
- [ ] Build message queue
- [ ] Add pub/sub system
- [ ] Implement agent discovery
- [ ] Test 10-agent coordination

### Phase 4: Production Features (Week 5)
- [ ] Add monitoring/metrics
- [ ] Implement error recovery
- [ ] Create dashboard
- [ ] Performance optimization

### Phase 5: Scale Testing (Week 6)
- [ ] 15-agent stress tests
- [ ] Complex workflow scenarios
- [ ] Performance benchmarking
- [ ] Production readiness review

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parallel Execution | 15 agents | Concurrent worktrees |
| Performance Gain | 3-5x | vs. sequential |
| Token Utilization | >80% | Active tokens/total |
| Phase Success Rate | >95% | Passed gates/total |
| Agent Reliability | >99% | Successful/total tasks |
| Message Latency | <100ms | Avg delivery time |

## 🚫 Anti-Patterns to Avoid

1. **DO NOT use asyncio.gather()** - Violates Rule 997
2. **DO NOT adopt external frameworks wholesale** - We have 80% already
3. **DO NOT create sequential bottlenecks** - Use Send API
4. **DO NOT share worktrees between agents** - Causes conflicts
5. **DO NOT exceed 15 concurrent agents** - Token pool limit
6. **DO NOT skip quality gates** - Ensures phase integrity
7. **DO NOT use O3/GPT-5 models** - Stick with Claude Code

## 📚 References

- `multi-agent-reference/` - Consolidated code patterns
- `CRITICAL_PATTERNS_ANALYSIS.md` - Must-implement patterns
- `UNIFIED_IMPLEMENTATION_ROADMAP.md` - Day-by-day implementation
- `.claude/agents/` - SDLC agent profiles
- `apps/multi-agent-monitor/` - Working POC code

## 🔐 Security & Safety

- Token rotation prevents rate limiting
- Worktree isolation prevents conflicts
- Quality gates prevent bad propagation
- Circuit breakers prevent cascading failures
- Audit logging for compliance

## 📈 Future Enhancements

- Cross-session persistence with Neo4j
- Hierarchical meta-coordination for 50+ agents
- Dynamic load balancing based on complexity
- Self-healing agent networks
- Automated performance optimization

---

**Architecture Status**: APPROVED FOR IMPLEMENTATION
**Next Step**: Begin Phase 0 - Foundation Setup
