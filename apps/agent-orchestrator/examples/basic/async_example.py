#!/usr/bin/env python3
"""
EP Async Example - Comprehensive demonstration of Python async patterns
Based on EP research findings for efficient concurrent programming
"""

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Task:
    """Represents a task to be processed"""
    id: int
    name: str
    priority: int
    data: Dict[str, Any]


class TaskStatus(Enum):
    """Task processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# 1. Basic Async/Await Pattern
# ============================================================================

async def basic_async_operation(task_id: int, delay: float) -> str:
    """Basic async operation with simulated I/O delay"""
    print(f"Task {task_id}: Starting operation")
    await asyncio.sleep(delay)  # Simulates I/O operation
    print(f"Task {task_id}: Operation completed")
    return f"Result from task {task_id}"


# ============================================================================
# 2. Concurrent Execution with gather()
# ============================================================================

async def parallel_execution_demo():
    """Demonstrates parallel execution using asyncio.gather()"""
    print("\n=== Parallel Execution Demo ===")

    # Create multiple coroutines
    coroutines = [
        basic_async_operation(i, random.uniform(0.5, 2.0))
        for i in range(5)
    ]

    # Execute all concurrently and collect results
    start_time = time.perf_counter()
    results = await asyncio.gather(*coroutines)
    elapsed = time.perf_counter() - start_time

    print(f"All tasks completed in {elapsed:.2f} seconds")
    print(f"Results: {results}")
    return results


# ============================================================================
# 3. Task Management with create_task()
# ============================================================================

async def task_management_demo():
    """Demonstrates task creation and management"""
    print("\n=== Task Management Demo ===")

    # Create tasks for independent execution
    task1 = asyncio.create_task(
        basic_async_operation(101, 1.0),
        name="high-priority-task"
    )
    task2 = asyncio.create_task(
        basic_async_operation(102, 0.5),
        name="low-priority-task"
    )

    # Can do other work here while tasks run
    print("Tasks are running in background...")
    await asyncio.sleep(0.2)
    print("Doing other work...")

    # Wait for specific tasks
    result1 = await task1
    result2 = await task2

    print(f"Task results: {result1}, {result2}")
    return result1, result2


# ============================================================================
# 4. Semaphore Pattern for Rate Limiting
# ============================================================================

class RateLimitedFetcher:
    """Fetcher with concurrent request limiting using semaphore"""

    def __init__(self, max_concurrent: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.request_count = 0

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch URL with rate limiting"""
        async with self.semaphore:
            self.request_count += 1
            print(f"Fetching {url} (request #{self.request_count})")

            # Simulate network request
            await asyncio.sleep(random.uniform(0.5, 1.5))

            return {
                "url": url,
                "status": 200,
                "data": f"Content from {url}",
                "request_number": self.request_count
            }

    async def fetch_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple URLs with rate limiting"""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)


async def rate_limiting_demo():
    """Demonstrates rate limiting with semaphore"""
    print("\n=== Rate Limiting Demo ===")

    fetcher = RateLimitedFetcher(max_concurrent=2)
    urls = [f"https://api.example.com/endpoint/{i}" for i in range(5)]

    start_time = time.perf_counter()
    results = await fetcher.fetch_multiple(urls)
    elapsed = time.perf_counter() - start_time

    print(f"Fetched {len(results)} URLs in {elapsed:.2f} seconds")
    print(f"With max 2 concurrent requests")
    return results


# ============================================================================
# 5. Queue Pattern for Producer-Consumer
# ============================================================================

class TaskProcessor:
    """Async task processor using queue pattern"""

    def __init__(self, num_workers: int = 3):
        self.queue = asyncio.Queue(maxsize=10)
        self.num_workers = num_workers
        self.results = []

    async def producer(self, tasks: List[Task]):
        """Add tasks to the queue"""
        print(f"Producer: Adding {len(tasks)} tasks to queue")
        for task in tasks:
            await self.queue.put(task)
            print(f"Producer: Added task {task.id} to queue")

        # Add sentinel values to signal workers to stop
        for _ in range(self.num_workers):
            await self.queue.put(None)

    async def worker(self, worker_id: int):
        """Process tasks from the queue"""
        while True:
            task = await self.queue.get()

            if task is None:  # Sentinel value
                print(f"Worker {worker_id}: Shutting down")
                self.queue.task_done()
                break

            try:
                print(f"Worker {worker_id}: Processing task {task.id}")
                # Simulate processing
                await asyncio.sleep(random.uniform(0.5, 1.5))

                result = {
                    "task_id": task.id,
                    "worker_id": worker_id,
                    "status": TaskStatus.COMPLETED,
                    "result": f"Processed {task.name}"
                }
                self.results.append(result)
                print(f"Worker {worker_id}: Completed task {task.id}")

            except Exception as e:
                print(f"Worker {worker_id}: Error processing task {task.id}: {e}")
                self.results.append({
                    "task_id": task.id,
                    "worker_id": worker_id,
                    "status": TaskStatus.FAILED,
                    "error": str(e)
                })
            finally:
                self.queue.task_done()

    async def process_all(self, tasks: List[Task]) -> List[Dict]:
        """Process all tasks using producer-consumer pattern"""
        # Start workers
        workers = [
            asyncio.create_task(self.worker(i))
            for i in range(self.num_workers)
        ]

        # Start producer
        await self.producer(tasks)

        # Wait for all tasks to be processed
        await self.queue.join()

        # Wait for workers to shut down
        await asyncio.gather(*workers)

        return self.results


async def queue_pattern_demo():
    """Demonstrates producer-consumer queue pattern"""
    print("\n=== Queue Pattern Demo ===")

    # Create sample tasks
    tasks = [
        Task(id=i, name=f"task_{i}", priority=random.randint(1, 5), data={"value": i * 10})
        for i in range(8)
    ]

    processor = TaskProcessor(num_workers=3)

    start_time = time.perf_counter()
    results = await processor.process_all(tasks)
    elapsed = time.perf_counter() - start_time

    print(f"\nProcessed {len(results)} tasks in {elapsed:.2f} seconds")
    print(f"Results: {results[:3]}...")  # Show first 3 results
    return results


# ============================================================================
# 6. Async Context Manager Pattern
# ============================================================================

class AsyncDatabaseConnection:
    """Simulated async database connection with context manager"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False

    async def connect(self):
        """Establish connection"""
        print(f"Connecting to database: {self.connection_string}")
        await asyncio.sleep(0.5)  # Simulate connection delay
        self.connected = True
        print("Database connected")

    async def disconnect(self):
        """Close connection"""
        print("Disconnecting from database")
        await asyncio.sleep(0.2)  # Simulate disconnection delay
        self.connected = False
        print("Database disconnected")

    async def execute(self, query: str) -> List[Dict]:
        """Execute a query"""
        if not self.connected:
            raise RuntimeError("Not connected to database")

        print(f"Executing query: {query}")
        await asyncio.sleep(0.3)  # Simulate query execution
        return [{"id": 1, "result": "data"}]

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


