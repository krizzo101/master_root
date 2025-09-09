# Token Pool Migration Guide

## Overview

The Enhanced Token Pool eliminates contention and improves performance through:
- **Lock-free distribution** using `asyncio.Queue`
- **Token reservation system** with configurable timeouts
- **Batch allocation** for multi-agent tasks
- **Full backward compatibility** with original TokenPool

## Key Improvements

### 1. Lock-Free Token Distribution
- Replaces lock-based round-robin with `asyncio.Queue`
- Eliminates contention under high concurrency
- FIFO ordering ensures fair distribution

### 2. Token Reservation System
- Reserve tokens with timeout before confirming use
- Automatic cleanup of expired reservations
- Prevents token hoarding and deadlocks

### 3. Batch Allocation
- Allocate multiple tokens atomically for multi-agent tasks
- Rollback on partial allocation failure
- Track and release batches as a unit

### 4. Comprehensive Metrics
- Track acquisition times, usage durations, queue depths
- Monitor timeouts and batch allocations
- Built-in performance insights

## Migration Path

### Option 1: Drop-in Replacement (Minimal Changes)

```python
# Old code
from generic_orchestrator import TokenPool

# New code - just change import
from token_pool_enhanced import TokenPool  # Alias provided

# Everything else works the same
pool = TokenPool()
token, idx = await pool.acquire()
pool.release(idx)
```

### Option 2: Use Enhanced Features

```python
from token_pool_enhanced import EnhancedTokenPool

# Initialize with configuration
pool = EnhancedTokenPool(
    tokens=my_tokens,
    default_reservation_timeout=30.0,  # 30 second reservations
    enable_metrics=True
)

# Must initialize before use
await pool.initialize()

# Use reservation system
reservation = await pool.acquire_with_reservation(
    timeout=60.0,  # Custom timeout
    task_id="data_processing"
)

# Do prep work while holding reservation
await prepare_resources()

# Confirm when ready to use
token, idx = await pool.confirm_reservation(reservation.reservation_id)

# Use token for API calls
result = await call_api(token)

# Release when done
await pool._release_token(idx)

# Batch allocation for multi-agent tasks
batch = await pool.acquire_batch(
    count=5,  # Need 5 tokens
    timeout=30.0,
    batch_id="multi_agent_task"
)

# Use tokens in parallel
tasks = []
for reservation in batch:
    token, idx = await pool.confirm_reservation(reservation.reservation_id)
    tasks.append(process_with_token(token))

results = await asyncio.gather(*tasks)

# Release entire batch
await pool.release_batch("multi_agent_task")

# Get metrics
metrics = pool.get_metrics()
print(f"Average acquisition time: {metrics['avg_acquisition_time']:.3f}s")
```

## Integration with GenericOrchestrator

### Minimal Change Integration

```python
# In generic_orchestrator.py
class GenericOrchestrator:
    def __init__(self, token_pool: TokenPool = None):
        # Just replace TokenPool import
        from token_pool_enhanced import TokenPool
        self.token_pool = token_pool or TokenPool()
```

### Enhanced Integration

```python
# In generic_orchestrator.py
class GenericOrchestrator:
    async def __init__(self, token_pool: EnhancedTokenPool = None):
        from token_pool_enhanced import EnhancedTokenPool

        self.token_pool = token_pool or EnhancedTokenPool(
            default_reservation_timeout=60.0,
            enable_metrics=True
        )
        await self.token_pool.initialize()

    async def execute_batch_agents(self, tasks: List[AgentTask]):
        """Execute multiple agents with batch token allocation"""
        # Reserve tokens for all agents upfront
        batch_id = f"batch_{uuid.uuid4()}"
        reservations = await self.token_pool.acquire_batch(
            count=len(tasks),
            timeout=120.0,
            batch_id=batch_id
        )

        try:
            # Execute agents in parallel with reserved tokens
            agent_tasks = []
            for task, reservation in zip(tasks, reservations):
                token, idx = await self.token_pool.confirm_reservation(
                    reservation.reservation_id
                )
                agent_tasks.append(self.execute_agent_with_token(task, token))

            results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            return results

        finally:
            # Always release batch
            await self.token_pool.release_batch(batch_id)
```

## Performance Comparison

### Before (Lock-based)
- **Contention**: High under concurrent load
- **Fairness**: Round-robin, but with lock overhead
- **Batch ops**: Sequential token acquisition
- **Metrics**: None built-in

### After (Lock-free Queue)
- **Contention**: Near-zero with asyncio.Queue
- **Fairness**: True FIFO ordering
- **Batch ops**: Atomic batch allocation
- **Metrics**: Comprehensive performance tracking

## Testing

Run comprehensive tests:
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
python -m pytest tests/test_token_pool_enhanced.py -v
```

## Monitoring

Access metrics during runtime:
```python
metrics = pool.get_metrics()
print(json.dumps(metrics, indent=2))
```

Example output:
```json
{
  "total_tokens": 10,
  "available_tokens": 7,
  "reserved_tokens": 1,
  "in_use_tokens": 2,
  "total_acquisitions": 1543,
  "total_releases": 1541,
  "total_reservations": 1543,
  "total_timeouts": 3,
  "total_batch_allocations": 45,
  "avg_acquisition_time": 0.0012,
  "avg_usage_duration": 2.341,
  "current_queue_depth": 7
}
```

## Troubleshooting

### Issue: Tokens not being released
**Solution**: Ensure you're awaiting release operations or using the cleanup task

### Issue: Reservation timeouts
**Solution**: Increase `default_reservation_timeout` or use custom timeout per reservation

### Issue: Batch allocation fails
**Solution**: Check available token count before requesting batch

### Issue: High acquisition times
**Solution**: Check metrics for queue depth, consider adding more tokens

## Best Practices

1. **Always initialize**: Call `await pool.initialize()` before use
2. **Use reservations**: For long-running preparations before API calls
3. **Batch wisely**: Group related agents for atomic token allocation
4. **Monitor metrics**: Track performance and identify bottlenecks
5. **Clean shutdown**: Call `await pool.shutdown()` when done
6. **Handle timeouts**: Implement retry logic for expired reservations

## Future Enhancements

Potential improvements for v2:
- Priority queue for urgent tasks
- Token health monitoring and rotation
- Distributed token pool across processes
- ML-based predictive token allocation
- Integration with rate limit detection
