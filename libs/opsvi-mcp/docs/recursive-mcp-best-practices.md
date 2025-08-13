# Recursive MCP Best Practices & Error Prevention

## Common Error: Tool Result Protocol Violation

### Error Message
```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"messages.61: `tool_use` ids were found without `tool_result` blocks immediately after: [tool_id]. Each `tool_use` block must have a corresponding `tool_result` block in the next message."}}
```

### Root Cause
This error occurs when:
1. Tool calls are initiated but results aren't properly handled
2. Multiple async operations run without proper result collection
3. Session attempts to continue without awaiting tool completions

## Prevention Strategies

### 1. Always Await Async Results
```python
# BAD - Can cause protocol violations
job1 = claude_run_async(task="analyze project A")
job2 = claude_run_async(task="analyze project B")
# Continuing without getting results...

# GOOD - Properly handle async operations
job1 = claude_run_async(task="analyze project A")
job2 = claude_run_async(task="analyze project B")

# Always check status and get results
status1 = claude_status(jobId=job1['jobId'])
status2 = claude_status(jobId=job2['jobId'])

# Wait for completion
while status1['status'] != 'completed':
    time.sleep(5)
    status1 = claude_status(jobId=job1['jobId'])

result1 = claude_result(jobId=job1['jobId'])
```

### 2. Use Synchronous Calls for Critical Operations
```python
# For operations that must complete before continuing
result = claude_run(task="critical analysis", outputFormat="json")
# Process result immediately
```

### 3. Implement Proper Error Handling
```python
async def safe_recursive_execution(tasks):
    jobs = []
    
    # Start all async jobs
    for task in tasks:
        try:
            job = await claude_run_async(task=task)
            jobs.append(job)
        except Exception as e:
            log_error(f"Failed to start job: {e}")
            
    # Collect all results with timeout
    results = []
    for job in jobs:
        try:
            result = await wait_for_completion(job['jobId'], timeout=300)
            results.append(result)
        except TimeoutError:
            # Handle timeout gracefully
            claude_kill_job(jobId=job['jobId'])
            
    return results
```

### 4. Use Status Monitoring Pattern
```python
def monitor_jobs(job_ids, check_interval=10):
    """Monitor multiple jobs and return when all complete"""
    completed = set()
    results = {}
    
    while len(completed) < len(job_ids):
        for job_id in job_ids:
            if job_id in completed:
                continue
                
            status = claude_status(jobId=job_id)
            
            if status['status'] == 'completed':
                results[job_id] = claude_result(jobId=job_id)
                completed.add(job_id)
            elif status['status'] == 'failed':
                completed.add(job_id)
                results[job_id] = {'error': status.get('error', 'Unknown error')}
                
        if len(completed) < len(job_ids):
            time.sleep(check_interval)
            
    return results
```

## Agent Profile Design for Recursive MCP

### Research Agent Profile
```yaml
profile:
  name: research-agent
  type: claude_run_async
  capabilities:
    - file_analysis
    - code_understanding
    - pattern_recognition
  
  configuration:
    outputFormat: json
    permissionMode: bypassPermissions
    timeout: 300
    
  reporting_template:
    summary:
      type: string
      maxLength: 500
    findings:
      type: array
      items:
        - category: string
        - insight: string
        - evidence: array
    recommendations:
      type: array
      maxLength: 5
```

### Implementation Agent Profile
```yaml
profile:
  name: implementation-agent
  type: claude_run
  capabilities:
    - code_generation
    - file_modification
    - testing
    
  configuration:
    outputFormat: json
    permissionMode: default
    requireConfirmation: true
    
  reporting_template:
    files_modified:
      type: array
    tests_added:
      type: array
    validation_results:
      type: object
```

### Orchestrator Agent Profile
```yaml
profile:
  name: orchestrator-agent
  type: master
  capabilities:
    - task_decomposition
    - agent_spawning
    - result_synthesis
    
  workflow:
    - analyze_complexity
    - decompose_tasks
    - assign_agents
    - monitor_progress
    - synthesize_results
    
  child_agent_management:
    max_concurrent: 5
    timeout_per_agent: 300
    retry_on_failure: true
    fallback_strategy: sequential
```

## Standardized Reporting Format

### Universal Agent Report Structure
```json
{
  "agent": {
    "id": "unique-agent-id",
    "type": "research|implementation|review|test",
    "parent_id": "parent-agent-id",
    "depth": 0
  },
  "task": {
    "original": "Full task description",
    "interpreted": "Agent's understanding",
    "complexity": "low|medium|high|extreme"
  },
  "execution": {
    "start_time": "ISO-8601",
    "end_time": "ISO-8601",
    "status": "success|partial|failed",
    "tools_used": ["tool1", "tool2"],
    "files_accessed": ["file1", "file2"]
  },
  "results": {
    "summary": "Executive summary",
    "details": {},
    "artifacts": [],
    "metrics": {
      "lines_analyzed": 0,
      "patterns_found": 0,
      "recommendations": 0
    }
  },
  "child_agents": [
    {
      "id": "child-id",
      "task": "subtask",
      "status": "completed"
    }
  ],
  "errors": [],
  "warnings": []
}
```

