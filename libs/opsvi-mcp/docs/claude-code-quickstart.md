# Claude Code MCP Server - Quick Start Guide

## 5-Minute Setup

### 1. Install

```bash
pip install opsvi-mcp
```

### 2. Configure

```bash
export CLAUDE_CODE_TOKEN="your-claude-api-token"
```

### 3. Start Server

```bash
python -m opsvi_mcp.servers.claude_code
```

### 4. Test It

```python
# In your MCP client
result = await claude_run("print('Hello from Claude Code!')")
print(result)
```

## Complete Setup Guide

### Prerequisites Checklist

- [ ] Python 3.9 or higher installed
- [ ] Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- [ ] Valid Claude API key
- [ ] MCP-compatible client (e.g., Claude Desktop)

### Step 1: Installation Options

#### Option A: Install from PyPI
```bash
pip install opsvi-mcp
```

#### Option B: Install from Source
```bash
git clone https://github.com/opsvi/master_root.git
cd master_root/libs/opsvi-mcp
pip install -e .
```

### Step 2: Authentication Setup

#### Method 1: Environment Variable
```bash
export CLAUDE_CODE_TOKEN="sk-ant-..."
```

#### Method 2: .env File
Create `.env` in your project root:
```env
CLAUDE_CODE_TOKEN=sk-ant-...
```

#### Method 3: MCP Configuration
Add to your MCP client config:
```json
{
  "mcpServers": {
    "claude-code": {
      "command": "python",
      "args": ["-m", "opsvi_mcp.servers.claude_code"],
      "env": {
        "CLAUDE_CODE_TOKEN": "sk-ant-..."
      }
    }
  }
}
```

### Step 3: Start the Server

#### Standalone Mode
```bash
python -m opsvi_mcp.servers.claude_code
```

#### With Custom Settings
```bash
export CLAUDE_MAX_RECURSION_DEPTH=5
export CLAUDE_LOG_LEVEL=DEBUG
python -m opsvi_mcp.servers.claude_code
```

### Step 4: Verify Installation

```python
# Test basic functionality
result = await claude_run("print('Setup successful!')")

# Test async execution
job = await claude_run_async("print('Async works!')")
status = await claude_status(json.loads(job)["jobId"])

# Test dashboard
dashboard = await claude_dashboard()
print(f"Server running with {dashboard['activeJobs']} active jobs")
```

## Basic Usage Examples

### Example 1: Simple Task

```python
# Execute a simple task
result = await claude_run(
    task="Create a Python function that calculates the area of a circle"
)
print(result)
```

### Example 2: Parallel Execution

```python
# Start multiple tasks in parallel
job1 = await claude_run_async("Analyze file1.py for code quality")
job2 = await claude_run_async("Generate tests for file2.py")
job3 = await claude_run_async("Document functions in file3.py")

# Wait for completion
jobs = [job1, job2, job3]
for job_response in jobs:
    job_id = json.loads(job_response)["jobId"]
    
    # Poll until complete
    while True:
        status = json.loads(await claude_status(job_id))
        if status["status"] == "completed":
            result = await claude_result(job_id)
            print(f"Job {job_id} result: {result}")
            break
        await asyncio.sleep(2)
```

### Example 3: Working Directory

```python
# Execute in specific directory
result = await claude_run(
    task="List all Python files and their line counts",
    cwd="/home/user/my-project"
)
```

### Example 4: Permission Modes

```python
# Bypass all permissions (fully automated)
result = await claude_run(
    task="Refactor the database module",
    permissionMode="bypassPermissions"
)

# Only auto-approve edits
result = await claude_run(
    task="Update documentation",
    permissionMode="acceptEdits"
)

# Planning mode only (no execution)
result = await claude_run(
    task="Plan the architecture for new feature",
    permissionMode="plan"
)
```

### Example 5: Nested Execution

```python
# Task that spawns sub-tasks
result = await claude_run("""
    Analyze the project structure and:
    1. For each Python module, create a sub-task to:
       - Count lines of code
       - Identify missing docstrings
       - Check for type hints
    2. Aggregate all results into a report
""")
```

