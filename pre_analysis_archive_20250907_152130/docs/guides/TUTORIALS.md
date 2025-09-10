# Agent Orchestrator Tutorials

## Tutorial 1: Your First Orchestration

### Goal
Create a simple 3-task orchestration that researches a topic, analyzes findings, and creates a summary.

### Step 1: Setup Environment

```bash
# Install requirements
cd /home/opsvi/master_root/apps/agent-orchestrator
./setup.sh

# Set your token (if not already set)
export CLAUDE_CODE_TOKEN='your-token-here'
```

### Step 2: Create Your Script

Create `my_first_orchestration.py`:

```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.append('/home/opsvi/master_root/apps/agent-orchestrator/src')

from generic_orchestrator import GenericOrchestrator, AgentTask

async def my_first_orchestration():
    # Initialize orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./my_output"),
        max_parallel=3,
        use_optimizations=True
    )

    # Define your tasks
    def create_tasks():
        return [
            AgentTask(
                task_id="research",
                task_type="research",
                prompt="Research the history and benefits of Python programming language"
            ),
            AgentTask(
                task_id="analyze",
                task_type="analysis",
                prompt="Analyze the research findings and identify top 5 key points",
                dependencies=["research"]  # Waits for research to complete
            ),
            AgentTask(
                task_id="summary",
                task_type="documentation",
                prompt="Create a brief executive summary of the analysis",
                dependencies=["analyze"]  # Waits for analysis to complete
            )
        ]

    # Run the orchestration
    print("Starting orchestration...")
    result = await orchestrator.run(task_generator=create_tasks)

    print(f"\nCompleted! Check ./my_output/tasks/ for results")
    print(f"Total time: {result['metrics']['total_duration']:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(my_first_orchestration())
```

### Step 3: Run Your Orchestration

```bash
python3 my_first_orchestration.py
```

### Expected Output

```
Starting orchestration...
INFO: Generated 3 tasks
INFO: Executing research (research)
INFO: ✓ research completed in 45.23s
INFO: Executing analyze (analysis)
INFO: ✓ analyze completed in 38.91s
INFO: Executing summary (documentation)
INFO: ✓ summary completed in 22.14s

Completed! Check ./my_output/tasks/ for results
Total time: 106.28 seconds
```

---

## Tutorial 2: Parallel Execution

### Goal
Run multiple independent tasks in parallel, then combine results.

### The Code

```python
async def parallel_example():
    orchestrator = GenericOrchestrator(
        output_dir=Path("./parallel_output"),
        max_parallel=5  # Allow 5 parallel tasks
    )

    def create_parallel_tasks():
        tasks = []

        # Create 5 independent research tasks
        topics = [
            "artificial intelligence",
            "quantum computing",
            "blockchain technology",
            "renewable energy",
            "space exploration"
        ]

        for topic in topics:
            tasks.append(AgentTask(
                task_id=f"research_{topic.replace(' ', '_')}",
                task_type="research",
                prompt=f"Research current trends in {topic}"
            ))

        # Add a summary task that depends on ALL research
        tasks.append(AgentTask(
            task_id="combine_findings",
            task_type="synthesis",
            prompt="Combine all research findings into a technology trends report",
            dependencies=[f"research_{t.replace(' ', '_')}" for t in topics]
        ))

        return tasks

    result = await orchestrator.run(task_generator=create_parallel_tasks)
    print(f"Parallel execution saved approximately {estimate_time_saved(result)}s")
```

### Key Points
- Independent tasks run simultaneously
- Dependent tasks wait for ALL dependencies
- Parallelism limited by token count and max_parallel setting

---

## Tutorial 3: Using Context and Hooks

### Goal
Pass context between tasks and use hooks for custom behavior.

### The Code

