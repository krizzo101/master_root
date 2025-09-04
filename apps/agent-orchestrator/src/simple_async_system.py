#!/usr/bin/env python3
"""
Simple Async System
A lightweight async framework for basic concurrent operations
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AsyncTask:
    """Simple async task definition"""

    task_id: str
    coro: Callable[..., Any]
    args: tuple = ()
    kwargs: dict = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class SimpleAsyncExecutor:
    """Basic async task executor with concurrency control"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tasks: Dict[str, AsyncTask] = {}

    async def execute_task(self, task: AsyncTask) -> Any:
        """Execute a single async task with concurrency control"""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            try:
                logger.info(f"Starting task: {task.task_id}")

                if asyncio.iscoroutinefunction(task.coro):
                    result = await task.coro(*task.args, **task.kwargs)
                else:
                    # Handle regular functions by running in executor
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, task.coro, *task.args)

                task.result = result
                task.status = TaskStatus.COMPLETED
                logger.info(f"Completed task: {task.task_id}")
                return result

            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.task_id} failed: {str(e)}")
                raise

    async def execute_batch(self, tasks: List[AsyncTask]) -> Dict[str, Any]:
        """Execute multiple tasks concurrently"""
        # Store tasks
        for task in tasks:
            self.tasks[task.task_id] = task

        # Execute all tasks concurrently
        task_coroutines = [self.execute_task(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect results
        result_dict = {}
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                result_dict[task.task_id] = {"error": str(result), "status": "failed"}
            else:
                result_dict[task.task_id] = {"result": result, "status": "completed"}

        return result_dict

    async def execute_sequential(self, tasks: List[AsyncTask]) -> Dict[str, Any]:
        """Execute tasks sequentially (useful for dependent operations)"""
        results = {}

        for task in tasks:
            self.tasks[task.task_id] = task
            try:
                result = await self.execute_task(task)
                results[task.task_id] = {"result": result, "status": "completed"}
            except Exception as e:
                results[task.task_id] = {"error": str(e), "status": "failed"}
                # Stop on first failure in sequential mode
                break

        return results

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        return task.status if task else None


class AsyncQueue:
    """Simple async queue for producer-consumer patterns"""

    def __init__(self, maxsize: int = 0):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.producers_done = asyncio.Event()

    async def put(self, item: Any) -> None:
        """Add item to queue"""
        await self.queue.put(item)

    async def get(self) -> Any:
        """Get item from queue"""
        return await self.queue.get()

    async def producer_done(self):
        """Signal that all producers are done"""
        self.producers_done.set()

    async def consumer_worker(
        self, worker_id: str, handler: Callable[[Any], Any]
    ) -> None:
        """Consumer worker that processes queue items"""
        logger.info(f"Consumer {worker_id} started")

        while True:
            try:
                # Wait for item with timeout to check if producers are done
                item = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Process item
                if asyncio.iscoroutinefunction(handler):
                    await handler(item)
                else:
                    handler(item)

                self.queue.task_done()

            except asyncio.TimeoutError:
                # Check if producers are done and queue is empty
                if self.producers_done.is_set() and self.queue.empty():
                    break
                continue

        logger.info(f"Consumer {worker_id} finished")


class AsyncTimer:
    """Simple async timer utilities"""

    @staticmethod
    async def delay(seconds: float) -> None:
        """Async delay"""
        await asyncio.sleep(seconds)

    @staticmethod
    async def timeout(coro: Any, seconds: float) -> Any:
        """Execute coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {seconds} seconds")
            raise

    @staticmethod
    async def retry(coro: Callable, max_attempts: int = 3, delay: float = 1.0) -> Any:
        """Retry coroutine with exponential backoff"""
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(coro):
                    return await coro()
                else:
                    return coro()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise

                wait_time = delay * (2**attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)


# Example usage and demonstrations
async def example_simple_task(task_name: str, duration: float = 1.0) -> str:
    """Example async task"""
    logger.info(f"Task {task_name} starting (duration: {duration}s)")
    await asyncio.sleep(duration)
    logger.info(f"Task {task_name} completed")
    return f"Result from {task_name}"


def example_sync_task(task_name: str) -> str:
    """Example synchronous task"""
    import time

    logger.info(f"Sync task {task_name} starting")
    time.sleep(0.5)  # Simulate work
    return f"Sync result from {task_name}"


async def demonstrate_simple_async_system():
    """Demonstrate the simple async system capabilities"""
    print("🚀 Simple Async System Demo")

    # 1. Basic concurrent execution
    print("\n1. Concurrent Task Execution:")
    executor = SimpleAsyncExecutor(max_concurrent=3)

    tasks = [
        AsyncTask("task1", example_simple_task, ("Task-1", 1.0)),
        AsyncTask("task2", example_simple_task, ("Task-2", 1.5)),
        AsyncTask("task3", example_sync_task, ("Task-3",)),
        AsyncTask("task4", example_simple_task, ("Task-4", 0.5)),
    ]

    results = await executor.execute_batch(tasks)
    print(f"Batch results: {results}")

    # 2. Sequential execution
    print("\n2. Sequential Task Execution:")
    sequential_tasks = [
        AsyncTask("seq1", example_simple_task, ("Seq-1", 0.5)),
        AsyncTask("seq2", example_simple_task, ("Seq-2", 0.3)),
    ]

    seq_results = await executor.execute_sequential(sequential_tasks)
    print(f"Sequential results: {seq_results}")

    # 3. Queue-based processing
    print("\n3. Queue-based Processing:")
    queue = AsyncQueue(maxsize=5)

    # Producer
    async def producer():
        for i in range(5):
            await queue.put(f"item-{i}")
            await asyncio.sleep(0.1)
        await queue.producer_done()

    # Consumer handler
    async def process_item(item):
        print(f"Processing: {item}")
        await asyncio.sleep(0.2)

    # Run producer and consumers
    producer_task = asyncio.create_task(producer())
    consumer_tasks = [
        asyncio.create_task(queue.consumer_worker(f"worker-{i}", process_item))
        for i in range(2)
    ]

    await producer_task
    await asyncio.gather(*consumer_tasks)

    # 4. Timer utilities
    print("\n4. Timer Utilities:")

    # Timeout example
    try:
        await AsyncTimer.timeout(example_simple_task("timeout-test", 2.0), 1.0)
    except asyncio.TimeoutError:
        print("Task timed out as expected")

    # Retry example
    failure_count = 0

    async def flaky_task():
        nonlocal failure_count
        failure_count += 1
        if failure_count < 3:
            raise Exception(f"Failure {failure_count}")
        return "Success after retries"

    result = await AsyncTimer.retry(flaky_task, max_attempts=3, delay=0.1)
    print(f"Retry result: {result}")


if __name__ == "__main__":
    asyncio.run(demonstrate_simple_async_system())
