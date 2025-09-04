# Dynamic Token Pool - Smart Token Allocation

## The Smart Approach

Instead of hard limits, the Dynamic Token Pool:

1. **Single agent gets ALL tokens** (18 now, 50+ soon!)
2. **New agents wait for tokens** as tasks complete
3. **Gradual rebalancing** to fair share (50/50, 33/33/33, etc.)
4. **Automatic cleanup** when agents finish

## How It Works

### Scenario 1: Single Agent Running
```
Agent A starts:
- Gets all 18 tokens
- Runs 18 tasks in parallel
- Maximum speed!
```

### Scenario 2: Second Agent Starts
```
Agent A: Running with 18 tokens
Agent B starts:
- Waits for Agent A's tasks to complete
- As each task finishes, token goes to Agent B
- Eventually reaches 9/9 split
```

### Scenario 3: One Agent Finishes
```
Agent A: 9 tokens
Agent B: 9 tokens
Agent A finishes:
- All 9 tokens return to pool
- Agent B picks them up
- Agent B now has 18 tokens
```

## Integration with Orchestrator

### Method 1: Token-Aware Orchestrator (Recommended)

```python
from dynamic_token_pool import DynamicTokenPool
from generic_orchestrator import GenericOrchestrator

class SmartOrchestrator(GenericOrchestrator):
    def __init__(self, output_dir):
        self.pool = DynamicTokenPool()

        # Request all available tokens
        tokens = self.pool.request_tokens()

        super().__init__(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=len(tokens)
        )

        print(f"Starting with {len(tokens)} tokens")

    async def execute_agent(self, task):
        """Override to release tokens as tasks complete"""
        result = await super().execute_agent(task)

        # Release token back to pool for rebalancing
        # This allows waiting agents to grab it
        # We'll request it back if we need it

        return result

    def __del__(self):
        """Release all tokens on cleanup"""
        self.pool.release_all()

# Usage
orchestrator = SmartOrchestrator(output_dir=Path("/tmp/project"))
# Automatically gets all available tokens!
```

### Method 2: Simple Usage

```python
from dynamic_token_pool import get_dynamic_tokens
from generic_orchestrator import GenericOrchestrator

# Get tokens (all if alone, fair share if not)
tokens = get_dynamic_tokens()

orchestrator = GenericOrchestrator(
    output_dir=Path("/tmp/project"),
    tokens=tokens,
    max_parallel=len(tokens)
)

print(f"Got {len(tokens)} tokens")
# First agent: 18 tokens
# Second agent (if one running): starts with 0, gradually gets 9
```

### Method 3: Adaptive Orchestrator

```python
from dynamic_token_pool import DynamicTokenPool
import asyncio

class AdaptiveOrchestrator:
    """Orchestrator that adapts to changing token availability"""

    def __init__(self, output_dir):
        self.pool = DynamicTokenPool()
        self.output_dir = output_dir
        self.running_tasks = {}

    async def run_with_rebalancing(self, all_tasks):
        """Run tasks, adapting to token availability"""

        pending_tasks = all_tasks.copy()
        completed = []

        while pending_tasks or self.running_tasks:
            # Request tokens (may get more as others release)
            tokens = self.pool.request_tokens()

            # Start new tasks if we have tokens
            while tokens and pending_tasks:
                task = pending_tasks.pop(0)
                token = tokens.pop(0)

                # Start task with token
                future = asyncio.create_task(
                    self.execute_with_token(task, token)
                )
                self.running_tasks[future] = (task, token)

            # Wait for any task to complete
            if self.running_tasks:
                done, pending = await asyncio.wait(
                    self.running_tasks.keys(),
                    return_when=asyncio.FIRST_COMPLETED
                )

                for future in done:
                    task, token = self.running_tasks.pop(future)
                    result = await future
                    completed.append(result)

                    # Token automatically available for reallocation

            await asyncio.sleep(0.1)  # Brief pause

        return completed
```