async def context_manager_demo():
    """Demonstrates async context manager pattern"""
    print("\n=== Async Context Manager Demo ===")

    async with AsyncDatabaseConnection("postgresql://localhost/mydb") as db:
        result = await db.execute("SELECT * FROM users")
        print(f"Query result: {result}")

    print("Context manager automatically handled connection lifecycle")


# ============================================================================
# 7. Timeout Pattern
# ============================================================================

async def long_running_operation(duration: float) -> str:
    """Simulates a long-running operation"""
    print(f"Starting operation that will take {duration} seconds")
    await asyncio.sleep(duration)
    return f"Operation completed after {duration} seconds"


async def timeout_pattern_demo():
    """Demonstrates timeout pattern for handling slow operations"""
    print("\n=== Timeout Pattern Demo ===")

    # Successful operation within timeout
    try:
        result = await asyncio.wait_for(
            long_running_operation(1.0),
            timeout=2.0
        )
        print(f"Success: {result}")
    except asyncio.TimeoutError:
        print("Operation timed out")

    # Operation that will timeout
    try:
        result = await asyncio.wait_for(
            long_running_operation(3.0),
            timeout=2.0
        )
        print(f"Success: {result}")
    except asyncio.TimeoutError:
        print("Operation timed out (expected)")


# ============================================================================
# 8. Batching Pattern for Performance
# ============================================================================

