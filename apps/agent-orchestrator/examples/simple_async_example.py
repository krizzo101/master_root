#!/usr/bin/env python3
"""
Simple Async System Usage Examples
Practical examples of using the simple async system
"""

import asyncio
import random
import sys
from pathlib import Path

from simple_async_system import AsyncQueue, AsyncTask, AsyncTimer, SimpleAsyncExecutor

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def fetch_data(url: str, delay: float = None) -> dict:
    """Simulate fetching data from an API"""
    if delay is None:
        delay = random.uniform(0.5, 2.0)

    print(f"Fetching data from {url}...")
    await asyncio.sleep(delay)  # Simulate network delay

    return {"url": url, "status": "success", "data": f"Data from {url}", "delay": delay}


def process_file(filename: str) -> str:
    """Simulate CPU-bound file processing"""
    import time

    print(f"Processing file: {filename}")
    time.sleep(0.3)  # Simulate processing time
    return f"Processed {filename}"


async def basic_concurrent_example():
    """Basic concurrent task execution"""
    print("=== Basic Concurrent Example ===")

    executor = SimpleAsyncExecutor(max_concurrent=3)

    # Create tasks for fetching data from multiple APIs
    urls = [
        "https://api1.example.com/data",
        "https://api2.example.com/users",
        "https://api3.example.com/posts",
        "https://api4.example.com/comments",
        "https://api5.example.com/metrics",
    ]

    tasks = [AsyncTask(f"fetch_{i}", fetch_data, (url,)) for i, url in enumerate(urls)]

    print(f"Executing {len(tasks)} fetch tasks concurrently...")
    results = await executor.execute_batch(tasks)

    print("\nResults:")
    for task_id, result in results.items():
        if "result" in result:
            data = result["result"]
            print(f"  {task_id}: {data['status']} - {data['delay']:.2f}s")
        else:
            print(f"  {task_id}: FAILED - {result['error']}")


async def mixed_workload_example():
    """Mix of async and sync tasks"""
    print("\n=== Mixed Workload Example ===")

    executor = SimpleAsyncExecutor(max_concurrent=4)

    # Mix of I/O-bound (async) and CPU-bound (sync) tasks
    tasks = [
        AsyncTask("fetch1", fetch_data, ("https://api.example.com/fast", 0.5)),
        AsyncTask("process1", process_file, ("document1.pdf",)),
        AsyncTask("fetch2", fetch_data, ("https://api.example.com/slow", 1.5)),
        AsyncTask("process2", process_file, ("document2.pdf",)),
        AsyncTask("fetch3", fetch_data, ("https://api.example.com/medium", 1.0)),
    ]

    print(f"Executing {len(tasks)} mixed tasks...")
    results = await executor.execute_batch(tasks)

    print("\nResults:")
    for task_id, result in results.items():
        status = result.get("status", "unknown")
        print(f"  {task_id}: {status}")


async def sequential_pipeline_example():
    """Sequential processing pipeline"""
    print("\n=== Sequential Pipeline Example ===")

    executor = SimpleAsyncExecutor()

    # Pipeline: fetch -> process -> validate -> save
    async def validate_data(data: dict) -> dict:
        await asyncio.sleep(0.2)
        data["validated"] = True
        return data

    async def save_data(data: dict) -> str:
        await asyncio.sleep(0.3)
        return f"Saved data: {data['url']}"

    # Sequential pipeline tasks
    pipeline_tasks = [
        AsyncTask("fetch", fetch_data, ("https://api.example.com/data", 0.5)),
        AsyncTask(
            "validate", validate_data, ({"url": "https://api.example.com/data"},)
        ),
        AsyncTask(
            "save",
            save_data,
            ({"url": "https://api.example.com/data", "validated": True},),
        ),
    ]

    print("Executing pipeline sequentially...")
    results = await executor.execute_sequential(pipeline_tasks)

    print("\nPipeline Results:")
    for task_id, result in results.items():
        status = result.get("status", "unknown")
        print(f"  {task_id}: {status}")


