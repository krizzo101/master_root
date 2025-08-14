# Migration Guide: Claude Code V1 → V2 → V3

## Overview

This guide helps you migrate between different versions of Claude Code MCP servers, explaining the differences, benefits, and migration strategies for each version.

## Quick Decision Matrix

| Your Need | Recommended Version | Why |
|-----------|-------------------|-----|
| Simple, synchronous tasks | V1 | Direct control, immediate results |
| Massive parallel analysis | V2 | Fire-and-forget, high concurrency |
| Production systems | V3 | Quality assurance, intelligent orchestration |
| Debugging/Development | V1 | Easier to trace, synchronous flow |
| Research/Exploration | V2 | Parallel exploration, result aggregation |
| Customer-facing code | V3 | Built-in quality gates, documentation |

## Version Comparison

### Architecture Evolution

```
V1: Client → Server → Agent → Result
    (Synchronous, coupled, blocking)

V2: Client → Server → [Agent1, Agent2, ...] → Results Directory
    (Asynchronous, decoupled, non-blocking)

V3: Client → Server → Mode Detector → [Specialized Agents] → Quality Gates → Result
    (Intelligent, orchestrated, quality-assured)
```

### Tool Count Evolution

- **V1**: 8 tools (fine-grained control)
- **V2**: 6 tools (batch operations)
- **V3**: 2 tools (intelligent abstraction)

## Migration from V1 to V2

### When to Migrate

Migrate to V2 when you need:
- Parallel execution of independent tasks
- Fire-and-forget execution patterns
- Better failure isolation
- Higher throughput

### Code Changes

#### Before (V1)
```python
# V1: Synchronous, blocking
result = await claude_run(
    task="Analyze file1.py"
)
# Waits for completion

# V1: Async with tracking
job_id = await claude_run_async(
    task="Analyze file2.py"
)
# Still maintains connection
status = await claude_status(job_id)
result = await claude_result(job_id)
```

#### After (V2)
```python
# V2: Fire-and-forget
job = await spawn_agent({
    "task": "Analyze file1.py",
    "output_dir": "/tmp/results"
})
# Returns immediately

# V2: Parallel execution
jobs = await spawn_parallel_agents([
    "Analyze file1.py",
    "Analyze file2.py",
    "Analyze file3.py"
])
# All run in parallel

# Collect when ready
results = await collect_results({
    "output_dir": "/tmp/results"
})
```

### Configuration Changes

#### V1 Configuration
```json
{
  "claude-code": {
    "env": {
      "CLAUDE_CODE_TOKEN": "token",
      "CLAUDE_MAX_CONCURRENT_JOBS": "8",
      "CLAUDE_TIMEOUT_SECONDS": "300"
    }
  }
}
```

#### V2 Configuration
```json
{
  "claude-code-v2": {
    "env": {
      "CLAUDE_CODE_TOKEN": "token",
      "CLAUDE_RESULTS_DIR": "/tmp/claude_results",
      "CLAUDE_MAX_CONCURRENT_L1": "10",
      "CLAUDE_DEFAULT_TIMEOUT": "600"
    }
  }
}
```

### Pattern Changes

#### Sequential Processing
```python
# V1: Sequential
for task in tasks:
    result = await claude_run(task)
    process(result)

# V2: Batch parallel
jobs = await spawn_parallel_agents(tasks)
await asyncio.sleep(30)  # Let them run
results = await collect_results()
for result in results["completed"]:
    process(result)
```

#### Error Handling
```python
# V1: Direct error handling
try:
    result = await claude_run(task)
except Exception as e:
    handle_error(e)

# V2: Check result status
results = await collect_results()
for job_id in results["failed"]:
    handle_failure(job_id)
for job_id in results["completed"]:
    handle_success(job_id)
```

## Migration from V2 to V3

### When to Migrate

Migrate to V3 when you need:
- Automatic quality assurance
- Intelligent task decomposition
- Multi-agent collaboration
- Production-ready outputs
- Built-in testing and documentation

### Code Changes

#### Before (V2)
```python
# V2: Manual task splitting
jobs = await spawn_parallel_agents([
    "Create user model",
    "Create authentication logic",
    "Create API endpoints",
    "Write tests",
    "Generate documentation"
])
# Hope they coordinate...

results = await collect_results()
# Manual quality check needed
```