```python
async def context_example():
    orchestrator = GenericOrchestrator(
        output_dir=Path("./context_output"),
        max_parallel=2
    )

    # Track shared context
    shared_context = {}

    # Define custom hooks
    async def save_context(task: AgentTask):
        """Save task results to shared context"""
        if task.status == "completed" and task.result:
            shared_context[task.task_id] = task.result
            print(f"📝 Saved context from {task.task_id}")

    async def inject_context(task: AgentTask) -> str:
        """Inject previous results into prompt"""
        base_prompt = task.prompt

        if task.dependencies and shared_context:
            context_info = "\n\nContext from previous tasks:\n"
            for dep in task.dependencies:
                if dep in shared_context:
                    context_info += f"- {dep}: Available\n"
            base_prompt = f"{base_prompt}{context_info}"

        return base_prompt

    # Set hooks
    orchestrator.post_execute_hook = save_context
    orchestrator.task_builder_hook = inject_context

    # Define tasks with context flow
    def create_contextual_tasks():
        return [
            AgentTask(
                task_id="gather_requirements",
                task_type="analysis",
                prompt="List 5 requirements for a task management system"
            ),
            AgentTask(
                task_id="design_database",
                task_type="design",
                prompt="Design a database schema based on the requirements",
                dependencies=["gather_requirements"],
                context={"needs_schema": True}
            ),
            AgentTask(
                task_id="design_api",
                task_type="design",
                prompt="Design REST API endpoints based on the requirements",
                dependencies=["gather_requirements"],
                context={"needs_endpoints": True}
            ),
            AgentTask(
                task_id="create_implementation_plan",
                task_type="planning",
                prompt="Create implementation plan combining database and API designs",
                dependencies=["design_database", "design_api"]
            )
        ]

    await orchestrator.run(task_generator=create_contextual_tasks)
```

---

## Tutorial 4: Error Handling and Recovery

### Goal
Handle failures gracefully and implement retry logic.

### The Code

```python
async def error_handling_example():
    orchestrator = GenericOrchestrator(
        output_dir=Path("./error_output"),
        max_parallel=3
    )

    # Track failures for retry
    failed_tasks = []
    retry_count = {}

    async def handle_failures(task: AgentTask):
        """Track and potentially retry failed tasks"""
        if task.status == "failed":
            task_key = task.task_id
            retry_count[task_key] = retry_count.get(task_key, 0) + 1

            if retry_count[task_key] <= 3:  # Max 3 retries
                print(f"⚠️ Task {task_key} failed, will retry ({retry_count[task_key]}/3)")
                failed_tasks.append(task)
            else:
                print(f"❌ Task {task_key} failed after 3 retries")

    orchestrator.post_execute_hook = handle_failures

    # Run main tasks
    def create_tasks():
        return [
            AgentTask(
                task_id="risky_task_1",
                task_type="processing",
                prompt="Process complex data that might fail"
            ),
            AgentTask(
                task_id="dependent_task",
                task_type="analysis",
                prompt="Analyze the processed data",
                dependencies=["risky_task_1"]
            )
        ]

    # Run with retry logic
    result = await orchestrator.run(task_generator=create_tasks)

    # Retry failed tasks
    while failed_tasks and any(retry_count.get(t.task_id, 0) <= 3 for t in failed_tasks):
        print(f"\nRetrying {len(failed_tasks)} failed tasks...")
        retry_tasks = failed_tasks.copy()
        failed_tasks.clear()

        # Reset status for retry
        for task in retry_tasks:
            task.status = "pending"
            task.error = None

        await orchestrator.execute_batch(retry_tasks)

    print(f"\nFinal status: {result['metrics']['completed']} completed, {result['metrics']['failed']} failed")
```

---

## Tutorial 5: Building a Complex Pipeline

### Goal
Create a multi-stage pipeline for a complete software development workflow.

### The Code

