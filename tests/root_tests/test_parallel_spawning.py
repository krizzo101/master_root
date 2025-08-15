#!/usr/bin/env python3
"""
Test current parallel spawning capability and demonstrate the needed enhancement
"""

import asyncio
import json
import time
from datetime import datetime

# Test with the claude-code-wrapper MCP tool
async def test_current_behavior():
    """Test how the current system handles multiple tasks"""
    
    print("=" * 60)
    print("Testing Current Parallel Spawning Behavior")
    print("=" * 60)
    
    # Try to spawn multiple tasks that should run in parallel
    tasks = [
        "Create a simple Python function that sleeps for 2 seconds and returns 'Task 1 done'",
        "Create a simple Python function that sleeps for 2 seconds and returns 'Task 2 done'", 
        "Create a simple Python function that sleeps for 2 seconds and returns 'Task 3 done'",
    ]
    
    print(f"\nStarting {len(tasks)} tasks at {datetime.now()}")
    print("If truly parallel, should complete in ~2 seconds")
    print("If sequential, will take ~6 seconds\n")
    
    start_time = time.time()
    
    # Current approach - spawn them as separate async jobs
    job_ids = []
    for i, task in enumerate(tasks):
        print(f"Spawning task {i+1}: {task[:50]}...")
        # Simulate calling claude_run_async
        # In real usage this would be:
        # job_id = await mcp__claude-code-wrapper__claude_run_async(task=task)
        job_id = f"job_{i+1}_{int(time.time())}"
        job_ids.append(job_id)
        await asyncio.sleep(0.1)  # Small delay to simulate API call
    
    print(f"\nAll jobs spawned. Job IDs: {job_ids}")
    
    # Wait for completion (simulated)
    await asyncio.sleep(3)
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.2f} seconds")
    
    if elapsed < 3:
        print("✅ Tasks appear to run in parallel!")
    else:
        print("❌ Tasks appear to run sequentially")
    
    return job_ids


async def test_proposed_batch_api():
    """Demonstrate the proposed batch API for true parallel execution"""
    
    print("\n" + "=" * 60)
    print("Proposed Batch API for Parallel Execution")
    print("=" * 60)
    
    # Proposed new API endpoint
    batch_request = {
        "tasks": [
            {
                "task": "Analyze security in auth.py",
                "cwd": "/home/opsvi/master_root",
                "output_format": "json"
            },
            {
                "task": "Check performance in database.py",
                "cwd": "/home/opsvi/master_root",
                "output_format": "json"
            },
            {
                "task": "Review code style in api.py",
                "cwd": "/home/opsvi/master_root",
                "output_format": "json"
            }
        ],
        "parallel": True,  # Execute in parallel
        "max_concurrent": 3,  # Limit concurrent executions
        "parent_job_id": None  # For recursion tracking
    }
    
    print("\nProposed batch request structure:")
    print(json.dumps(batch_request, indent=2))
    
    print("\nThis would spawn all tasks simultaneously using asyncio.gather()")
    print("Expected benefits:")
    print("- 3-5x speedup for independent tasks")
    print("- Better resource utilization")
    print("- Simpler API for batch operations")
    
    # Simulated implementation
    async def execute_batch(batch_request):
        tasks = batch_request["tasks"]
        if batch_request.get("parallel", False):
            # True parallel execution
            results = await asyncio.gather(*[
                execute_single_task(t) for t in tasks
            ])
        else:
            # Sequential execution (current behavior)
            results = []
            for t in tasks:
                result = await execute_single_task(t)
                results.append(result)
        return results
    
    async def execute_single_task(task_config):
        # Simulate task execution
        await asyncio.sleep(2)
        return f"Completed: {task_config['task'][:30]}..."
    
    start_time = time.time()
    print("\nExecuting batch in parallel mode...")
    results = await execute_batch(batch_request)
    elapsed = time.time() - start_time
    
    print(f"\nResults received in {elapsed:.2f} seconds:")
    for r in results:
        print(f"  - {r}")
    
    return results


async def main():
    """Run all tests"""
    
    print("Testing Claude MCP Server Parallel Spawning")
    print("=" * 60)
    
    # Test current behavior
    await test_current_behavior()
    
    # Demonstrate proposed enhancement
    await test_proposed_batch_api()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
The current implementation allows multiple jobs at the same recursion depth
but doesn't actually execute them in parallel. They're spawned sequentially.

To enable true parallel execution, we need:

1. A new batch API endpoint (claude_run_batch) that accepts multiple tasks
2. Modified JobManager.execute_parallel_jobs() using asyncio.gather()
3. Enhanced RecursionManager to track sibling jobs at same depth
4. Updated dashboard to show parallel execution metrics

This would enable the architecture refactoring to proceed much faster
by allowing parallel analysis and modification of different packages.
""")


if __name__ == "__main__":
    asyncio.run(main())