class BatchProcessor:
    """Process items in batches for improved performance"""

    async def process_item(self, item: Any) -> Dict:
        """Process a single item"""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"item": item, "processed": True}

    async def process_batch(self, items: List[Any], batch_size: int = 5) -> List[Dict]:
        """Process items in batches"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            print(f"Processing batch of {len(batch)} items")

            # Process batch concurrently
            batch_tasks = [self.process_item(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

            # Small delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(0.2)

        return results


async def batching_demo():
    """Demonstrates batching pattern"""
    print("\n=== Batching Pattern Demo ===")

    items = list(range(12))  # 12 items to process
    processor = BatchProcessor()

    start_time = time.perf_counter()
    results = await processor.process_batch(items, batch_size=3)
    elapsed = time.perf_counter() - start_time

    print(f"Processed {len(results)} items in {elapsed:.2f} seconds")
    print(f"Using batch size of 3")
    return results


# ============================================================================
# 9. Lock Pattern for Synchronization
# ============================================================================

class SharedCounter:
    """Thread-safe counter using async lock"""

    def __init__(self):
        self.value = 0
        self.lock = asyncio.Lock()

    async def increment(self, worker_id: int):
        """Increment counter with lock protection"""
        async with self.lock:
            # Critical section
            current = self.value
            print(f"Worker {worker_id}: Current value = {current}")
            await asyncio.sleep(0.1)  # Simulate some work
            self.value = current + 1
            print(f"Worker {worker_id}: Updated value = {self.value}")

    async def get_value(self) -> int:
        """Get current counter value"""
        async with self.lock:
            return self.value


async def lock_pattern_demo():
    """Demonstrates lock pattern for synchronization"""
    print("\n=== Lock Pattern Demo ===")

    counter = SharedCounter()

    # Multiple workers trying to increment counter
    workers = [
        counter.increment(i)
        for i in range(5)
    ]

    await asyncio.gather(*workers)

    final_value = await counter.get_value()
    print(f"Final counter value: {final_value}")
    print("Without lock, race conditions would corrupt the counter")


# ============================================================================
# 10. Error Handling with TaskGroup (Python 3.11+)
# ============================================================================

async def potentially_failing_task(task_id: int, should_fail: bool = False):
    """Task that might fail"""
    await asyncio.sleep(random.uniform(0.1, 0.5))

    if should_fail:
        raise ValueError(f"Task {task_id} failed as requested")

    return f"Task {task_id} succeeded"


async def error_handling_demo():
    """Demonstrates error handling patterns"""
    print("\n=== Error Handling Demo ===")

    # Try with TaskGroup if Python 3.11+
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(potentially_failing_task(1, False))
            task2 = tg.create_task(potentially_failing_task(2, True))  # Will fail
            task3 = tg.create_task(potentially_failing_task(3, False))
    except* ValueError as eg:
        print(f"Caught exception group: {eg.exceptions}")
    except AttributeError:
        # Fallback for Python < 3.11
        print("TaskGroup not available, using gather with return_exceptions")

        results = await asyncio.gather(
            potentially_failing_task(1, False),
            potentially_failing_task(2, True),
            potentially_failing_task(3, False),
            return_exceptions=True
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1} failed: {result}")
            else:
                print(f"Task {i+1} succeeded: {result}")


# ============================================================================
# 11. Async Iterator Pattern
# ============================================================================

class AsyncDataStream:
    """Async iterator for streaming data"""

    def __init__(self, max_items: int = 5):
        self.max_items = max_items
        self.current = 0

    async def fetch_next_batch(self) -> Optional[List[str]]:
        """Simulate fetching next batch of data"""
        if self.current >= self.max_items:
            return None

        await asyncio.sleep(0.3)  # Simulate network delay
        batch_size = min(2, self.max_items - self.current)
        batch = [f"item_{self.current + i}" for i in range(batch_size)]
        self.current += batch_size
        return batch

    def __aiter__(self):
        """Return async iterator"""
        return self

    async def __anext__(self):
        """Get next item from stream"""
        if not hasattr(self, '_buffer'):
            self._buffer = []

        if not self._buffer:
            batch = await self.fetch_next_batch()
            if batch is None:
                raise StopAsyncIteration
            self._buffer.extend(batch)

        return self._buffer.pop(0)


async def async_iterator_demo():
    """Demonstrates async iterator pattern"""
    print("\n=== Async Iterator Demo ===")

    stream = AsyncDataStream(max_items=7)

    print("Streaming data items:")
    async for item in stream:
        print(f"  Received: {item}")
        # Process each item as it arrives
        await asyncio.sleep(0.1)


# ============================================================================
# Main Orchestrator
# ============================================================================

async def main():
    """Main function orchestrating all demos"""
    print("=" * 60)
    print("EP ASYNC PATTERNS DEMONSTRATION")
    print("=" * 60)

    # Run all demonstrations
    demos = [
        ("Parallel Execution", parallel_execution_demo()),
        ("Task Management", task_management_demo()),
        ("Rate Limiting", rate_limiting_demo()),
        ("Queue Pattern", queue_pattern_demo()),
        ("Context Manager", context_manager_demo()),
        ("Timeout Pattern", timeout_pattern_demo()),
        ("Batching Pattern", batching_demo()),
        ("Lock Pattern", lock_pattern_demo()),
        ("Error Handling", error_handling_demo()),
        ("Async Iterator", async_iterator_demo()),
    ]

    for name, demo_coro in demos:
        print(f"\n{'=' * 60}")
        print(f"Running: {name}")
        print('=' * 60)
        try:
            await demo_coro
        except Exception as e:
            print(f"Demo failed: {e}")

        # Small pause between demos
        await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("ALL DEMONSTRATIONS COMPLETED")
    print("=" * 60)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run with debug mode for development
    import sys

    debug_mode = "--debug" in sys.argv

    if debug_mode:
        print("Running in debug mode")
        asyncio.run(main(), debug=True)
    else:
        asyncio.run(main())
