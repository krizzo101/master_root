# Shared Token Pool - Preventing Token Hoarding

## The Problem
With 18 tokens available, if one orchestrator uses all of them, other agents/orchestrators can't run in parallel.

## The Solution: Shared Token Pool

The `SharedTokenPool` class ensures fair token distribution:

### Key Features:
1. **Maximum 5 tokens per orchestrator instance** (configurable)
2. **Automatic cleanup** of abandoned tokens (10 minute timeout)
3. **File-based locking** for coordination between processes
4. **Process monitoring** to detect dead instances

## Usage Options

### Option 1: Direct Token Pool Usage (Recommended)

```python
from shared_token_pool import SharedTokenPool

# Create a shared pool with max 5 tokens per instance
pool = SharedTokenPool(max_tokens_per_instance=5)

# Acquire tokens
my_tokens = pool.acquire_tokens(requested=3)  # Get up to 3 tokens
print(f"Got {len(my_tokens)} tokens")

# Use tokens with orchestrator
orchestrator = GenericOrchestrator(
    output_dir=Path("/tmp/project"),
    tokens=my_tokens,  # Use only allocated tokens
    max_parallel=len(my_tokens)
)

# ... do work ...

# Release tokens when done
pool.release_tokens()
```

### Option 2: Context Manager (Auto-release)

```python
from shared_token_pool import SharedTokenPool

pool = SharedTokenPool(max_tokens_per_instance=5)

# Tokens automatically released when done
with pool as tokens:
    orchestrator = GenericOrchestrator(
        output_dir=Path("/tmp/project"),
        tokens=tokens,
        max_parallel=len(tokens)
    )
    # ... do work ...
# Tokens released here automatically
```

### Option 3: Modified Orchestrator (Easiest)

```python
from generic_orchestrator import GenericOrchestrator
from shared_token_pool import get_shared_tokens

# Orchestrator that uses shared pool
class FairOrchestrator(GenericOrchestrator):
    def __init__(self, output_dir, max_tokens=5):
        # Get tokens from shared pool
        tokens = get_shared_tokens(max_tokens)
        super().__init__(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=len(tokens)
        )
        self.shared_pool = SharedTokenPool()

    def __del__(self):
        # Release tokens on cleanup
        self.shared_pool.release_tokens()

# Use it
orchestrator = FairOrchestrator(
    output_dir=Path("/tmp/project"),
    max_tokens=5  # Request up to 5 tokens
)
```

## Configuration

### Token Limits per Instance

Different limits for different use cases:

```python
# Small tasks - 3 tokens max
pool = SharedTokenPool(max_tokens_per_instance=3)

# Medium tasks - 5 tokens max (default)
pool = SharedTokenPool(max_tokens_per_instance=5)

# Large tasks - 8 tokens max
pool = SharedTokenPool(max_tokens_per_instance=8)

# Critical task - 10 tokens max
pool = SharedTokenPool(max_tokens_per_instance=10)
```

### Token Timeout

Tokens are automatically released after timeout:

```python
# Default: 10 minutes
pool = SharedTokenPool(token_timeout=600)

# Quick tasks: 5 minutes
pool = SharedTokenPool(token_timeout=300)

# Long tasks: 30 minutes
pool = SharedTokenPool(token_timeout=1800)
```

## Monitoring Token Usage

### Check Pool Status

```python
from shared_token_pool import SharedTokenPool

pool = SharedTokenPool()
status = pool.get_status()

print(f"Total tokens: {status['total_tokens']}")  # 18
print(f"Available: {status['available_tokens']}")
print(f"Used: {status['used_tokens']}")
print(f"Active instances: {status['active_instances']}")

# Detailed view
for instance, details in status['instance_details'].items():
    print(f"Instance {instance}: {details['tokens']} tokens, age: {details['age_seconds']}s")
```

### Command Line Check

```bash
python3 /home/opsvi/master_root/apps/agent-orchestrator/src/shared_token_pool.py
```

## Token Allocation Strategy

With 18 tokens available:

| Scenario | Instances | Tokens Each | Total Used |
|----------|-----------|-------------|------------|
| Many small tasks | 6 | 3 | 18 |
| Balanced load | 3-4 | 5 | 15-20* |
| Few large tasks | 2 | 8 | 16 |
| Single critical | 1 | 15 | 15 |

*Some instances may get 4 tokens if 18 doesn't divide evenly

## Best Practices

### 1. Release Tokens Promptly
```python
pool = SharedTokenPool()
tokens = pool.acquire_tokens()
try:
    # Do work
    pass
finally:
    pool.release_tokens()  # Always release
```

### 2. Request Only What You Need
```python
# For 3 parallel tasks, request 3 tokens
tokens = pool.acquire_tokens(requested=3)
```

### 3. Handle Token Shortage
```python
tokens = pool.acquire_tokens(requested=5)
if len(tokens) < 3:  # Minimum needed
    print(f"Warning: Only got {len(tokens)} tokens")
    # Adjust parallelism or wait
```

### 4. Monitor Token Health
```python
status = pool.get_status()
if status['available_tokens'] == 0:
    print("All tokens in use, consider waiting...")
```

## Example: Multiple Orchestrators

```python
# Agent 1: Documentation builder
pool1 = SharedTokenPool()
tokens1 = pool1.acquire_tokens(3)  # Gets 3 tokens
doc_orchestrator = GenericOrchestrator(tokens=tokens1)

# Agent 2: Test runner (different process)
pool2 = SharedTokenPool()
tokens2 = pool2.acquire_tokens(5)  # Gets 5 tokens
test_orchestrator = GenericOrchestrator(tokens=tokens2)

# Agent 3: Code analyzer (different process)
pool3 = SharedTokenPool()
tokens3 = pool3.acquire_tokens(5)  # Gets 5 tokens
analyzer_orchestrator = GenericOrchestrator(tokens=tokens3)

# Total: 13 tokens used, 5 available for other agents
```

## Troubleshooting

### Issue: "No tokens available"
- Check pool status: `pool.get_status()`
- Look for stuck instances holding tokens
- Check `/tmp/token_locks/token_allocations.json`

### Issue: Tokens not released
- Process may have crashed
- Wait for timeout (default 10 minutes)
- Or manually clean: `rm /tmp/token_locks/token_allocations.json`

### Issue: Need more than 5 tokens
- Adjust limit: `SharedTokenPool(max_tokens_per_instance=8)`
- But be considerate of other agents!

## Summary

The shared token pool ensures:
- **Fair distribution** - No single agent monopolizes tokens
- **Automatic cleanup** - Dead processes don't hold tokens forever
- **Flexibility** - Configure limits based on needs
- **Visibility** - Monitor who's using what

This prevents the token hoarding problem while maintaining high parallelism!
