# Agent Orchestrator API Reference

## Core Classes

### `GenericOrchestrator`

Main orchestration class that manages parallel execution of Claude agents.

```python
GenericOrchestrator(
    output_dir: Path,
    max_parallel: int = 10,
    tokens: List[str] = None,
    use_optimizations: bool = True
)
```

#### Parameters
- `output_dir` (Path): Directory for output files and logs
- `max_parallel` (int): Maximum agents to run in parallel
- `tokens` (List[str], optional): List of Claude API tokens
- `use_optimizations` (bool): Enable performance optimizations

#### Methods

##### `async execute_agent(task: AgentTask) -> Dict`
Execute a single agent task.

**Parameters:**
- `task` (AgentTask): Task to execute

**Returns:**
- Dict containing task results, status, and timing

**Example:**
```python
result = await orchestrator.execute_agent(task)
print(f"Status: {result['status']}")
print(f"Duration: {result['end_time'] - result['start_time']}s")
```

##### `async execute_batch(tasks: List[AgentTask]) -> List[Dict]`
Execute multiple tasks respecting dependencies and parallelism limits.

**Parameters:**
- `tasks` (List[AgentTask]): List of tasks to execute

**Returns:**
- List of result dictionaries

**Example:**
```python
tasks = [task1, task2, task3]
results = await orchestrator.execute_batch(tasks)
```

##### `async run(task_generator: Callable, result_processor: Optional[Callable]) -> Dict`
Main entry point for orchestration.

**Parameters:**
- `task_generator` (Callable): Function that returns list of AgentTask objects
- `result_processor` (Optional[Callable]): Function to process results

**Returns:**
- Dict with metrics and results

**Example:**
```python
def generate_tasks():
    return [AgentTask(...), AgentTask(...)]

def process_results(results):
    print(f"Processed {len(results)} results")

result = await orchestrator.run(
    task_generator=generate_tasks,
    result_processor=process_results
)
```

#### Hooks

##### `pre_execute_hook`
Called before each task execution.

```python
async def before_task(task: AgentTask):
    print(f"Starting {task.task_id}")

orchestrator.pre_execute_hook = before_task
```

##### `post_execute_hook`
Called after each task execution.

```python
async def after_task(task: AgentTask):
    if task.status == "completed":
        print(f"✓ {task.task_id}")

orchestrator.post_execute_hook = after_task
```

##### `task_builder_hook`
Customize prompt building for each task.

```python
async def build_prompt(task: AgentTask) -> str:
    return f"Custom prompt for {task.task_type}: {task.prompt}"

orchestrator.task_builder_hook = build_prompt
```

---

### `AgentTask`

Data class representing a single agent task.

```python
@dataclass
class AgentTask:
    task_id: str
    task_type: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
```

#### Fields
- `task_id` (str): Unique identifier for the task
- `task_type` (str): Type of task (e.g., "research", "code", "test")
- `prompt` (str): The prompt to send to Claude
- `context` (Dict): Additional context data
- `dependencies` (List[str]): List of task_ids this task depends on
- `status` (str): Current status ("pending", "running", "completed", "failed")
- `result` (Optional[Dict]): Task execution result
- `error` (Optional[str]): Error message if failed
- `start_time` (Optional[float]): Timestamp when task started
- `end_time` (Optional[float]): Timestamp when task ended

#### Methods

##### `to_dict() -> Dict`
Convert task to dictionary representation.

**Example:**
```python
task = AgentTask(
    task_id="analyze",
    task_type="analysis",
    prompt="Analyze the codebase"
)
task_dict = task.to_dict()
```

---

### `TokenPool`

Manages Claude API tokens for parallel execution.

```python
TokenPool(tokens: List[str] = None)
```

#### Parameters
- `tokens` (List[str], optional): List of API tokens. If None, uses CLAUDE_CODE_TOKEN env var

#### Methods

##### `async acquire() -> Tuple[str, int]`
Get next available token (round-robin).

**Returns:**
- Tuple of (token, token_index)

##### `size() -> int`
Get number of available tokens.

**Returns:**
- Number of tokens in pool

---

### `DependencyManager`

Manages task dependencies and execution order.

#### Methods

##### `async can_run(task: AgentTask) -> bool`
Check if task dependencies are satisfied.

##### `async mark_running(task_id: str)`
Mark task as currently running.

##### `async mark_completed(task_id: str)`
Mark task as completed successfully.

##### `async mark_failed(task_id: str)`
Mark task as failed.

---

### `MessageBus`

Simple file-based message passing between agents.

```python
MessageBus(message_dir: Path)
```

#### Methods

##### `async send(from_id: str, to_id: str, message: Dict)`
Send message from one agent to another.

##### `async receive(agent_id: str) -> List[Dict]`
Get all messages for an agent.

---

## Complete Example

```python
import asyncio
from pathlib import Path
from generic_orchestrator import GenericOrchestrator, AgentTask

async def main():
    # Create orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"),
        max_parallel=5,
        use_optimizations=True
    )

    # Define task generator
    def generate_tasks():
        return [
            # Independent tasks (will run in parallel)
            AgentTask(
                task_id="research_api",
                task_type="research",
                prompt="Research REST API best practices"
            ),
            AgentTask(
                task_id="research_db",
                task_type="research",
                prompt="Research database optimization techniques"
            ),

            # Dependent task (waits for research)
            AgentTask(
                task_id="design",
                task_type="design",
                prompt="Design a scalable web service",
                dependencies=["research_api", "research_db"]
            ),

            # Final implementation (waits for design)
            AgentTask(
                task_id="implement",
                task_type="code",
                prompt="Implement the designed service",
                dependencies=["design"]
            )
        ]

    # Process results
    async def process_results(results):
        successful = sum(1 for r in results if r['status'] == 'completed')
        print(f"\nCompleted {successful}/{len(results)} tasks")

        for result in results:
            if result['status'] == 'failed':
                print(f"Failed: {result['task_id']} - {result['error']}")

    # Run orchestration
    result = await orchestrator.run(
        task_generator=generate_tasks,
        result_processor=process_results
    )

    print(f"\nTotal duration: {result['metrics']['total_duration']:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

The orchestrator handles various error conditions:

1. **Missing Dependencies**: Tasks with unmet dependencies are marked as failed
2. **Token Exhaustion**: Waits for tokens to become available
3. **Claude CLI Errors**: Captures stderr and marks task as failed
4. **Timeout**: Can be configured per task (future enhancement)
5. **JSON Parsing**: Handles invalid JSON responses gracefully

## Performance Considerations

1. **Token Pool Size**: More tokens = more parallelism
2. **Max Parallel**: Balance between speed and resource usage
3. **Dependencies**: Minimize dependency chains for better parallelism
4. **Optimizations**: Use `use_optimizations=True` for faster execution

## Thread Safety

The orchestrator is designed to be thread-safe:
- Token pool uses asyncio locks
- Dependency manager uses locks for state changes
- Message bus uses atomic file operations