#### After (V3)
```python
# V3: Intelligent orchestration
result = await claude_run_v3(
    task="Create production-ready user authentication system",
    auto_detect=True  # Automatically handles everything
)
# Includes models, logic, endpoints, tests, docs
# With built-in quality assurance
```

### Configuration Changes

#### V2 Configuration
```json
{
  "claude-code-v2": {
    "env": {
      "CLAUDE_MAX_CONCURRENT_L1": "10",
      "CLAUDE_RESULTS_DIR": "/tmp/results"
    }
  }
}
```

#### V3 Configuration
```json
{
  "claude-code-v3": {
    "env": {
      "CLAUDE_ENABLE_MULTI_AGENT": "true",
      "CLAUDE_MAX_RECURSION_DEPTH": "5",
      "CLAUDE_ENABLE_CRITIC": "true",
      "CLAUDE_ENABLE_TESTING": "true",
      "CLAUDE_QUALITY_THRESHOLD": "0.8",
      "CLAUDE_AGENT_MODE_AUTO_DETECT": "true"
    }
  }
}
```

### Pattern Changes

#### Task Description
```python
# V2: Explicit decomposition
tasks = [
    "Create database schema",
    "Implement CRUD operations",
    "Add validation",
    "Write unit tests"
]
await spawn_parallel_agents(tasks)

# V3: Natural language description
await claude_run_v3(
    task="Create a complete database layer with CRUD operations, validation, and tests",
    auto_detect=True
)
# V3 handles decomposition automatically
```

#### Quality Assurance
```python
# V2: Manual quality check
results = await collect_results()
for result in results["completed"]:
    quality = manual_review(result)
    if quality < threshold:
        # Spawn another agent to fix
        await spawn_agent({"task": f"Fix issues in {result}"})

# V3: Built-in quality gates
result = await claude_run_v3(
    task="Create API endpoints",
    mode="QUALITY",  # Automatic review and iteration
    quality_level="high"
)
# Already reviewed and improved
```

## Migration from V1 to V3

### Direct Jump Strategy

If jumping directly from V1 to V3:

#### Before (V1)
```python
# V1: Multiple separate calls
code_result = await claude_run("Implement feature")
test_result = await claude_run("Write tests for feature")
doc_result = await claude_run("Document feature")
# No coordination between tasks
```

#### After (V3)
```python
# V3: Single intelligent call
result = await claude_run_v3(
    task="Implement feature with tests and documentation",
    mode="FULL_CYCLE"
)
# Coordinated, quality-assured, complete
```

### Key Differences

| Aspect | V1 | V3 |
|--------|-----|-----|
| **Tools** | 8 separate tools | 2 intelligent tools |
| **Execution** | Manual orchestration | Automatic orchestration |
| **Quality** | External validation | Built-in quality gates |
| **Agents** | Single agent | Multiple specialized agents |
| **Modes** | None | 10 automatic modes |

## Gradual Migration Strategy

### Phase 1: Parallel Running
Run both versions simultaneously:
```python
# Keep V1 for critical paths
v1_result = await claude_run(critical_task)

# Test V3 for new features
v3_result = await claude_run_v3(new_feature_task, auto_detect=True)
```

### Phase 2: Feature-by-Feature
Migrate specific features:
```python
def process_task(task, use_v3=False):
    if use_v3 and task_is_complex(task):
        return await claude_run_v3(task, auto_detect=True)
    else:
        return await claude_run(task)
```

### Phase 3: Full Migration
Update all configurations and code:
```bash
# Update MCP config
sed -i 's/claude-code/claude-code-v3/g' .mcp.json

# Update environment
export CLAUDE_ENABLE_MULTI_AGENT=true
export CLAUDE_AGENT_MODE_AUTO_DETECT=true
```

## Rollback Procedures

### V3 to V2 Rollback
```python
# If V3 has issues, fallback to V2
try:
    result = await claude_run_v3(task, mode="QUALITY")
except Exception as e:
    # Fallback to V2
    job = await spawn_agent({"task": task})
    result = await collect_results()
```

