# Worktree Architecture for Multi-Agent System

## Overview

Git worktrees are a **core architectural component** of our multi-agent orchestration system, not an optional feature. They provide the foundation for safe, parallel agent execution.

## Why Worktrees Are Essential

### The Problem
Without worktrees, multiple agents face:
- **File conflicts** - Agents overwrite each other's changes
- **Git conflicts** - Simultaneous commits create merge nightmares
- **Sequential bottleneck** - Agents must wait their turn
- **Unsafe rollback** - Can't isolate problematic agent work
- **No true parallelism** - 15 tokens wasted on sequential execution

### The Solution
Worktrees give each agent:
- **Isolated workspace** - Complete copy of the codebase
- **Independent branch** - Clean git history per agent
- **Parallel execution** - True 15x parallelization
- **Safe experimentation** - Discard failed attempts easily
- **Clean merging** - Structured integration of agent work

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SafeOrchestrator                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                WorktreeManager (Core)                │  │
│  │                                                      │  │
│  │  • Creates isolated worktrees per agent             │  │
│  │  • Manages branch lifecycle                         │  │
│  │  • Coordinates shared message space                 │  │
│  │  • Handles merging strategies                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Execution Layer                   │  │
│  │                                                      │  │
│  │  Agent 1 ──► Worktree 1 ──► Branch: agent/1/task   │  │
│  │  Agent 2 ──► Worktree 2 ──► Branch: agent/2/task   │  │
│  │  Agent 3 ──► Worktree 3 ──► Branch: agent/3/task   │  │
│  │     ...                                             │  │
│  │  Agent 15 ─► Worktree 15 ─► Branch: agent/15/task  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## File System Layout

```
/home/opsvi/
├── master_root/                    # Main repository
│   ├── .git/                       # Primary git directory
│   └── apps/multi-agent-monitor/   # Main codebase
│
├── agent_worktrees/                # Isolated agent workspaces
│   ├── agent_1_requirements_20240115_120000/
│   │   └── [full repo copy]
│   ├── agent_2_business_20240115_120000/
│   │   └── [full repo copy]
│   └── ...
│
└── agent_shared/                   # Shared communication space
    ├── messages/                   # Inter-agent messaging
    ├── outputs/                    # Collected results
    ├── metrics/                    # Performance tracking
    └── locks/                      # Coordination locks
```

## Core Components

### 1. WorktreeManager Class

**Purpose**: Central management of all agent worktrees

**Key Methods**:
- `create_agent_worktree()` - Spin up isolated environment
- `commit_agent_work()` - Commit within worktree
- `merge_agent_work()` - Integrate back to main
- `cleanup_worktree()` - Remove and clean up

**Features**:
- Automatic branch naming convention
- Registry tracking all active worktrees
- Shared message space coordination
- Cleanup on failure or completion

### 2. SafeOrchestrator Integration

```python
class SafeOrchestrator:
    def __init__(self, use_worktrees=True):
        # Worktrees are ON by default
        self.worktree_manager = WorktreeManager()

    async def execute_phase_with_worktrees(self, agents):
        # Create worktrees for all agents
        worktrees = []
        for agent in agents:
            wt = self.worktree_manager.create_agent_worktree(
                agent_id=agent.id,
                agent_type=agent.type
            )
            worktrees.append(wt)

        # Launch agents in parallel (TRUE parallelism!)
        tasks = [
            self.launch_agent_in_worktree(agent, wt)
            for agent, wt in zip(agents, worktrees)
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # Merge successful work
        for agent, result in zip(agents, results):
            if result.success:
                self.worktree_manager.merge_agent_work(agent.id)
```

### 3. Agent Execution Environment

Each agent receives:
```json
{
  "working_directory": "/home/opsvi/agent_worktrees/agent_1_...",
  "agent_workspace": ".../agent_workspace/",
  "shared_messages": "/home/opsvi/agent_shared/messages/",
  "shared_outputs": "/home/opsvi/agent_shared/outputs/",
  "branch_name": "agent/requirements-analyst/20240115_120000",
  "isolation": "complete"
}
```

## Execution Patterns

### Pattern 1: Parallel Team Execution
```python
# Architecture team - 3 agents work simultaneously
async def execute_architecture_team():
    agents = [
        "solution-architect",
        "api-specialist",
        "database-specialist"
    ]

    # All 3 get worktrees and execute in parallel
    # No waiting, no conflicts, pure parallelism
```

