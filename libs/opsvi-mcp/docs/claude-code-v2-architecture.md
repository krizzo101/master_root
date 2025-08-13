# Claude Code V2: Hybrid Decoupling Architecture

## Overview

Claude Code V2 implements a **hybrid decoupling pattern** that solves the tool_result protocol violation issue while maintaining proper parent-child responsibility chains.

## Key Design Principles

### 1. First-Level Decoupling Only
- **Parent → L1 Agents**: Fire-and-forget (decoupled)
- **L1 → L2 Agents**: Synchronous management (coupled)
- **L2 → L3 Agents**: Synchronous management (coupled)

### 2. Responsibility Hierarchy
```
Parent Agent (You)
    ├── L1 Agent A [DECOUPLED - Fire & Forget]
    │   ├── L2 Agent A.1 [MANAGED by A]
    │   └── L2 Agent A.2 [MANAGED by A]
    │       └── L3 Agent A.2.1 [MANAGED by A.2]
    │
    ├── L1 Agent B [DECOUPLED - Fire & Forget]
    │   └── L2 Agent B.1 [MANAGED by B]
    │
    └── L1 Agent C [DECOUPLED - Fire & Forget]
```

## Why This Architecture?

### Problem Solved
The original error occurred because:
```
Parent → spawn_async(A) → tool_use_id_123
Parent → spawn_async(B) → tool_use_id_456  
Parent → spawn_async(C) → tool_use_id_789
Parent → [Tries to continue without results] → ERROR!
```

### Solution Applied
```
Parent → spawn_agent(A) → Returns immediately {"job_id": "A", "result_location": "/tmp/A.json"}
Parent → spawn_agent(B) → Returns immediately {"job_id": "B", "result_location": "/tmp/B.json"}
Parent → spawn_agent(C) → Returns immediately {"job_id": "C", "result_location": "/tmp/C.json"}
Parent → [Can continue working] → collect_results() when ready
```

## How It Works

### 1. Spawning First-Level Agents

```python
# Parent agent spawns L1 agents
result = await spawn_parallel_agents(
    tasks=[
        "Analyze the codebase architecture",
        "Review security vulnerabilities", 
        "Generate comprehensive documentation"
    ],
    agent_profile="research",
    output_dir="/tmp/analysis_results"
)

# Returns immediately:
{
    "success": true,
    "total_spawned": 3,
    "jobs": [
        {"job_id": "uuid-1", "result_location": "/tmp/analysis_results/uuid-1.json"},
        {"job_id": "uuid-2", "result_location": "/tmp/analysis_results/uuid-2.json"},
        {"job_id": "uuid-3", "result_location": "/tmp/analysis_results/uuid-3.json"}
    ]
}
```

### 2. L1 Agent Managing Children

Each L1 agent is **fully responsible** for its children:

```python
# Inside L1 Agent A
async def execute_task():
    # L1 agent analyzes task complexity
    if task_requires_decomposition:
        # Spawn L2 children SYNCHRONOUSLY
        child1_result = await spawn_child("Analyze subsystem 1", depth=1)
        child2_result = await spawn_child("Analyze subsystem 2", depth=1)
        
        # Wait for all children to complete
        all_children_complete = await wait_for_children()
        
        # Synthesize results
        final_result = synthesize(child1_result, child2_result)
    
    # Write complete result (including all children)
    write_result({
        "job_id": "A",
        "status": "completed",
        "output": final_result,
        "children": {
            "child1": child1_result,
            "child2": child2_result
        }
    })
```

### 3. Parent Collecting Results

The parent can check results at any time without blocking:

```python
# Parent checks results when convenient
results = await collect_results(
    output_dir="/tmp/analysis_results",
    include_partial=True
)

# Returns current state:
{
    "completed": 2,  # A and B done
    "pending": 1,    # C still running
    "results": {
        "uuid-1": {
            "status": "completed",
            "output": {...},
            "children": {  # L1 Agent A managed these
                "child1": {...},
                "child2": {...}
            }
        },
        "uuid-2": {
            "status": "completed",
            "output": {...},
            "children": {}  # L1 Agent B had no children
        }
    }
}
```

## Benefits

