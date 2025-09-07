# Agent Orchestrator Usage Guide

## 🚨 CRITICAL: THE PURPOSE IS MULTI-AGENT COORDINATION

**THE ORCHESTRATOR EXISTS FOR COORDINATING MULTIPLE SPECIALIZED AGENTS - NOT SINGLE-AGENT WORKFLOWS**

## MANDATORY FOR ALL AGENTS

**Effective immediately: All agents MUST use the orchestrator for MULTI-AGENT coordination**

### ❌ WRONG WAY (What Agent 1 has been doing):
```python
# DON'T DO THIS - Single agent doing everything
task = AgentTask("do_everything", "research", "Do all my work")
results = await orchestrator.execute_batch([task])  # WRONG!
```

### ✅ CORRECT WAY (Multi-agent coordination):
```python
# DO THIS - Break work into specialized agent tasks
tasks = [
    AgentTask("research", "research-genius", "Research the problem domain"),
    AgentTask("design", "solution-architect", "Design solution based on research", dependencies=["research"]),
    AgentTask("implement", "development-specialist", "Implement the design", dependencies=["design"]),
    AgentTask("test", "qa-testing-guru", "Test the implementation", dependencies=["implement"]),
    AgentTask("document", "technical-writer", "Document the solution", dependencies=["implement"])
]
results = await orchestrator.execute_batch(tasks)  # CORRECT!
```

The orchestrator is **VALIDATED WORKING** (10/10 tests passed) and provides:
- **Multi-agent parallel execution** with dependency management
- **Specialized agent coordination** (research, development, testing, etc.)
- **STRICT token pool management** (requires 2+ tokens, NO FALLBACKS)
- File-based message bus for inter-agent communication
- Comprehensive logging and monitoring

## 🚨 CRITICAL: TOKEN POOL REQUIREMENTS

**ORCHESTRATOR FAILS HARD IF INSUFFICIENT TOKENS:**
- **Requires 2+ Claude tokens** for multi-agent coordination
- **NO FALLBACKS** to single-token operation
- **FAILS IMMEDIATELY** if token pool can't support parallel agents
- **This is intentional** - prevents silent degradation to single-agent execution

## Quick Start

```python
from src.generic_orchestrator import GenericOrchestrator, AgentTask
from pathlib import Path

# 1. Initialize orchestrator
orchestrator = GenericOrchestrator(
    output_dir=Path("./output"),
    max_parallel=3  # Max concurrent tasks
)

# 2. Create tasks
task1 = AgentTask(
    task_id="research_phase",
    task_type="research",
    prompt="Research the current state of X"
)

task2 = AgentTask(
    task_id="implementation_phase",
    task_type="development-specialist",
    prompt="Implement Y based on research findings",
    dependencies=["research_phase"]  # Wait for task1
)

# 3. Execute tasks
results = await orchestrator.execute_batch([task1, task2])
```

## Task Types Available

Use these validated agent types for `task_type`:
- `research` - Research and analysis tasks
- `development-specialist` - Code implementation
- `qa-testing-guru` - Testing and validation
- `technical-writer` - Documentation
- `database-specialist` - Database operations
- `security-architect` - Security analysis
- `performance-optimizer` - Performance optimization

## Key Features Validated

### ✅ Parallel Execution
```python
# Tasks without dependencies run in parallel
tasks = [
    AgentTask("task1", "research", "Research A"),
    AgentTask("task2", "research", "Research B"),
    AgentTask("task3", "research", "Research C")
]
results = await orchestrator.execute_batch(tasks)
```

### ✅ Dependency Management
```python
# Tasks with dependencies wait for completion
task_a = AgentTask("analyze", "research", "Analyze system")
task_b = AgentTask("design", "development-specialist", "Design solution",
                   dependencies=["analyze"])
task_c = AgentTask("implement", "development-specialist", "Implement design",
                   dependencies=["design"])
```

### ✅ Token Pool (Automatic)
- Automatically manages Claude Code tokens
- Round-robin allocation prevents conflicts
- Secure token loading from environment

### ✅ Message Bus
```python
from src.generic_orchestrator import MessageBus

message_bus = MessageBus(Path("./messages"))
await message_bus.send("agent_a", "agent_b", {"type": "status", "data": "complete"})
messages = await message_bus.receive("agent_b")
```

