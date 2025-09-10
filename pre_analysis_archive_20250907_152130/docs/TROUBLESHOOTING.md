# Troubleshooting Guide

## Common Issues and Solutions

### 1. "No Claude tokens available"

**Error Message:**
```
ValueError: No Claude tokens available. Please set CLAUDE_CODE_TOKEN environment variable
```

**Cause:** The CLAUDE_CODE_TOKEN environment variable is not set.

**Solution:**
```bash
# Set your token
export CLAUDE_CODE_TOKEN='your-token-here'

# Verify it's set
echo $CLAUDE_CODE_TOKEN
```

**Permanent Fix:**
Add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
export CLAUDE_CODE_TOKEN='your-token-here'
```

---

### 2. "Invalid session ID"

**Error Message:**
```
Error: Invalid session ID. Must be a valid UUID.
```

**Cause:** Session ID format was incorrect (fixed in latest version).

**Solution:**
Ensure you're using the latest version of `generic_orchestrator.py`. The session ID should be generated as:
```python
session_id = str(uuid.uuid4())  # Correct
# NOT: session_id = f"{task_id}_{uuid.uuid4().hex[:8]}"  # Wrong
```

---

### 3. "claude: command not found"

**Error Message:**
```
claude: command not found
```

**Cause:** Claude CLI is not installed or not in PATH.

**Solution:**
1. Install Claude CLI:
```bash
# Check installation guide at:
# https://claude.ai/cli
```

2. Verify installation:
```bash
which claude
claude --version
```

3. Add to PATH if needed:
```bash
export PATH="$PATH:/path/to/claude/bin"
```

---

### 4. Tasks Stuck as "Pending"

**Symptom:** Tasks remain in pending state and never execute.

**Possible Causes:**
1. Circular dependencies
2. Missing dependencies
3. No available tokens

**Diagnosis:**
```python
# Add debug logging
async def debug_dependencies(task: AgentTask):
    print(f"Task {task.task_id} waiting for: {task.dependencies}")

orchestrator.pre_execute_hook = debug_dependencies
```

**Solutions:**
1. Check dependency graph:
```python
def validate_dependencies(tasks):
    task_ids = {t.task_id for t in tasks}
    for task in tasks:
        for dep in task.dependencies:
            if dep not in task_ids:
                print(f"ERROR: {task.task_id} depends on non-existent {dep}")
```

2. Visualize dependencies:
```python
def print_dependency_graph(tasks):
    for task in tasks:
        deps = " → ".join(task.dependencies) if task.dependencies else "None"
        print(f"{task.task_id}: {deps}")
```

---

### 5. "Possible deadlock detected"

**Error Message:**
```
WARNING: Possible deadlock detected
```

**Cause:** Tasks have unresolvable dependencies.

**Common Scenarios:**
1. Circular dependency: A → B → A
2. Missing task: A depends on B, but B doesn't exist
3. Failed dependency: A depends on B, but B failed

**Solution:**
```python
# Break circular dependencies
# Instead of: A → B → C → A
# Use: A → B → C, then A2 → C

# Handle failed dependencies
if task.dependencies:
    for dep in task.dependencies:
        if dep_status[dep] == "failed":
            task.status = "skipped"
            task.error = f"Dependency {dep} failed"
```

---

### 6. Slow Execution Times

**Symptom:** Tasks take much longer than expected.

**Causes:**
1. Not using optimizations
2. Using wrong model
3. Complex prompts

**Solutions:**

1. Enable optimizations:
```python
orchestrator = GenericOrchestrator(
    use_optimizations=True  # Essential for speed
)
```

2. Use appropriate model:
```python
# For simple tasks (fastest)
cmd.extend(["--model", "sonnet"])

# For complex tasks (slower but better)
cmd.extend(["--model", "opus"])
```

3. Optimize prompts:
```python
# Bad: Very long, complex prompt
prompt = "First, research... then analyze... then create... then optimize..."

# Good: Focused, single-purpose
prompt = "List the top 5 features of Python"
```

---

### 7. JSON Parsing Errors

**Error Message:**
```
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** Claude returned non-JSON output or an error.

