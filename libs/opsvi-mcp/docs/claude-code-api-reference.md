# Claude Code MCP Server - API Reference

## Quick Reference

| Tool | Type | Returns | Purpose |
|------|------|---------|---------|
| `claude_run` | Sync | Result JSON | Execute task and wait for completion |
| `claude_run_async` | Async | Job ID | Start task and return immediately |
| `claude_status` | Query | Status JSON | Check job progress |
| `claude_result` | Query | Result JSON | Get completed job output |
| `claude_list_jobs` | Query | Job Array | List all jobs |
| `claude_kill_job` | Action | Success JSON | Terminate running job |
| `claude_dashboard` | Query | Metrics JSON | System performance stats |
| `claude_recursion_stats` | Query | Stats JSON | Recursion metrics |

## Detailed API Documentation

### claude_run

Execute a Claude Code task synchronously. Blocks until the task completes.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task` | string | Yes | - | Task description for Claude Code |
| `cwd` | string | No | Current dir | Working directory for execution |
| `outputFormat` | string | No | "json" | Output format: "json" or "text" |
| `permissionMode` | string | No | "bypassPermissions" | Permission handling mode |
| `verbose` | boolean | No | false | Enable verbose output |
| `parentJobId` | string | No | null | Parent job ID for recursion |

#### Permission Modes

- **`bypassPermissions`**: Auto-approve all operations (recommended for automation)
- **`acceptEdits`**: Auto-approve file edits only
- **`default`**: Interactive mode (not suitable for headless)
- **`plan`**: Planning mode without execution

#### Response

Returns the Claude Code execution result as a JSON string.

**Success Response Structure**:
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 15234,
  "duration_api_ms": 16789,
  "num_turns": 8,
  "result": "Task completed successfully",
  "session_id": "uuid-here",
  "total_cost_usd": 0.0234,
  "usage": {
    "input_tokens": 12345,
    "output_tokens": 678,
    "cache_creation_input_tokens": 5000,
    "cache_read_input_tokens": 10000
  },
  "permission_denials": []
}
```

#### Example

```python
result = await claude_run(
    task="Write a Python function to calculate factorial",
    cwd="/home/user/project",
    outputFormat="json",
    permissionMode="bypassPermissions",
    verbose=True
)
```

---

### claude_run_async

Execute a Claude Code task asynchronously. Returns immediately with a job ID.

#### Parameters

Same as `claude_run`.

#### Response

Returns a JSON object with job information:

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Job started successfully"
}
```

#### Example

```python
job = await claude_run_async(
    task="Analyze all Python files in the project",
    cwd="/home/user/project"
)
job_id = json.loads(job)["jobId"]
```

---

### claude_status

Check the status of an asynchronous job.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | string | Yes | Job ID from claude_run_async |

#### Response

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "task": "Analyze all Python files in the project",
  "startTime": "2025-08-12T15:56:02.474887",
  "endTime": null,
  "error": null,
  "recursionDepth": 0,
  "parentJobId": null
}
```

#### Status Values

- **`running`**: Job is currently executing
- **`completed`**: Job finished successfully
- **`failed`**: Job encountered an error
- **`timeout`**: Job exceeded time limit

#### Example

```python
status = await claude_status(jobId="550e8400-e29b-41d4-a716-446655440000")
status_obj = json.loads(status)
if status_obj["status"] == "completed":
    print("Job finished!")
```

---

### claude_result

Retrieve the result of a completed job.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | string | Yes | Job ID from claude_run_async |

#### Response

Returns the full Claude Code execution result (same structure as `claude_run` response).

#### Error Cases

- Throws exception if job not found
- Throws exception if job still running
- Throws exception if job failed

#### Example

```python
try:
    result = await claude_result(jobId="550e8400-e29b-41d4-a716-446655440000")
    result_obj = json.loads(result)
    print(f"Result: {result_obj['result']}")
except Exception as e:
    print(f"Error getting result: {e}")
```

---

### claude_list_jobs

List all jobs (active and recent).

#### Parameters

None

#### Response

Returns an array of job status objects:

```json
[
  {
    "jobId": "job-1-id",
    "status": "completed",
    "task": "Task description",
    "startTime": "2025-08-12T15:56:02.474887",
    "endTime": "2025-08-12T15:56:18.794919",
    "error": null,
    "recursionDepth": 0,
    "parentJobId": null
  },
  {
    "jobId": "job-2-id",
    "status": "running",
    "task": "Another task",
    "startTime": "2025-08-12T15:57:02.474887",
    "endTime": null,
    "error": null,
    "recursionDepth": 1,
    "parentJobId": "job-1-id"
  }
]
```

#### Example

```python
jobs = await claude_list_jobs()
jobs_list = json.loads(jobs)
active = [j for j in jobs_list if j["status"] == "running"]
print(f"Active jobs: {len(active)}")
```

---

### claude_kill_job

Terminate a running job.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | string | Yes | Job ID to terminate |