### Pattern 2: Pipeline with Handoffs
```python
# Sequential phases, parallel within phase
async def execute_pipeline():
    # Phase 1: Requirements (2 agents parallel)
    await execute_team(["req-analyst", "biz-analyst"])

    # Phase 2: Architecture (3 agents parallel)
    await execute_team(["architect", "api", "database"])

    # Phase 3: Review (5 agents parallel)
    await execute_team(["security", "qa", "perf", "docs", "ops"])
```

### Pattern 3: Swarm Mode
```python
# All 15 agents attack problem simultaneously
async def execute_swarm(task):
    # Create 15 worktrees
    # Launch 15 agents
    # Let them self-organize via shared messages
    # Merge all successful contributions
```

## Safety Features

### Isolation Guarantees
- **No file conflicts**: Each agent has own filesystem
- **No git conflicts**: Separate branches per agent
- **No race conditions**: Worktrees eliminate contention
- **Clean rollback**: Delete worktree = undo agent work

### Failure Handling
```python
try:
    result = await execute_agent_in_worktree(agent, worktree)
    if result.success:
        worktree_manager.merge_agent_work(agent.id)
    else:
        worktree_manager.cleanup_worktree(agent.id, force=True)
        # Agent work completely discarded, no trace
except Exception:
    # Emergency cleanup
    worktree_manager.cleanup_all(force=True)
```

## Performance Benefits

### Without Worktrees (Sequential)
```
Agent 1: 30 seconds
Agent 2: 30 seconds (waits for Agent 1)
Agent 3: 30 seconds (waits for Agent 2)
...
Total: 15 × 30 = 450 seconds (7.5 minutes)
```

### With Worktrees (Parallel)
```
Agent 1: 30 seconds ──┐
Agent 2: 30 seconds ──┤
Agent 3: 30 seconds ──┼── All run simultaneously
...                   │
Agent 15: 30 seconds ─┘
Total: 30 seconds (15x speedup!)
```

## Configuration

### Enable/Disable Worktrees
```python
# Enabled by default
orchestrator = SafeOrchestrator(use_worktrees=True)

# Disable for single-agent testing
orchestrator = SafeOrchestrator(use_worktrees=False)
```

### Worktree Settings
```python
WORKTREE_CONFIG = {
    "base_path": "/home/opsvi/agent_worktrees",
    "shared_path": "/home/opsvi/agent_shared",
    "max_worktrees": 15,
    "auto_cleanup": True,
    "cleanup_on_merge": True,
    "preserve_failed": False  # Keep failed worktrees for debugging
}
```

## Migration Path

### Phase 1: Current State
- Single directory execution
- Sequential agent runs
- File conflicts possible

### Phase 2: Worktree Integration (NOW)
- WorktreeManager implemented
- SafeOrchestrator updated
- POC tests with 2 agents

### Phase 3: Full Adoption
- All agent executions use worktrees
- Parallel execution standard
- 15-agent swarm enabled

## Best Practices

### DO:
- ✅ Always use worktrees for multi-agent tasks
- ✅ Clean up worktrees after successful merge
- ✅ Use shared message space for coordination
- ✅ Commit frequently within worktrees
- ✅ Test with small agent groups first

### DON'T:
- ❌ Share files directly between worktrees
- ❌ Assume worktree = branch (worktree is workspace + branch)
- ❌ Leave stale worktrees (use cleanup)
- ❌ Bypass WorktreeManager for git operations

## Monitoring

### Worktree Dashboard
```python
def get_worktree_status():
    return {
        "active_worktrees": 8,
        "agents": {
            "agent_1": {"branch": "agent/req/...", "files": 5, "commits": 2},
            "agent_2": {"branch": "agent/biz/...", "files": 3, "commits": 1},
            # ...
        },
        "shared_messages": 47,
        "disk_usage": "2.4 GB",
        "performance": "15x parallelization active"
    }
```

## Conclusion

Worktrees are not just a feature - they are **the foundational technology** that enables:
- True 15-agent parallelization
- Safe experimentation
- Clean git history
- Conflict-free collaboration
- Instant rollback

Without worktrees, we have a sequential system pretending to be parallel.
With worktrees, we have a **true swarm intelligence platform**.