**Solution:**
```python
try:
    result = json.loads(stdout.decode())
except json.JSONDecodeError:
    # Fall back to text result
    result = {
        "type": "text",
        "content": stdout.decode(),
        "error": "Non-JSON response"
    }
```

---

### 8. File Permission Errors

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: 'output/tasks/task.json'
```

**Cause:** Output directory has incorrect permissions.

**Solution:**
```bash
# Fix permissions
chmod -R 755 output/

# Or recreate directory
rm -rf output/
mkdir -p output/tasks output/logs
```

---

### 9. Token Pool Exhaustion

**Symptom:** Only one task runs at a time despite max_parallel > 1.

**Cause:** Only one token available.

**Solution:**
```python
# Add more tokens
tokens = [
    os.environ.get('CLAUDE_TOKEN_1'),
    os.environ.get('CLAUDE_TOKEN_2'),
    os.environ.get('CLAUDE_TOKEN_3'),
]

orchestrator = GenericOrchestrator(
    tokens=[t for t in tokens if t],  # Filter None values
    max_parallel=len(tokens)
)
```

---

### 10. Memory Issues with Large Orchestrations

**Symptom:** Process runs out of memory with many tasks.

**Solutions:**

1. Batch processing:
```python
def batch_tasks(all_tasks, batch_size=50):
    for i in range(0, len(all_tasks), batch_size):
        batch = all_tasks[i:i + batch_size]
        yield batch

for batch in batch_tasks(large_task_list):
    await orchestrator.execute_batch(batch)
```

2. Clear completed tasks:
```python
async def clear_completed(task: AgentTask):
    if task.status == "completed":
        # Save result to disk and clear from memory
        save_to_disk(task)
        task.result = None  # Free memory
```

3. Use streaming for large outputs:
```python
# Future enhancement: Stream results to file
# instead of keeping in memory
```

---

## Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging

# Set to DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or just for orchestrator
logger = logging.getLogger('generic_orchestrator')
logger.setLevel(logging.DEBUG)
```

---

## Performance Diagnostics

### Check Execution Times

```python
async def time_analysis(results):
    for r in results:
        if r.get('start_time') and r.get('end_time'):
            duration = r['end_time'] - r['start_time']
            print(f"{r['task_id']}: {duration:.2f}s")

    avg_time = sum(r['end_time'] - r['start_time'] for r in results) / len(results)
    print(f"Average: {avg_time:.2f}s")
```

### Monitor Resource Usage

```bash
# Watch memory usage
watch -n 1 'ps aux | grep python'

# Monitor file creation
watch -n 1 'ls -la output/tasks/ | wc -l'

# Check Claude processes
ps aux | grep claude
```

---

## Getting Help

### 1. Check Logs
```bash
# View recent errors
tail -f output/logs/*.log

# Check session logs
ls -la ~/.claude/projects/*/
```

### 2. Validate Setup
```bash
# Run setup script
./setup.sh

# Test with simple task
python3 -c "
from src.generic_orchestrator import GenericOrchestrator, AgentTask
import asyncio

async def test():
    o = GenericOrchestrator(output_dir='./test')
    t = AgentTask(task_id='test', task_type='test', prompt='Say hello')
    await o.execute_agent(t)

asyncio.run(test())
"
```

### 3. Environment Info
```bash
# Collect diagnostic info
echo "Python: $(python3 --version)"
echo "Claude: $(claude --version 2>&1)"
echo "Token: ${CLAUDE_CODE_TOKEN:0:10}..."
echo "Path: $PATH"
echo "OS: $(uname -a)"
```

---

## Prevention Tips

1. **Always run setup first**: `./setup.sh`
2. **Use try-except blocks** in production code
3. **Validate dependencies** before running
4. **Start small**: Test with 2-3 tasks before scaling
5. **Monitor resources**: Watch memory and disk usage
6. **Keep logs**: Save outputs for debugging
7. **Use appropriate timeouts**: Prevent hanging tasks
8. **Document your orchestrations**: Comment complex flows

---

## Known Limitations

1. **No built-in retry logic** - Must implement manually
2. **No progress bars** - Use hooks for progress tracking
3. **No task cancellation** - Once started, tasks run to completion
4. **Limited to CLI interface** - No API client support yet
5. **No distributed execution** - Single machine only

These may be addressed in future versions.