## Common Patterns

### Pattern 1: Fire and Forget

```python
async def fire_and_forget(task):
    """Start a task without waiting for completion"""
    job = await claude_run_async(task)
    job_id = json.loads(job)["jobId"]
    print(f"Started job {job_id}")
    return job_id
```

### Pattern 2: Batch Processing

```python
async def batch_process(tasks):
    """Process multiple tasks with concurrency limit"""
    max_concurrent = 3
    results = []
    
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i:i + max_concurrent]
        
        # Start batch
        jobs = []
        for task in batch:
            job = await claude_run_async(task)
            jobs.append(json.loads(job)["jobId"])
        
        # Wait for batch completion
        for job_id in jobs:
            while True:
                status = json.loads(await claude_status(job_id))
                if status["status"] == "completed":
                    result = await claude_result(job_id)
                    results.append(result)
                    break
                await asyncio.sleep(2)
    
    return results
```

### Pattern 3: Timeout Handling

```python
async def execute_with_timeout(task, timeout_seconds=300):
    """Execute task with custom timeout"""
    job = await claude_run_async(task)
    job_id = json.loads(job)["jobId"]
    
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        status = json.loads(await claude_status(job_id))
        
        if status["status"] == "completed":
            return await claude_result(job_id)
        elif status["status"] in ["failed", "timeout"]:
            raise Exception(f"Job failed: {status.get('error')}")
        
        await asyncio.sleep(2)
    
    # Timeout reached - kill job
    await claude_kill_job(job_id)
    raise Exception("Job exceeded timeout")
```

### Pattern 4: Progress Monitoring

```python
async def execute_with_progress(task):
    """Execute task with progress updates"""
    job = await claude_run_async(task, verbose=True)
    job_id = json.loads(job)["jobId"]
    
    print(f"Job {job_id} started...")
    last_status = None
    
    while True:
        status = json.loads(await claude_status(job_id))
        dashboard = json.loads(await claude_dashboard())
        
        # Print status changes
        if status["status"] != last_status:
            print(f"Status: {status['status']}")
            last_status = status["status"]
        
        # Print system metrics
        print(f"  Active jobs: {dashboard['activeJobs']}, "
              f"Load: {dashboard['systemLoad']:.1f}%", end='\r')
        
        if status["status"] in ["completed", "failed", "timeout"]:
            print()  # New line after progress
            break
        
        await asyncio.sleep(1)
    
    if status["status"] == "completed":
        return await claude_result(job_id)
    else:
        raise Exception(f"Job failed: {status.get('error')}")
```

## Configuration Options

### Environment Variables

```bash
# Core settings
export CLAUDE_CODE_TOKEN="your-token"

# Recursion limits
export CLAUDE_MAX_RECURSION_DEPTH=3
export CLAUDE_MAX_CONCURRENT_AT_DEPTH=5
export CLAUDE_MAX_TOTAL_JOBS=20

# Timeouts
export CLAUDE_TIMEOUT_MULTIPLIER=1.5

# Logging
export CLAUDE_LOG_LEVEL=INFO  # ERROR, WARN, INFO, DEBUG, TRACE
export CLAUDE_PERF_LOGGING=true
export CLAUDE_CHILD_LOGGING=true
export CLAUDE_RECURSION_LOGGING=true
```

### Configuration File

Create `claude-code-config.json`:
```json
{
  "recursion": {
    "max_depth": 3,
    "max_concurrent_at_depth": 5,
    "max_total_jobs": 20,
    "timeout_multiplier": 1.5
  },
  "logging": {
    "log_level": "INFO",
    "enable_performance_logging": true,
    "enable_child_process_logging": true,
    "enable_recursion_logging": true,
    "logs_dir": "/var/log/claude-code"
  },
  "server": {
    "base_timeout": 300000,
    "max_timeout": 1800000
  }
}
```

## Troubleshooting

### Issue: "Authentication failed"

**Solution 1**: Verify token is set
```bash
echo $CLAUDE_CODE_TOKEN
```

**Solution 2**: Test Claude CLI directly
```bash
claude-code "print('test')" --headless
```