#### Response

```json
{
  "success": true,
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 killed"
}
```

#### Example

```python
result = await claude_kill_job(jobId="550e8400-e29b-41d4-a716-446655440000")
if json.loads(result)["success"]:
    print("Job terminated successfully")
```

---

### claude_dashboard

Get real-time system performance metrics.

#### Parameters

None

#### Response

```json
{
  "activeJobs": 3,
  "completedJobs": 15,
  "failedJobs": 2,
  "averageDuration": 25.5,
  "parallelEfficiency": 2.8,
  "nestedDepth": 2,
  "systemLoad": 65.5,
  "recursionStats": {
    "max_depth": 3,
    "depth_counts": {"0": 2, "1": 1},
    "root_job_counts": {"job-1": 3},
    "active_contexts": 3
  }
}
```

#### Metrics Explained

- **`activeJobs`**: Currently running jobs
- **`completedJobs`**: Successfully finished jobs
- **`failedJobs`**: Jobs that encountered errors
- **`averageDuration`**: Mean job execution time (seconds)
- **`parallelEfficiency`**: Ratio of parallel speedup
- **`nestedDepth`**: Maximum recursion depth in use
- **`systemLoad`**: CPU/memory utilization percentage

#### Example

```python
dashboard = await claude_dashboard()
data = json.loads(dashboard)
print(f"System efficiency: {data['parallelEfficiency']:.2f}x")
```

---

### claude_recursion_stats

Get detailed recursion statistics.

#### Parameters

None

#### Response

```json
{
  "max_depth": 3,
  "depth_counts": {
    "0": 5,
    "1": 3,
    "2": 1
  },
  "root_job_counts": {
    "job-root-1": 4,
    "job-root-2": 5
  },
  "active_contexts": 9
}
```

#### Fields

- **`max_depth`**: Configured maximum recursion depth
- **`depth_counts`**: Number of jobs at each depth level
- **`root_job_counts`**: Jobs spawned per root job
- **`active_contexts`**: Total active recursion contexts

#### Example

```python
stats = await claude_recursion_stats()
data = json.loads(stats)
if data["depth_counts"].get("2", 0) > 0:
    print("Warning: Deep recursion detected")
```

## Error Handling

### Common Error Responses

#### Authentication Error
```json
{
  "error": "Authentication failed: Invalid or missing CLAUDE_CODE_TOKEN"
}
```

#### Recursion Limit Error
```json
{
  "error": "Recursion depth limit exceeded: 3/3. Job would create infinite loop."
}
```

#### Timeout Error
```json
{
  "error": "Job timeout at recursion depth 0"
}
```

#### Job Not Found
```json
{
  "error": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Error Handling Best Practices

```python
async def safe_execute(task):
    try:
        # Start job
        job_response = await claude_run_async(task)
        job = json.loads(job_response)
        job_id = job["jobId"]
        
        # Poll for completion
        max_attempts = 60  # 5 minutes with 5-second intervals
        for _ in range(max_attempts):
            status_response = await claude_status(job_id)
            status = json.loads(status_response)
            
            if status["status"] == "completed":
                result = await claude_result(job_id)
                return json.loads(result)
            elif status["status"] in ["failed", "timeout"]:
                raise Exception(f"Job failed: {status.get('error', 'Unknown error')}")
            
            await asyncio.sleep(5)
        
        # Timeout - kill the job
        await claude_kill_job(job_id)
        raise Exception("Job exceeded maximum wait time")
        
    except Exception as e:
        print(f"Error executing task: {e}")
        return None
```

## Rate Limits & Quotas

### System Limits

| Limit | Default Value | Configurable | Environment Variable |
|-------|--------------|--------------|---------------------|
| Max Recursion Depth | 3 | Yes | `CLAUDE_MAX_RECURSION_DEPTH` |
| Max Concurrent at Depth | 5 | Yes | `CLAUDE_MAX_CONCURRENT_AT_DEPTH` |
| Max Total Jobs | 20 | Yes | `CLAUDE_MAX_TOTAL_JOBS` |
| Base Timeout | 5 minutes | Yes | Via config |
| Max Timeout | 30 minutes | Yes | Via config |

### Performance Guidelines

| Metric | Recommended | Maximum |
|--------|-------------|---------|
| Concurrent Jobs | 3-5 | 10 |
| Job Duration | 30-60 seconds | 5 minutes |
| Recursion Depth | 1-2 | 3 |
| Output Size | < 1 MB | 10 MB |

## Integration Examples

### Python Client

```python
import asyncio
import json
from typing import List, Dict, Any

