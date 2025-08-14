# Claude Code MCP Servers - Tools Comparison & Usage Guide

## Overview

Each Claude Code server version offers different tools optimized for specific use cases:

- **V1 (claude-code-wrapper)**: 8 tools - Traditional job management with synchronous and async execution
- **V2 (claude-code-v2)**: 6 tools - Fire-and-forget pattern for parallel agent spawning
- **V3 (claude-code-v3)**: 2 tools - Intelligent mode-based execution with multi-agent orchestration

## Tool Inventory by Server

### Claude Code V1 (claude-code-wrapper) - 8 Tools

| Tool | Purpose | Key Parameters | Return Type |
|------|---------|----------------|-------------|
| `claude_run` | Synchronous task execution | `task`, `cwd`, `outputFormat`, `permissionMode` | JSON/Text result |
| `claude_run_async` | Asynchronous task execution | `task`, `cwd`, `outputFormat`, `permissionMode`, `parentJobId` | Job ID |
| `claude_status` | Check job status | `jobId` | Status info |
| `claude_result` | Get completed job result | `jobId` | Execution result |
| `claude_list_jobs` | List all jobs | None | Job list |
| `claude_kill_job` | Terminate running job | `jobId` | Success status |
| `claude_dashboard` | System performance metrics | None | Dashboard data |
| `claude_recursion_stats` | Recursion statistics | None | Stats & limits |

### Claude Code V2 (claude-code-v2) - 6 Tools  

| Tool | Purpose | Key Parameters | Return Type |
|------|---------|----------------|-------------|
| `spawn_agent` | Fire-and-forget agent spawning | `task`, `agent_profile`, `output_dir`, `timeout`, `metadata` | Job info with ID |
| `spawn_parallel_agents` | Spawn multiple agents | `tasks[]`, `agent_profile`, `output_dir`, `timeout` | Jobs info with IDs |
| `collect_results` | Gather agent results | `job_ids[]`, `output_dir`, `include_partial`, `cleanup` | Results dict |
| `check_agent_health` | Health status check | `job_id` (optional) | Health info |
| `kill_agent` | Terminate agent | `job_id`, `cleanup` | Success status |
| `aggregate_results` | Combine multiple results | `output_dir`, `aggregation_type` | Aggregated data |

### Claude Code V3 (claude-code-v3) - 2 Tools

| Tool | Purpose | Key Parameters | Return Type |
|------|---------|----------------|-------------|
| `claude_run_v3` | Intelligent multi-mode execution | `task`, `mode`, `auto_detect`, `quality_level` | Execution plan |
| `get_v3_status` | Server capabilities status | None | Config & features |

## Detailed Tool Usage

### V1: Traditional Job Management

**Best for**: Tasks requiring synchronous results, job tracking, parent-child relationships

```python
# Synchronous execution - waits for result
result = await claude_run(
    task="Create a Python function to calculate fibonacci",
    cwd="/project",
    outputFormat="json",
    permissionMode="default"
)

# Asynchronous execution - returns immediately
job_id = await claude_run_async(
    task="Analyze large codebase",
    cwd="/project",
    parentJobId="parent_123"  # For nested jobs
)

# Check status
status = await claude_status(jobId=job_id)
# Returns: {"status": "running", "progress": 45, ...}

# Get result when complete
result = await claude_result(jobId=job_id)

# Monitor system
dashboard = await claude_dashboard()
# Returns: {"activeJobs": 5, "cpuUsage": 45.2, ...}
```

**V1 Recursion Management**:
- Max depth: 3 levels
- Concurrent jobs per depth: 8
- Total jobs: 30
- Supports parent-child job relationships

### V2: Fire-and-Forget Parallel Execution

**Best for**: Parallel analysis, independent tasks, result aggregation

```python
# Spawn single agent - returns immediately
result = await spawn_agent(
    task="Analyze security vulnerabilities",
    agent_profile="security_analyst",
    output_dir="/tmp/results",
    timeout=600,  # seconds
    metadata={"type": "security"}
)
job_id = result["job_id"]

# Spawn multiple agents in parallel
result = await spawn_parallel_agents(
    tasks=[
        "Review code quality",
        "Generate tests",
        "Create documentation"
    ],
    agent_profile="comprehensive",
    output_dir="/tmp/results",
    timeout=600
)
job_ids = [job["job_id"] for job in result["jobs"]]

# Collect results (non-blocking)
results = await collect_results(
    job_ids=job_ids,
    output_dir="/tmp/results",
    include_partial=True,
    cleanup=False
)

# Aggregate findings
aggregated = await aggregate_results(
    output_dir="/tmp/results",
    aggregation_type="consensus"  # or "summary", "merge"
)
```

**V2 Patterns**:
- Fire-and-forget: Agents run independently
- No recursion tracking between agents
- Results written to files
- Three aggregation modes:
  - `summary`: Key findings overview
  - `merge`: Combine all data
  - `consensus`: Find agreements

### V3: Intelligent Mode-Based Execution

**Best for**: Complex tasks needing quality assurance, automatic mode selection, multi-agent orchestration

```python
# Auto-detect best mode
result = await claude_run_v3(
    task="Create a production-ready REST API with tests and docs",
    auto_detect=True  # Analyzes task to select mode
)

# Explicit mode selection
result = await claude_run_v3(
    task="Fix security vulnerabilities",
    mode="QUALITY",  # Forces quality mode with review
    quality_level="high"
)

# Available modes:
# - RAPID: Quick, no validation
# - CODE: Standard with basic checks  
# - QUALITY: Code + Review + Tests
# - FULL_CYCLE: Everything including docs
# - TESTING: Focus on test generation
# - DOCUMENTATION: Focus on docs
# - DEBUG: Fix issues with validation
# - ANALYSIS: Code understanding
# - REVIEW: Code critique
```