**Solution 3**: Re-export token
```bash
export CLAUDE_CODE_TOKEN="sk-ant-..."
```

### Issue: "Recursion depth limit exceeded"

**Solution 1**: Increase limit
```bash
export CLAUDE_MAX_RECURSION_DEPTH=5
```

**Solution 2**: Reduce task complexity
```python
# Instead of deep recursion, use iteration
result = await claude_run("""
    Process items iteratively rather than recursively
""")
```

### Issue: "Job timeout"

**Solution 1**: Increase timeout
```python
# Set longer timeout for complex tasks
result = await claude_run(
    task="Complex analysis task",
    # Timeout handled by server config
)
```

**Solution 2**: Break into smaller tasks
```python
# Split large task
subtasks = split_large_task(main_task)
results = []
for subtask in subtasks:
    result = await claude_run(subtask)
    results.append(result)
```

### Issue: "Too many concurrent jobs"

**Solution 1**: Check active jobs
```python
dashboard = await claude_dashboard()
print(f"Active jobs: {dashboard['activeJobs']}")

# List all jobs
jobs = await claude_list_jobs()
for job in json.loads(jobs):
    if job["status"] == "running":
        print(f"Running: {job['jobId']}")
```

**Solution 2**: Kill stuck jobs
```python
jobs = json.loads(await claude_list_jobs())
for job in jobs:
    if job["status"] == "running":
        # Kill jobs running too long
        start = datetime.fromisoformat(job["startTime"])
        if (datetime.now() - start).seconds > 600:  # 10 minutes
            await claude_kill_job(job["jobId"])
```

## Best Practices

### 1. Always Handle Errors

```python
async def safe_execute(task):
    try:
        result = await claude_run(task)
        return json.loads(result)
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### 2. Use Async for Long Tasks

```python
# Good - non-blocking
job = await claude_run_async("Long running analysis")

# Bad - blocks everything
result = await claude_run("Long running analysis")
```

### 3. Monitor System Load

```python
async def check_before_execute(task):
    dashboard = json.loads(await claude_dashboard())
    
    if dashboard["activeJobs"] >= 5:
        print("System busy, waiting...")
        await asyncio.sleep(10)
    
    return await claude_run_async(task)
```

### 4. Clean Up Resources

```python
async def cleanup_old_jobs():
    jobs = json.loads(await claude_list_jobs())
    
    for job in jobs:
        if job["status"] == "completed":
            # Results are already stored, safe to ignore
            pass
        elif job["status"] == "running":
            # Check if stuck
            start = datetime.fromisoformat(job["startTime"])
            if (datetime.now() - start).seconds > 1800:  # 30 min
                await claude_kill_job(job["jobId"])
```

### 5. Use Appropriate Permission Modes

```python
# For automation - bypass all
result = await claude_run(task, permissionMode="bypassPermissions")

# For supervised tasks - accept edits only
result = await claude_run(task, permissionMode="acceptEdits")

# For planning - no execution
result = await claude_run(task, permissionMode="plan")
```

## Next Steps

1. **Read Full Documentation**: See [claude-code-server.md](./claude-code-server.md)
2. **API Reference**: See [claude-code-api-reference.md](./claude-code-api-reference.md)
3. **Advanced Examples**: Check the `examples/` directory
4. **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

## Support

- **GitHub Issues**: [Report bugs](https://github.com/opsvi/master_root/issues)
- **Documentation**: [Full docs](./claude-code-server.md)
- **Examples**: [Code examples](../examples/)

## Quick Reference Card

```python
# Import (in MCP client)
from your_mcp_client import claude_run, claude_run_async, claude_status, claude_result

# Basic execution
result = await claude_run("Your task here")

# Async execution
job = await claude_run_async("Your task here")
job_id = json.loads(job)["jobId"]

# Check status
status = await claude_status(job_id)

# Get result
result = await claude_result(job_id)

# List jobs
jobs = await claude_list_jobs()

# Kill job
await claude_kill_job(job_id)

# Dashboard
metrics = await claude_dashboard()

# Recursion stats
stats = await claude_recursion_stats()
```