## Monitoring Token Distribution

### Check Pool Status

```bash
# Command line status check
python3 /home/opsvi/master_root/apps/agent-orchestrator/src/dynamic_token_pool.py status
```

Output:
```
Dynamic Token Pool Status:
  Total tokens: 18
  In use: 18
  Available: 0
  Active instances: 2

Distribution:
  pid_12345_1234567: 9 tokens (50.0%) - PID 12345
  pid_67890_1234568: 9 tokens (50.0%) - PID 67890
```

### Programmatic Status

```python
from dynamic_token_pool import DynamicTokenPool

pool = DynamicTokenPool()
status = pool.get_status()

print(f"I have {status['my_tokens']} tokens")
print(f"Total {status['instances']} agents running")
print(f"Available tokens: {status['available']}")
```

## Scaling to 50+ Tokens

The system automatically scales:

### With 50 tokens:
- **1 agent**: Gets all 50 tokens!
- **2 agents**: 25 each
- **5 agents**: 10 each
- **10 agents**: 5 each

### Dynamic Adjustment Example:
```
Time 0: Agent A starts → 50 tokens
Time 1: Agent B starts → A: 50, B: 0 (waiting)
Time 2: A's task completes → A: 49, B: 1
Time 3: More tasks complete → A: 40, B: 10
Time 4: Equilibrium → A: 25, B: 25
Time 5: Agent B finishes → A: 50, B: 0
```

## Best Practices

### 1. Don't Hold Tokens Idle
```python
# Bad: Request tokens but don't use them
tokens = pool.request_tokens()
time.sleep(60)  # Holding tokens idle!

# Good: Release if not actively using
tokens = pool.request_tokens()
if not ready_to_execute:
    pool.release_all()
```

### 2. Clean Shutdown
```python
pool = DynamicTokenPool()
try:
    tokens = pool.request_tokens()
    # Do work
finally:
    pool.release_all()  # Always cleanup
```

### 3. Handle Variable Token Counts
```python
# Your task count might exceed available tokens
tasks = [... 30 tasks ...]
tokens = pool.request_tokens()

# Adjust parallelism to available tokens
orchestrator = GenericOrchestrator(
    output_dir=output_dir,
    tokens=tokens,
    max_parallel=len(tokens)  # Could be 1 to 50!
)
```

## Advanced: Token Lifecycle Hooks

For fine-grained control:

```python
class TokenAwareOrchestrator(GenericOrchestrator):
    def __init__(self, output_dir):
        self.pool = DynamicTokenPool()
        self.token_task_map = {}
        super().__init__(output_dir=output_dir)

    async def execute_agent(self, task):
        # Check current token availability
        tokens = self.pool.request_tokens()

        if not tokens:
            # Wait for tokens
            while not tokens:
                await asyncio.sleep(1)
                tokens = self.pool.request_tokens()

        # Use first available token
        token = tokens[0]

        try:
            # Execute task
            result = await self._run_with_token(task, token)
            return result
        finally:
            # Release this specific token for others
            self.pool.release_token(0)
```

## Troubleshooting

### Issue: Second agent gets no tokens
- **Cause**: First agent's tasks are long-running
- **Solution**: Tasks complete → tokens redistribute

### Issue: Tokens not rebalancing
- **Check**: Are tasks actually completing?
- **Check**: Is first agent releasing tokens?
- **Debug**: Check `/tmp/token_locks/pool_state.json`

### Issue: Dead instance holding tokens
- **Automatic**: Cleaned up after 10 minutes
- **Manual**: Delete `/tmp/token_locks/pool_state.json`

## Summary

The Dynamic Pool ensures:
- **Maximum parallelism** when running alone
- **Fair sharing** when multiple agents run
- **Automatic rebalancing** as tasks complete
- **Scales perfectly** from 18 to 50+ tokens

No tokens wasted, maximum efficiency!
