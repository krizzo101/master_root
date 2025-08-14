# V1 Enhancement: True Parallel Recursive Multi-Agent Execution

## Current State Analysis

### What V1 Currently Does:
1. **Recursive Spawning**: ✅ Claude can spawn children via `claude_run_async(parentJobId=...)`
2. **Depth Tracking**: ✅ Tracks recursion depth (0→1→2→3)
3. **Parent-Child Relationships**: ✅ Maintains job genealogy
4. **Async Execution**: ✅ Returns job IDs immediately

### The Critical Limitation:
**Children can only spawn ONE grandchild at a time** because Claude instances call tools sequentially:
```python
# Current behavior in Claude:
job1 = await claude_run_async(task="Subtask 1", parentJobId=my_id)
job2 = await claude_run_async(task="Subtask 2", parentJobId=my_id)  # Waits for job1 to return
job3 = await claude_run_async(task="Subtask 3", parentJobId=my_id)  # Waits for job2 to return
```

## Required Changes for True Parallel Recursive Execution

### 1. **New Batch Spawning Tool** (Critical Change)

Add a new tool to V1 server that spawns multiple children in ONE call:

```python
@mcp.tool()
async def claude_run_batch_async(
    tasks: List[str],
    parentJobId: Optional[str] = None,
    outputFormat: str = "json",
    permissionMode: str = "bypassPermissions",
) -> str:
    """
    Spawn multiple Claude instances simultaneously.
    Returns all job IDs immediately.
    """
    job_ids = []
    
    # Create all jobs first (fast)
    for task in tasks:
        job = job_manager.create_job(
            task=task,
            parent_job_id=parentJobId,
            output_format=outputFormat,
            permission_mode=permissionMode
        )
        job_ids.append(job.id)
    
    # Launch all executions in parallel (using asyncio.gather)
    await asyncio.gather(*[
        job_manager.execute_job_async(job) 
        for job in jobs
    ])
    
    return json.dumps({
        "jobIds": job_ids,
        "count": len(job_ids),
        "status": "all_started"
    })
```

### 2. **Batch Result Collection Tool**

Add a tool to collect multiple results efficiently:

```python
@mcp.tool()
async def claude_results_batch(
    jobIds: List[str],
    wait: bool = True,
    timeout: int = 300
) -> str:
    """
    Get results for multiple jobs.
    Can wait for completion or return current status.
    """
    if wait:
        # Wait for all jobs to complete (with timeout)
        results = await job_manager.wait_for_jobs(jobIds, timeout)
    else:
        # Return current status immediately
        results = job_manager.get_jobs_status(jobIds)
    
    return json.dumps(results)
```

### 3. **Enhanced Recursion Manager**

Update recursion limits to handle parallel branching:

```python
class RecursionConfig:
    max_depth: int = 5  # Increase from 3
    max_concurrent_at_depth: Dict[int, int] = {
        0: 1,    # Root level - 1 instance
        1: 10,   # First level - 10 parallel children
        2: 50,   # Second level - 50 total grandchildren
        3: 100,  # Third level - 100 great-grandchildren
        4: 200,  # Fourth level - 200 max
        5: 400   # Fifth level - 400 max
    }
    max_total_jobs: int = 1000  # Increase from 30
    max_children_per_parent: int = 20  # New limit
```

### 4. **Parallel-Aware Job Manager**

Modify job execution to handle parallel children:

```python
async def execute_job_async(self, job: ClaudeJob) -> None:
    """Execute with parallel child awareness"""
    
    # Track active children for this parent
    if job.parent_job_id:
        self.increment_parent_children(job.parent_job_id)
    
    # Configure MCP to include V1 server for recursion
    mcp_config = self.create_mcp_config(
        job_id=job.id,
        include_v1_server=True,  # Critical: Child needs V1 tools
        parent_job_id=job.parent_job_id
    )
    
    # Launch Claude with recursive capabilities
    process = await self.spawn_claude_process(
        task=job.task,
        mcp_config=mcp_config,
        env={
            "CLAUDE_PARENT_JOB_ID": job.parent_job_id or "",
            "CLAUDE_RECURSION_DEPTH": str(job.recursion_context.depth),
            "CLAUDE_MAX_CHILDREN": str(self.get_remaining_children_quota(job.id))
        }
    )
```

### 5. **Smart MCP Configuration**

Ensure each Claude instance has access to V1 tools:

```python
def create_recursive_mcp_config(job_id: str, depth: int) -> dict:
    """Create MCP config that includes V1 server for recursion"""
    return {
        "claude-code": {  # V1 server MUST be included
            "command": "python",
            "args": ["-m", "opsvi_mcp.servers.claude_code"],
            "env": {
                "CLAUDE_CODE_TOKEN": os.environ.get("CLAUDE_CODE_TOKEN"),
                "PYTHONPATH": "/home/opsvi/master_root/libs",
                "CLAUDE_RECURSION_ENABLED": "true",
                "CLAUDE_CURRENT_DEPTH": str(depth)
            }
        },
        # Include other necessary MCP servers based on task
    }
```

## Implementation Architecture

### The Tree Structure:
```
Root Claude (depth 0)
├── Calls: claude_run_batch_async(["Task A", "Task B", "Task C"])
├── Child A (depth 1) - Spawned simultaneously
│   ├── Calls: claude_run_batch_async(["A1", "A2", "A3"])
│   ├── Grandchild A1 (depth 2) - Spawned simultaneously
│   ├── Grandchild A2 (depth 2) - Spawned simultaneously
│   └── Grandchild A3 (depth 2) - Spawned simultaneously
├── Child B (depth 1) - Spawned simultaneously
│   └── Calls: claude_run_batch_async(["B1", "B2"])
│       ├── Grandchild B1 (depth 2) - Spawned simultaneously
│       └── Grandchild B2 (depth 2) - Spawned simultaneously
└── Child C (depth 1) - Spawned simultaneously
    └── Can spawn its own children in parallel
```

### Execution Timeline:
```
T=0:   Root starts
T=1:   Root spawns 3 children simultaneously
T=2:   All 3 children start executing
T=3:   Child A spawns 3 grandchildren simultaneously
T=3.5: Child B spawns 2 grandchildren simultaneously
T=4:   5 grandchildren executing in parallel
T=5:   Grandchildren can spawn great-grandchildren
...
T=N:   Results bubble up through collection tools
```

## Critical Requirements

### 1. **Every Claude Instance Needs V1 Tools**
Each spawned Claude MUST have access to:
- `claude_run_async` (for single child)
- `claude_run_batch_async` (for multiple children)
- `claude_results_batch` (for collecting child results)

### 2. **Resource Management**
```python
# Prevent fork bombs
if depth >= MAX_DEPTH:
    disable_spawning_tools()

if total_jobs >= MAX_TOTAL:
    reject_new_spawns()

if children_count >= MAX_PER_PARENT:
    throttle_spawning()
```

### 3. **Result Aggregation**
Parents need to collect and synthesize child results:
```python
# In Claude's execution
children = await claude_run_batch_async([...])
# Do other work while children run
results = await claude_results_batch(children["jobIds"], wait=True)
synthesized = analyze_and_combine(results)
```

## Benefits of This Architecture

1. **Exponential Parallelism**: 
   - 1 → 10 → 100 → 1000 instances in just 3 levels
   - Massive parallel processing power

2. **Natural Task Decomposition**:
   - Claude decides how to break down problems
   - Each level can adapt its decomposition strategy

3. **Fault Tolerance**:
   - Failed children don't block siblings
   - Parents can retry or compensate

4. **Emergent Intelligence**:
   - Complex behaviors emerge from simple recursive rules
   - Self-organizing problem-solving trees

## Implementation Priority

### Phase 1: Core Tools (Required)
1. ✅ Add `claude_run_batch_async` tool
2. ✅ Add `claude_results_batch` tool
3. ✅ Update recursion limits

### Phase 2: Resource Management
1. ✅ Implement fork bomb prevention
2. ✅ Add job quotas per parent
3. ✅ Add depth-based throttling

### Phase 3: Optimization
1. ✅ Smart MCP server selection
2. ✅ Result caching
3. ✅ Partial result collection

## Example Usage

When Claude receives a complex task:

```python
# Claude's internal logic (automated, not user code)
async def handle_complex_task(task):
    # Decompose into subtasks
    subtasks = analyze_and_decompose(task)
    
    # Spawn all subtasks in parallel
    result = await claude_run_batch_async(
        tasks=subtasks,
        parentJobId=current_job_id
    )
    
    # Continue with other work while children run
    local_work = do_local_processing()
    
    # Collect results when needed
    child_results = await claude_results_batch(
        jobIds=result["jobIds"],
        wait=True
    )
    
    # Synthesize everything
    return combine_results(local_work, child_results)
```

## The Key Insight

**The critical change**: Moving from sequential `claude_run_async` calls to batch `claude_run_batch_async` enables true parallel recursive execution. Each Claude instance becomes a node that can spawn multiple children simultaneously, and those children can do the same, creating an exponentially growing tree of parallel execution.

This transforms V1 from "recursive but sequential" to "recursive AND parallel" - achieving what V3 claimed but failed to deliver.