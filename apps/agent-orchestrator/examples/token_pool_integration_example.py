#!/usr/bin/env python3
"""
Example integration of Enhanced Token Pool with GenericOrchestrator
Demonstrates migration path and new features
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generic_orchestrator import AgentTask
from token_pool_enhanced import EnhancedTokenPool, TokenPool


async def example_backward_compatible():
    """Example using backward compatible interface"""
    print("\n=== Backward Compatible Usage ===")

    # Create pool using alias (drop-in replacement)
    pool = TokenPool(tokens=["token1", "token2", "token3"])

    # Original interface works exactly the same
    token, idx = await pool.acquire()
    print(f"Acquired token at index {idx}")

    # Simulate work
    await asyncio.sleep(0.5)

    # Release (synchronous method still works)
    pool.release(idx)
    print(f"Released token at index {idx}")

    # Check availability
    print(f"Available tokens: {pool.available}/{pool.size()}")

    await pool.shutdown()


async def example_reservation_system():
    """Example using reservation system"""
    print("\n=== Reservation System Usage ===")

    pool = EnhancedTokenPool(
        tokens=["token1", "token2", "token3"], default_reservation_timeout=10.0
    )
    await pool.initialize()

    # Reserve a token
    print("Creating reservation...")
    reservation = await pool.acquire_with_reservation(
        timeout=5.0, task_id="analysis_task"
    )
    print(f"Reserved token {reservation.token_idx} for task {reservation.task_id}")
    print(f"Time remaining: {reservation.time_remaining:.1f}s")

    # Simulate preparation work
    print("Doing preparation work...")
    await asyncio.sleep(1.0)

    # Confirm and use token
    print("Confirming reservation...")
    token, idx = await pool.confirm_reservation(reservation.reservation_id)
    print(f"Token confirmed and in use: index {idx}")

    # Simulate API call
    await asyncio.sleep(0.5)

    # Release
    await pool._release_token(idx)
    print(f"Token {idx} released")

    await pool.shutdown()


async def example_batch_allocation():
    """Example using batch allocation for multi-agent tasks"""
    print("\n=== Batch Allocation Usage ===")

    pool = EnhancedTokenPool(
        tokens=[f"token_{i}" for i in range(10)], enable_metrics=True
    )
    await pool.initialize()

    # Allocate batch for multi-agent task
    print("Allocating batch of 5 tokens...")
    batch_id = "multi_agent_analysis"
    reservations = await pool.acquire_batch(count=5, timeout=30.0, batch_id=batch_id)
    print(f"Allocated {len(reservations)} tokens for batch {batch_id}")

    # Simulate parallel agent execution
    async def execute_agent(reservation):
        token, idx = await pool.confirm_reservation(reservation.reservation_id)
        print(f"  Agent using token {idx}")
        await asyncio.sleep(1.0)  # Simulate work
        return f"Result from token {idx}"

    # Run agents in parallel
    print("Executing agents in parallel...")
    tasks = [execute_agent(r) for r in reservations]
    results = await asyncio.gather(*tasks)

    print("Agent results:")
    for result in results:
        print(f"  - {result}")

    # Release entire batch
    print(f"Releasing batch {batch_id}...")
    await pool.release_batch(batch_id)

    # Show metrics
    metrics = pool.get_metrics()
    print("\nMetrics:")
    print(f"  Total acquisitions: {metrics['total_acquisitions']}")
    print(f"  Total batch allocations: {metrics['total_batch_allocations']}")
    print(
        f"  Available tokens: {metrics['available_tokens']}/{metrics['total_tokens']}"
    )

    await pool.shutdown()


async def example_high_concurrency():
    """Example demonstrating performance under high concurrency"""
    print("\n=== High Concurrency Performance ===")

    pool = EnhancedTokenPool(
        tokens=[f"token_{i}" for i in range(20)], enable_metrics=True
    )
    await pool.initialize()

    # Create many concurrent tasks
    async def worker(worker_id):
        reservation = await pool.acquire_with_reservation()
        token, idx = await pool.confirm_reservation(reservation.reservation_id)
        await asyncio.sleep(0.01)  # Simulate quick work
        await pool._release_token(idx)
        return worker_id

    print("Running 100 concurrent workers...")
    start_time = asyncio.get_event_loop().time()

    # Launch all workers
    tasks = [worker(i) for i in range(100)]
    results = await asyncio.gather(*tasks)

    elapsed = asyncio.get_event_loop().time() - start_time

    # Show performance metrics
    metrics = pool.get_metrics()
    print(f"\nCompleted {len(results)} tasks in {elapsed:.2f}s")
    print(f"Average acquisition time: {metrics['avg_acquisition_time']*1000:.2f}ms")
    print(f"Total timeouts: {metrics['total_timeouts']}")
    print(
        f"Final token availability: {metrics['available_tokens']}/{metrics['total_tokens']}"
    )

    await pool.shutdown()


async def example_orchestrator_integration():
    """Example showing integration with orchestrator tasks"""
    print("\n=== Orchestrator Integration Example ===")

    pool = EnhancedTokenPool(
        tokens=[f"token_{i}" for i in range(5)], enable_metrics=True
    )
    await pool.initialize()

    # Create mock agent tasks
    tasks = [
        AgentTask(
            task_id=f"task_{i}",
            task_type="analysis",
            prompt=f"Analyze component {i}",
            context={"component": i},
        )
        for i in range(3)
    ]

    print(f"Executing {len(tasks)} orchestrator tasks...")

    # Allocate tokens for all tasks
    batch_id = "orchestrator_batch"
    reservations = await pool.acquire_batch(
        count=len(tasks), timeout=60.0, batch_id=batch_id
    )

    # Execute tasks with reserved tokens
    async def execute_task(task, reservation):
        token, idx = await pool.confirm_reservation(reservation.reservation_id)
        print(f"  Task {task.task_id} using token {idx}")

        # Simulate agent execution
        await asyncio.sleep(0.5)

        task.status = "completed"
        task.result = {"analysis": f"Completed {task.task_type}"}
        return task

    # Run all tasks
    task_executions = [
        execute_task(task, res) for task, res in zip(tasks, reservations)
    ]
    completed_tasks = await asyncio.gather(*task_executions)

    # Release batch
    await pool.release_batch(batch_id)

    # Show results
    print("\nTask Results:")
    for task in completed_tasks:
        print(f"  {task.task_id}: {task.status} - {task.result}")

    # Show final metrics
    metrics = pool.get_metrics()
    print(f"\nFinal Metrics:")
    print(f"  Total reservations: {metrics['total_reservations']}")
    print(f"  Total releases: {metrics['total_releases']}")
    print(f"  Batch allocations: {metrics['total_batch_allocations']}")

    await pool.shutdown()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Enhanced Token Pool Integration Examples")
    print("=" * 60)

    # Run examples in sequence
    await example_backward_compatible()
    await example_reservation_system()
    await example_batch_allocation()
    await example_high_concurrency()
    await example_orchestrator_integration()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