class ClaudeCodeClient:
    async def execute_parallel(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel"""
        # Start all jobs
        jobs = []
        for task in tasks:
            job_response = await claude_run_async(task)
            job = json.loads(job_response)
            jobs.append(job["jobId"])
        
        # Collect results
        results = []
        for job_id in jobs:
            # Wait for completion
            while True:
                status = json.loads(await claude_status(job_id))
                if status["status"] in ["completed", "failed", "timeout"]:
                    break
                await asyncio.sleep(2)
            
            # Get result
            if status["status"] == "completed":
                result = json.loads(await claude_result(job_id))
                results.append(result)
            else:
                results.append({"error": status.get("error", "Job failed")})
        
        return results
    
    async def execute_with_monitoring(self, task: str):
        """Execute task with real-time monitoring"""
        # Start job
        job = json.loads(await claude_run_async(task))
        job_id = job["jobId"]
        
        # Monitor progress
        print(f"Job {job_id} started...")
        
        while True:
            # Check status
            status = json.loads(await claude_status(job_id))
            
            # Get dashboard
            dashboard = json.loads(await claude_dashboard())
            
            print(f"Status: {status['status']}")
            print(f"Active jobs: {dashboard['activeJobs']}")
            print(f"System load: {dashboard['systemLoad']:.1f}%")
            
            if status["status"] in ["completed", "failed", "timeout"]:
                break
            
            await asyncio.sleep(5)
        
        # Get result
        if status["status"] == "completed":
            return json.loads(await claude_result(job_id))
        else:
            return {"error": status.get("error", "Job failed")}
```

### Recursive Task Example

```python
async def recursive_directory_processor():
    """Process directory tree recursively"""
    result = await claude_run("""
        import os
        import json
        
        def process_directory(path, depth=0):
            # Check recursion limit
            if depth >= 2:
                return {"path": path, "skipped": "max depth"}
            
            # Process current directory
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    # Spawn child task for subdirectory
                    child_task = f"Process directory: {item_path}"
                    # This would call claude_run recursively
                    items.append({"type": "dir", "path": item_path})
                else:
                    items.append({"type": "file", "path": item_path})
            
            return {"path": path, "items": items, "depth": depth}
        
        result = process_directory("/home/user/project")
        print(json.dumps(result, indent=2))
    """, parentJobId=None)
    
    return result
```

## Webhook Integration

While the current implementation doesn't include built-in webhook support, you can implement webhooks using the async API:

```python
from aiohttp import web
import asyncio

class WebhookServer:
    def __init__(self):
        self.jobs = {}
    
    async def handle_execute(self, request):
        """Webhook endpoint to start job"""
        data = await request.json()
        task = data.get("task")
        callback_url = data.get("callback_url")
        
        # Start job
        job = json.loads(await claude_run_async(task))
        job_id = job["jobId"]
        
        # Store callback
        self.jobs[job_id] = callback_url
        
        # Start monitoring in background
        asyncio.create_task(self.monitor_job(job_id))
        
        return web.json_response({"jobId": job_id})
    
    async def monitor_job(self, job_id):
        """Monitor job and send webhook on completion"""
        while True:
            status = json.loads(await claude_status(job_id))
            
            if status["status"] in ["completed", "failed", "timeout"]:
                # Get result
                if status["status"] == "completed":
                    result = json.loads(await claude_result(job_id))
                else:
                    result = {"error": status.get("error", "Job failed")}
                
                # Send webhook
                callback_url = self.jobs.get(job_id)
                if callback_url:
                    async with aiohttp.ClientSession() as session:
                        await session.post(callback_url, json={
                            "jobId": job_id,
                            "status": status["status"],
                            "result": result
                        })
                
                # Clean up
                del self.jobs[job_id]
                break
            
            await asyncio.sleep(5)
```

## Testing & Debugging

### Test Commands

```python
# Test basic execution
await claude_run("print('Hello World')")

# Test async execution
job = await claude_run_async("print('Async Hello')")
await claude_status(json.loads(job)["jobId"])

# Test recursion
await claude_run("""
    Use claude_run to create a nested task that prints 'Nested Hello'
""")

# Test parallel execution
jobs = []
for i in range(3):
    job = await claude_run_async(f"print('Job {i}')")
    jobs.append(json.loads(job)["jobId"])

# Test dashboard
dashboard = await claude_dashboard()
print(dashboard)

# Test error handling
try:
    await claude_result("invalid-job-id")
except Exception as e:
    print(f"Expected error: {e}")
```

### Debug Logging

Enable verbose logging for debugging:

```bash
export CLAUDE_LOG_LEVEL=TRACE
export CLAUDE_PERF_LOGGING=true
export CLAUDE_CHILD_LOGGING=true
export CLAUDE_RECURSION_LOGGING=true
```

Check logs at: `/home/opsvi/master_root/logs/claude-code/`

## Version Compatibility

| Server Version | Claude Code CLI | MCP Protocol | Python |
|---------------|-----------------|--------------|--------|
| 1.0.0 | >= 0.5.0 | 1.0 | >= 3.9 |
| 1.1.0 | >= 0.6.0 | 1.0 | >= 3.9 |
| 1.2.0 | >= 0.7.0 | 1.0 | >= 3.9 |
| 1.3.0 | >= 0.8.0 | 1.0 | >= 3.9 |