async def queue_processing_example():
    """Producer-consumer queue processing"""
    print("\n=== Queue Processing Example ===")

    queue = AsyncQueue(maxsize=10)
    processed_items = []

    # Producer: generate work items
    async def producer(name: str, count: int):
        print(f"Producer {name} starting...")
        for i in range(count):
            item = f"{name}-item-{i}"
            await queue.put(item)
            print(f"  Produced: {item}")
            await asyncio.sleep(0.1)  # Simulate production delay
        print(f"Producer {name} finished")

    # Consumer handler: process work items
    async def process_work_item(item: str):
        processing_time = random.uniform(0.2, 0.8)
        print(f"  Processing {item} (will take {processing_time:.2f}s)")
        await asyncio.sleep(processing_time)
        processed_items.append(item)
        print(f"  Completed {item}")

    # Start producers
    producer_tasks = [
        asyncio.create_task(producer("Producer-A", 3)),
        asyncio.create_task(producer("Producer-B", 2)),
    ]

    # Start consumers
    consumer_tasks = [
        asyncio.create_task(queue.consumer_worker(f"Consumer-{i}", process_work_item))
        for i in range(2)
    ]

    # Wait for producers to finish
    await asyncio.gather(*producer_tasks)
    await queue.producer_done()

    # Wait for consumers to finish
    await asyncio.gather(*consumer_tasks)

    print(f"\nProcessed {len(processed_items)} items: {processed_items}")


async def timer_utilities_example():
    """Demonstrate timer utilities"""
    print("\n=== Timer Utilities Example ===")

    # 1. Timeout example
    print("1. Timeout handling:")
    try:
        result = await AsyncTimer.timeout(
            fetch_data("https://slow-api.example.com", 3.0), timeout=1.0
        )
        print(f"  Result: {result}")
    except asyncio.TimeoutError:
        print("  ✓ Task timed out as expected")

    # 2. Retry with exponential backoff
    print("\n2. Retry with backoff:")
    attempt_count = 0

    async def unreliable_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt #{attempt_count}")

        if attempt_count < 3:
            raise Exception(f"Simulated failure #{attempt_count}")

        return "Success!"

    try:
        result = await AsyncTimer.retry(unreliable_operation, max_attempts=4, delay=0.5)
        print(f"  ✓ Final result: {result}")
    except Exception as e:
        print(f"  ✗ All retries failed: {e}")


async def error_handling_example():
    """Demonstrate error handling in async tasks"""
    print("\n=== Error Handling Example ===")

    executor = SimpleAsyncExecutor(max_concurrent=3)

    async def failing_task(task_name: str, should_fail: bool = False):
        await asyncio.sleep(0.5)
        if should_fail:
            raise ValueError(f"Task {task_name} failed intentionally")
        return f"Success from {task_name}"

    # Mix of successful and failing tasks
    tasks = [
        AsyncTask("success1", failing_task, ("Task-1", False)),
        AsyncTask("failure1", failing_task, ("Task-2", True)),
        AsyncTask("success2", failing_task, ("Task-3", False)),
        AsyncTask("failure2", failing_task, ("Task-4", True)),
    ]

    print("Executing tasks with intentional failures...")
    results = await executor.execute_batch(tasks)

    print("\nResults (showing error handling):")
    successful = 0
    failed = 0

    for task_id, result in results.items():
        if "error" in result:
            print(f"  ✗ {task_id}: FAILED - {result['error']}")
            failed += 1
        else:
            print(f"  ✓ {task_id}: SUCCESS - {result['result']}")
            successful += 1

    print(f"\nSummary: {successful} successful, {failed} failed")


async def main():
    """Run all examples"""
    print("🚀 Simple Async System Examples\n")

    examples = [
        basic_concurrent_example,
        mixed_workload_example,
        sequential_pipeline_example,
        queue_processing_example,
        timer_utilities_example,
        error_handling_example,
    ]

    for example in examples:
        try:
            await example()
            await asyncio.sleep(0.5)  # Brief pause between examples
        except KeyboardInterrupt:
            print("\n⚠️  Examples interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example failed: {e}")

    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