## Workflow Patterns

### 1. Parallel Research Pattern
```python
async def parallel_research(topics):
    """Execute parallel research on multiple topics"""
    
    agents = []
    for topic in topics:
        agent_task = {
            "task": f"Research: {topic}",
            "profile": "research-agent",
            "reporting": "standardized",
            "timeout": 300
        }
        agents.append(claude_run_async(**agent_task))
    
    # Monitor and collect
    results = await monitor_all_agents(agents)
    
    # Synthesize findings
    synthesis = await synthesize_research(results)
    
    return synthesis
```

### 2. Sequential Validation Pattern
```python
def sequential_validation(implementation):
    """Validate implementation through multiple stages"""
    
    stages = [
        {"agent": "syntax-validator", "critical": True},
        {"agent": "security-scanner", "critical": True},
        {"agent": "performance-analyzer", "critical": False},
        {"agent": "documentation-checker", "critical": False}
    ]
    
    for stage in stages:
        result = claude_run(
            task=f"Validate: {stage['agent']}",
            target=implementation
        )
        
        if stage['critical'] and result['status'] == 'failed':
            return {"validation": "failed", "stage": stage['agent']}
    
    return {"validation": "passed", "reports": collect_reports()}
```

### 3. Recursive Decomposition Pattern
```python
def recursive_decomposition(task, max_depth=3, current_depth=0):
    """Recursively decompose complex tasks"""
    
    if current_depth >= max_depth:
        return execute_atomic_task(task)
    
    # Analyze complexity
    complexity = analyze_task_complexity(task)
    
    if complexity['score'] < 0.3:
        return execute_atomic_task(task)
    
    # Decompose
    subtasks = decompose_task(task)
    
    # Recurse
    results = []
    for subtask in subtasks:
        result = recursive_decomposition(
            subtask, 
            max_depth, 
            current_depth + 1
        )
        results.append(result)
    
    return synthesize_results(results)
```

## Error Recovery Mechanisms

### 1. Graceful Degradation
```python
async def execute_with_fallback(task, strategies):
    """Execute task with fallback strategies"""
    
    for strategy in strategies:
        try:
            if strategy['type'] == 'parallel':
                return await parallel_execution(task)
            elif strategy['type'] == 'sequential':
                return sequential_execution(task)
            elif strategy['type'] == 'single':
                return direct_execution(task)
        except Exception as e:
            log_error(f"Strategy {strategy['type']} failed: {e}")
            continue
    
    return {"status": "failed", "tried": strategies}
```

### 2. Checkpoint Recovery
```python
class CheckpointedExecution:
    def __init__(self, task):
        self.task = task
        self.checkpoints = []
        
    def save_checkpoint(self, state):
        self.checkpoints.append({
            'timestamp': datetime.now(),
            'state': state
        })
        
    def recover_from_last(self):
        if self.checkpoints:
            return self.checkpoints[-1]['state']
        return None
```

### 3. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.is_open = False
        
    def call(self, func, *args, **kwargs):
        if self.is_open:
            if (datetime.now() - self.last_failure).seconds > self.timeout:
                self.is_open = False
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                
            raise e
```

## Best Practices Summary

1. **Always handle async operations properly** - Wait for results before continuing
2. **Use appropriate execution modes** - Sync for critical, async for parallel
3. **Implement timeout mechanisms** - Prevent hanging operations
4. **Standardize reporting** - Ensure consistent output from all agents
5. **Plan for failure** - Have fallback strategies and error recovery
6. **Monitor resource usage** - Track concurrent agents and system load
7. **Use circuit breakers** - Prevent cascade failures
8. **Implement checkpointing** - Allow recovery from partial completion
9. **Validate before proceeding** - Check prerequisites before spawning agents
10. **Log everything** - Maintain audit trail for debugging

## Quick Fixes for Common Issues

### Issue: Tool result protocol violation
**Fix**: Always await async results before continuing

### Issue: Session timeout
**Fix**: Implement heartbeat monitoring for long-running tasks

### Issue: Memory overflow from large results
**Fix**: Use streaming or pagination for large datasets

### Issue: Circular dependencies in recursive calls
**Fix**: Implement depth limits and cycle detection

### Issue: Lost child agent results
**Fix**: Use persistent job tracking with unique IDs