**V3 Intelligence**:
- Analyzes task complexity
- Detects quality requirements
- Selects appropriate agents
- Configures iterations and thresholds

## How Agents Should Use These Servers

### Decision Tree for Server Selection

```
Is the task simple and needs immediate result?
├─ Yes → V1 with claude_run
└─ No → Continue
    │
    Are multiple independent analyses needed?
    ├─ Yes → V2 with spawn_parallel_agents
    └─ No → Continue
        │
        Does task need quality assurance?
        ├─ Yes → V3 with appropriate mode
        └─ No → V1 with claude_run_async
```

### Best Practices for Agents

#### 1. Task Formatting

**V1/V2 - Be explicit**:
```python
task = """
Create a Python class called DatabaseManager with:
1. Connection pooling
2. Query builder
3. Transaction support
4. Error handling
Include comprehensive docstrings.
"""
```

**V3 - Include quality hints**:
```python
task = """
Create a PRODUCTION-READY authentication system with:
- JWT token management
- Rate limiting
- Security best practices
- Comprehensive tests
- API documentation
"""
# V3 will detect "production-ready" and select FULL_CYCLE mode
```

#### 2. Parameter Optimization

**V1 Parameters**:
```python
# For code generation
params = {
    "outputFormat": "json",  # Structured output
    "permissionMode": "default",  # Standard permissions
    "cwd": "/project"  # Working directory
}

# For analysis
params = {
    "outputFormat": "text",  # Human-readable
    "permissionMode": "readonly",  # No modifications
}
```

**V2 Agent Profiles**:
```python
profiles = {
    "quick_analysis": {"timeout": 60000, "max_depth": 1},
    "comprehensive": {"timeout": 300000, "max_depth": 3},
    "security_analyst": {"focus": "vulnerabilities"},
    "performance_optimizer": {"focus": "bottlenecks"}
}
```

**V3 Quality Levels**:
```python
quality_mapping = {
    "rapid": "Prototype/POC",
    "normal": "Development",
    "high": "Staging/QA",
    "maximum": "Production"
}
```

#### 3. Result Handling

**V1 - Check completion**:
```python
async def wait_for_result(job_id, max_wait=300):
    for _ in range(max_wait):
        status = await claude_status(job_id)
        if status["status"] == "completed":
            return await claude_result(job_id)
        elif status["status"] == "failed":
            raise Exception(f"Job failed: {status.get('error')}")
        await asyncio.sleep(1)
    raise TimeoutError("Job timed out")
```

**V2 - Batch collection**:
```python
# Spawn agents
job_ids = await spawn_parallel_agents(tasks)

# Wait and collect
results = await collect_results({
    "job_ids": job_ids,
    "wait_for_completion": True,
    "timeout": 600000
})

# Process results
successful = results["completed"]
failed = results["failed"]
```

**V3 - Mode-aware processing**:
```python
result = await claude_run_v3(task, mode="QUALITY")

# Result includes mode-specific data
if result["mode"] == "QUALITY":
    review_score = result["config"]["quality_threshold"]
    critic_enabled = result["config"]["enable_critic"]
    # Process quality metrics
```

## Performance Characteristics

### V1: Synchronous Pipeline
- **Latency**: Medium (waits for completion)
- **Throughput**: Limited by recursion depth
- **Best for**: Sequential tasks, debugging

### V2: Parallel Fire-and-Forget
- **Latency**: Low (immediate return)
- **Throughput**: High (parallel execution)
- **Best for**: Batch processing, independent analyses

### V3: Intelligent Orchestration
- **Latency**: Variable (depends on mode)
- **Throughput**: Optimized per mode
- **Best for**: Production systems, quality-critical tasks

## Example: Same Task, Different Servers

**Task**: "Create a user authentication system"

**V1 Approach**:
```python
job_id = await claude_run_async(
    task="Create a user authentication system with login, register, and password reset"
)
result = await claude_result(job_id)
```

**V2 Approach**:
```python
# Break into parallel subtasks
jobs = await spawn_parallel_agents([
    "Create user model and database schema",
    "Implement authentication endpoints",
    "Add password hashing and validation",
    "Create JWT token management"
])
results = await collect_results({"job_ids": jobs})
final = await aggregate_results(aggregation_type="merge")
```

**V3 Approach**:
```python
# Let V3 handle orchestration
result = await claude_run_v3(
    task="Create a production-ready user authentication system",
    auto_detect=True  # Will select FULL_CYCLE mode
)
# V3 automatically includes tests, docs, security review
```

## Troubleshooting

### Common Issues

1. **V1 timeout errors**: Increase `CLAUDE_TIMEOUT_SECONDS`
2. **V2 missing results**: Check `/tmp/claude_results/` directory
3. **V3 wrong mode**: Use explicit `mode` parameter instead of auto-detect

### Debug Information

```python
# V1 - Check system state
dashboard = await claude_dashboard()
stats = await claude_recursion_stats()

# V2 - Check agent health
health = await check_agent_health()  # All agents
health = await check_agent_health(job_id)  # Specific agent

# V3 - Check configuration
status = await get_v3_status()
print(status["modes_available"])
print(status["features"])
```

## Summary

- **Use V1** for traditional job management with tracking
- **Use V2** for parallel, independent agent tasks
- **Use V3** for intelligent, quality-assured execution
- Format tasks clearly with requirements
- Choose parameters based on task complexity
- Handle results according to server pattern