```python
async def development_pipeline():
    orchestrator = GenericOrchestrator(
        output_dir=Path("./pipeline_output"),
        max_parallel=4
    )

    def create_pipeline():
        return [
            # Stage 1: Requirements
            AgentTask(
                task_id="requirements",
                task_type="analysis",
                prompt="Define requirements for a weather notification service"
            ),

            # Stage 2: Design (parallel)
            AgentTask(
                task_id="system_design",
                task_type="architecture",
                prompt="Create system architecture for the weather service",
                dependencies=["requirements"]
            ),
            AgentTask(
                task_id="api_design",
                task_type="design",
                prompt="Design REST API for weather notifications",
                dependencies=["requirements"]
            ),
            AgentTask(
                task_id="database_design",
                task_type="design",
                prompt="Design database schema for weather data",
                dependencies=["requirements"]
            ),

            # Stage 3: Implementation planning
            AgentTask(
                task_id="implementation_plan",
                task_type="planning",
                prompt="Create detailed implementation plan",
                dependencies=["system_design", "api_design", "database_design"]
            ),

            # Stage 4: Code generation (parallel)
            AgentTask(
                task_id="backend_code",
                task_type="code",
                prompt="Generate Python Flask backend code",
                dependencies=["implementation_plan"]
            ),
            AgentTask(
                task_id="database_code",
                task_type="code",
                prompt="Generate SQL database setup scripts",
                dependencies=["implementation_plan"]
            ),
            AgentTask(
                task_id="frontend_code",
                task_type="code",
                prompt="Generate React frontend components",
                dependencies=["implementation_plan"]
            ),

            # Stage 5: Testing
            AgentTask(
                task_id="test_plan",
                task_type="testing",
                prompt="Create comprehensive test plan",
                dependencies=["backend_code", "database_code", "frontend_code"]
            ),
            AgentTask(
                task_id="test_code",
                task_type="code",
                prompt="Generate pytest test cases",
                dependencies=["test_plan"]
            ),

            # Stage 6: Documentation
            AgentTask(
                task_id="documentation",
                task_type="documentation",
                prompt="Create complete project documentation",
                dependencies=["test_code"]
            )
        ]

    # Add progress tracking
    async def track_progress(task: AgentTask):
        if task.status == "completed":
            print(f"✓ Completed: {task.task_id}")
        elif task.status == "running":
            print(f"⚡ Running: {task.task_id}")

    orchestrator.post_execute_hook = track_progress

    print("Starting development pipeline...")
    result = await orchestrator.run(task_generator=create_pipeline)

    print(f"\nPipeline complete!")
    print(f"Generated {result['metrics']['completed']} artifacts")
    print(f"Total time: {result['metrics']['total_duration']:.2f}s")
```

---

## Best Practices

### 1. Task Naming
Use descriptive, unique task IDs:
```python
# Good
task_id="validate_user_input"
task_id="fetch_weather_data_api"

# Bad
task_id="task1"
task_id="step2"
```

### 2. Dependency Management
Keep dependency chains shallow when possible:
```python
# Better (parallel where possible)
A → [B, C, D] → E

# Worse (long sequential chain)
A → B → C → D → E
```

### 3. Error Handling
Always plan for failures:
```python
# Add timeout and retry logic
task = AgentTask(
    task_id="critical_task",
    context={
        "timeout": 300,  # 5 minutes
        "retries": 3,
        "critical": True
    }
)
```

### 4. Resource Management
Balance parallelism with available resources:
```python
# Consider your token count
if token_count == 1:
    max_parallel = 1  # Sequential only
elif token_count < 5:
    max_parallel = token_count
else:
    max_parallel = 5  # Reasonable limit
```

### 5. Output Organization
Structure output for easy access:
```python
orchestrator = GenericOrchestrator(
    output_dir=Path(f"./output/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
)
```

---

## Advanced Patterns

### Pattern 1: Map-Reduce
```python
# Map phase: Process items in parallel
map_tasks = [
    AgentTask(task_id=f"process_{i}", task_type="map", prompt=f"Process item {i}")
    for i in range(10)
]

# Reduce phase: Combine results
reduce_task = AgentTask(
    task_id="combine_results",
    task_type="reduce",
    prompt="Combine all processed items",
    dependencies=[t.task_id for t in map_tasks]
)
```

### Pattern 2: Pipeline with Branching
```python
# Main path with conditional branches
tasks = [
    AgentTask(task_id="analyze", task_type="analysis", prompt="Analyze input"),
    AgentTask(task_id="classify", task_type="classification", prompt="Classify type",
              dependencies=["analyze"]),
    # Branch based on classification
    AgentTask(task_id="process_type_a", task_type="processing",
              prompt="Process as type A", dependencies=["classify"]),
    AgentTask(task_id="process_type_b", task_type="processing",
              prompt="Process as type B", dependencies=["classify"]),
]
```

### Pattern 3: Recursive Decomposition
```python
def create_recursive_tasks(depth=0, max_depth=3, parent=None):
    tasks = []
    task_id = f"level_{depth}_{uuid.uuid4().hex[:8]}"

    task = AgentTask(
        task_id=task_id,
        task_type="decompose",
        prompt=f"Decompose problem at level {depth}",
        dependencies=[parent] if parent else []
    )
    tasks.append(task)

    if depth < max_depth:
        # Create child tasks
        for i in range(2):  # Binary tree
            tasks.extend(create_recursive_tasks(depth+1, max_depth, task_id))

    return tasks
```

## Next Steps

1. Review the [API Reference](API_REFERENCE.md) for detailed method documentation
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
3. Explore example scripts in the `examples/` directory
4. Join the community and share your orchestrations!