### V2 to V1 Rollback
```python
# If V2 has issues, fallback to V1
try:
    jobs = await spawn_parallel_agents(tasks)
except Exception as e:
    # Fallback to V1
    for task in tasks:
        result = await claude_run(task)
```

## Performance Considerations

### Concurrency Settings

#### V1 → V2
- V1: Fixed concurrency (8 jobs)
- V2: Higher parallelism (10+ L1 agents)
- **Action**: Increase `CLAUDE_MAX_CONCURRENT_L1`

#### V2 → V3
- V2: Static concurrency
- V3: Adaptive concurrency by depth
- **Action**: Configure depth-based limits

### Timeout Adjustments

#### V1 → V2
```bash
# V1: Seconds
CLAUDE_TIMEOUT_SECONDS=300

# V2: Milliseconds
CLAUDE_DEFAULT_TIMEOUT=300000
```

#### V2 → V3
```bash
# V3: Dynamic timeouts
CLAUDE_ENABLE_ADAPTIVE_TIMEOUT=true
CLAUDE_BASE_TIMEOUT=300000
CLAUDE_MAX_TIMEOUT=1800000
```

## Feature Mapping

### V1 Features in V2/V3

| V1 Feature | V2 Equivalent | V3 Equivalent |
|------------|---------------|---------------|
| `claude_run` | `spawn_agent` (async) | `claude_run_v3` (mode="RAPID") |
| `claude_run_async` | `spawn_agent` | `claude_run_v3` (any mode) |
| `claude_status` | `check_agent_health` | Built into result |
| `claude_result` | `collect_results` | Direct return |
| `claude_list_jobs` | Check results directory | `get_v3_status` |
| `claude_kill_job` | `kill_agent` | Automatic cleanup |
| `claude_dashboard` | System monitoring | Built-in metrics |
| `claude_recursion_stats` | N/A | Configuration status |

## Testing Your Migration

### V1 → V2 Test
```python
async def test_v2_migration():
    # Test fire-and-forget
    job = await spawn_agent({"task": "Test task"})
    assert job["success"]
    
    # Test parallel
    jobs = await spawn_parallel_agents(["Task1", "Task2"])
    assert len(jobs["jobs"]) == 2
    
    # Test collection
    await asyncio.sleep(5)
    results = await collect_results()
    assert results["completed"] > 0
```

### V2 → V3 Test
```python
async def test_v3_migration():
    # Test auto-detect
    result = await claude_run_v3(
        task="Create simple function",
        auto_detect=True
    )
    assert result["mode"] == "CODE"
    
    # Test quality mode
    result = await claude_run_v3(
        task="Production API",
        mode="QUALITY"
    )
    assert "critic_review" in result
```

## Common Migration Issues

### Issue 1: Different Result Formats
**V1**: Direct result object
**V2**: Results in files
**V3**: Comprehensive result with metadata

**Solution**: Create adapters
```python
def normalize_result(version, raw_result):
    if version == "v1":
        return {"output": raw_result}
    elif version == "v2":
        return json.load(open(raw_result["result_location"]))
    elif version == "v3":
        return raw_result["final_output"]
```

### Issue 2: Timeout Handling
**V1**: Fails immediately
**V2**: Partial results available
**V3**: Checkpointing and recovery

**Solution**: Implement consistent timeout handling
```python
def handle_timeout(version, job_id):
    if version == "v3":
        # V3 can recover
        return recover_from_checkpoint(job_id)
    elif version == "v2":
        # V2 might have partial results
        return collect_partial_results(job_id)
    else:
        # V1 needs retry
        return retry_task(job_id)
```

## Recommended Migration Path

### For New Projects
Start directly with **V3** - it's the most mature and feature-complete.

### For Existing V1 Projects
1. **Simple projects**: Migrate directly to V3
2. **Complex projects**: V1 → V2 (stabilize) → V3

### For Existing V2 Projects
Migrate to V3 when you need:
- Better quality assurance
- Automatic task decomposition
- Multi-agent coordination

## Summary

- **V1 → V2**: Gain parallelism and decoupling
- **V2 → V3**: Gain intelligence and quality
- **V1 → V3**: Gain everything but requires more changes

Choose based on your needs:
- **Keep V1**: For simple, synchronous tasks
- **Use V2**: For parallel, independent analyses
- **Use V3**: For production, quality-critical systems