## Directory Structure Created

```
output/
├── tasks/           # Individual task results
├── logs/           # Execution logs
├── messages/       # Inter-agent messages
└── monitoring/     # System metrics
```

## Error Handling

The orchestrator handles:
- Task failures (logged, other tasks continue)
- Dependency cycles (validation prevents)
- Token exhaustion (fallback mechanisms)
- File system errors (graceful degradation)

## 🔥 MANDATORY TASK BREAKDOWN REQUIREMENTS

**AGENTS MUST BREAK ALL WORK INTO MINIMUM 3+ SPECIALIZED TASKS:**

- **Research tasks** → `research-genius` agent type
- **Design/Architecture** → `solution-architect` agent type
- **Implementation** → `development-specialist` agent type
- **Testing/Validation** → `qa-testing-guru` agent type
- **Documentation** → `technical-writer` agent type

**❌ BANNED:** Single-task workflows (what Agent 1 keeps doing)
**✅ REQUIRED:** Multi-task, multi-agent coordination workflows

## Mandatory Agent Integration

**ALL AGENTS MUST:**

1. **Import the orchestrator:**
   ```python
   from src.generic_orchestrator import GenericOrchestrator, AgentTask
   ```

2. **Use orchestrator for multi-step work:**
   ```python
   # Instead of doing steps manually
   orchestrator = GenericOrchestrator(output_dir=Path("./my_work"))

   tasks = [
       AgentTask("step1", "research", "Do research"),
       AgentTask("step2", "development-specialist", "Implement", dependencies=["step1"]),
       AgentTask("step3", "qa-testing-guru", "Test implementation", dependencies=["step2"])
   ]

   results = await orchestrator.execute_batch(tasks)
   ```

3. **Test your orchestrator usage:**
   ```bash
   # Run the validation tests
   cd /home/opsvi/master_root/apps/agent-orchestrator
   python basic_functionality_tests.py
   ```

4. **Document orchestrator usage in your deliverables:**
   - Show how you used the orchestrator
   - Include task definitions and results
   - Provide examples others can run

## Example: Complete Agent Workflow

```python
import asyncio
from pathlib import Path
from src.generic_orchestrator import GenericOrchestrator, AgentTask

async def agent_workflow():
    # Initialize with your work directory
    orchestrator = GenericOrchestrator(
        output_dir=Path("./agent_work_output"),
        max_parallel=2
    )

    # Define your work as coordinated tasks
    tasks = [
        AgentTask(
            task_id="analyze_requirements",
            task_type="research",
            prompt="Analyze the requirements for X"
        ),
        AgentTask(
            task_id="design_solution",
            task_type="development-specialist",
            prompt="Design a solution based on requirements analysis",
            dependencies=["analyze_requirements"]
        ),
        AgentTask(
            task_id="implement_solution",
            task_type="development-specialist",
            prompt="Implement the designed solution",
            dependencies=["design_solution"]
        ),
        AgentTask(
            task_id="test_solution",
            task_type="qa-testing-guru",
            prompt="Test the implemented solution thoroughly",
            dependencies=["implement_solution"]
        )
    ]

    # Execute with orchestration
    results = await orchestrator.execute_batch(tasks)

    # Report results
    for result in results:
        print(f"Task {result['task_id']}: {result['status']}")

    return results

# Run your coordinated workflow
if __name__ == "__main__":
    results = asyncio.run(agent_workflow())
```

## Validation Required

Before claiming any work complete, you MUST:

1. **Test orchestrator integration:** Your code should run without errors
2. **Provide working examples:** Include runnable code that uses orchestrator
3. **Document task definitions:** Show exact AgentTask configurations used
4. **Include result validation:** Prove your orchestrated tasks succeeded

## Support

- **Test file:** `basic_functionality_tests.py` (10/10 tests pass)
- **Core module:** `src/generic_orchestrator.py`
- **Working directory:** `/home/opsvi/master_root/apps/agent-orchestrator`

---

**COORDINATION REQUIREMENT:** All agents must transition to orchestrated task execution immediately. No more manual step-by-step work without orchestration.