### 1. Protocol Compliance
- Every `tool_use` gets immediate `tool_result`
- No hanging tool calls
- Clean API interaction

### 2. Failure Isolation
- If L1 Agent A crashes, Agents B and C continue
- Parent isn't affected by child failures
- Each L1 agent handles its own error recovery

### 3. Resource Management
- Parent doesn't hold resources for child execution
- Can spawn many L1 agents without blocking
- Memory/CPU distributed across processes

### 4. Clear Responsibility
- Each L1 agent owns its complete subtree
- Results include full recursive execution
- No orphaned sub-agents

## Usage Patterns

### Pattern 1: Parallel Analysis
```python
# Spawn multiple independent analyses
await spawn_parallel_agents([
    "Analyze project A",
    "Analyze project B",
    "Analyze project C"
])

# Continue with other work...
do_other_tasks()

# Collect when ready
results = await collect_results()
```

### Pattern 2: Progressive Collection
```python
# Spawn long-running tasks
jobs = await spawn_parallel_agents(complex_tasks)

# Check periodically
while True:
    results = await collect_results(include_partial=True)
    
    if results["completed"] == len(jobs):
        break
        
    # Process completed results incrementally
    process_available(results["completed"])
    
    await asyncio.sleep(30)
```

### Pattern 3: Aggregated Insights
```python
# Spawn specialized agents
await spawn_parallel_agents([
    "Security analysis",
    "Performance analysis",
    "Code quality analysis"
])

# Wait and aggregate
await asyncio.sleep(60)
results = await aggregate_results(aggregation_type="consensus")
```

## Configuration

### Environment Variables
```bash
# Core settings
export CLAUDE_CODE_TOKEN="your-token"
export CLAUDE_RESULTS_DIR="/tmp/claude_results"

# Limits
export CLAUDE_MAX_CONCURRENT_L1=10  # Max first-level agents
export CLAUDE_MAX_RECURSION=3       # Max depth for each L1 agent
export CLAUDE_DEFAULT_TIMEOUT=600   # Timeout per agent

# Child management
export CLAUDE_ENABLE_CHILDREN=true  # L1 agents can spawn children
export CLAUDE_CHILD_TIMEOUT_RATIO=0.5  # Children get 50% of parent timeout
```

## Error Handling

### L1 Agent Failure
```json
{
    "job_id": "failed-agent",
    "status": "failed",
    "error": "Connection timeout",
    "children": {
        "child1": {"status": "completed"},  // Some children may have completed
        "child2": {"status": "cancelled"}    // Others cancelled on parent failure
    }
}
```

### Graceful Degradation
- Parent continues despite L1 failures
- Partial results are preserved
- Can retry failed agents individually

## Migration Guide

### From Original Claude Code
```python
# OLD - Coupled, blocking
result = await claude_run(task)  # Blocks until complete

# NEW - Decoupled, non-blocking  
job = await spawn_agent(task)  # Returns immediately
# ... do other work ...
result = await collect_results([job["job_id"]])
```

### From Async Pattern
```python
# OLD - Still coupled via tool protocol
job = await claude_run_async(task)
status = await claude_status(job["job_id"])  # Still maintaining connection

# NEW - Fully decoupled
job = await spawn_agent(task)  # Fire and forget
# Parent can even terminate and results will still be written
```

## Best Practices

1. **Use for Complex Multi-Agent Tasks**: Best suited for tasks requiring multiple parallel analyses
2. **Set Appropriate Timeouts**: L1 agents should have enough time for their entire subtree
3. **Monitor Resource Usage**: Each L1 agent is a separate process
4. **Implement Result Validation**: Check that all expected agents completed
5. **Use Agent Profiles**: Standardize agent behavior and reporting
6. **Clean Up Old Results**: Implement periodic cleanup of result directory

## Summary

The hybrid decoupling pattern provides:
- **Reliability**: No more protocol violations
- **Scalability**: Spawn many agents without blocking
- **Responsibility**: Each agent manages its children
- **Resilience**: Failures are isolated
- **Flexibility**: Collect results when convenient

This architecture enables massive parallel agent execution while maintaining clean parent-child relationships and preventing the cascade failures that caused the original error.