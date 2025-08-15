"""
Async utilities for concurrent operations and resource management.
"""

import asyncio
import time
from typing import List, Callable, Any, Optional, TypeVar, Union, Dict, Set
from functools import wraps, partial
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from .logger import get_logger

T = TypeVar('T')
logger = get_logger(__name__)


class AsyncRateLimiter:
    """Rate limiter for async operations."""
    
    def __init__(self, max_calls: int, time_window: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a call."""
        async with self.lock:
            now = time.time()
            
            # Remove old calls outside the window
            self.calls = [t for t in self.calls if now - t < self.time_window]
            
            # Check if we can make a call
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = self.calls[0]
                wait_time = self.time_window - (now - oldest_call)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Recursive call after waiting
                    return await self.acquire()
            
            # Record this call
            self.calls.append(now)
    
    @asynccontextmanager
    async def __call__(self):
        """Context manager for rate-limited operations."""
        await self.acquire()
        yield


class AsyncTaskPool:
    """Pool for managing concurrent async tasks with limits."""
    
    def __init__(self, max_concurrent: int = 10, max_queue_size: int = 100):
        """
        Initialize task pool.
        
        Args:
            max_concurrent: Maximum concurrent tasks
            max_queue_size: Maximum queue size
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.tasks: Set[asyncio.Task] = set()
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []
    
    async def start(self):
        """Start the task pool workers."""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Starting task pool with {self.max_concurrent} workers")
        
        # Create worker tasks
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def stop(self):
        """Stop the task pool."""
        if not self._running:
            return
        
        logger.info("Stopping task pool")
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        # Cancel remaining tasks
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
    
    async def _worker(self, worker_id: str):
        """Worker coroutine that processes tasks from the queue."""
        logger.debug(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get task from queue with timeout
                task_data = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=1.0
                )
                
                task_id, func, args, kwargs = task_data
                
                logger.debug(f"Worker {worker_id} processing task {task_id}")
                
                # Execute task
                try:
                    async with self.semaphore:
                        result = await func(*args, **kwargs)
                        self.results[task_id] = result
                        logger.debug(f"Task {task_id} completed successfully")
                except Exception as e:
                    self.errors[task_id] = e
                    logger.error(f"Task {task_id} failed: {e}")
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def submit(self, 
                    func: Callable, 
                    *args, 
                    task_id: Optional[str] = None,
                    **kwargs) -> str:
        """
        Submit a task to the pool.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            task_id: Optional task ID
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        if not self._running:
            await self.start()
        
        task_id = task_id or f"task-{time.time()}"
        
        # Add to queue
        await self.queue.put((task_id, func, args, kwargs))
        logger.debug(f"Task {task_id} submitted to pool")
        
        return task_id
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get result of a task.
        
        Args:
            task_id: Task ID
            timeout: Optional timeout in seconds
            
        Returns:
            Task result
            
        Raises:
            Exception: If task failed
            TimeoutError: If timeout reached
        """
        start_time = time.time()
        
        while True:
            if task_id in self.results:
                return self.results.pop(task_id)
            
            if task_id in self.errors:
                raise self.errors.pop(task_id)
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.1)
    
    async def map(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        Map a function over items concurrently.
        
        Args:
            func: Async function to apply
            items: List of items
            
        Returns:
            List of results
        """
        # Submit all tasks
        task_ids = []
        for item in items:
            task_id = await self.submit(func, item)
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = await self.get_result(task_id)
            results.append(result)
        
        return results


async def run_async_tasks(tasks: List[Callable], 
                         max_concurrent: Optional[int] = None) -> List[Any]:
    """
    Run multiple async tasks concurrently.
    
    Args:
        tasks: List of async callables
        max_concurrent: Maximum concurrent tasks (None for unlimited)
        
    Returns:
        List of results in order
    """
    if max_concurrent:
        # Use semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task()
        
        return await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks]
        )
    else:
        # Run all tasks concurrently
        return await asyncio.gather(*[task() for task in tasks])


async def retry_async(func: Callable,
                     max_attempts: int = 3,
                     delay: float = 1.0,
                     backoff: float = 2.0,
                     exceptions: tuple = (Exception,)) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Function result
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {current_delay}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All {max_attempts} attempts failed")
    
    raise last_exception


async def timeout_async(func: Callable,
                       timeout: float,
                       error_message: Optional[str] = None) -> Any:
    """
    Run an async function with timeout.
    
    Args:
        func: Async function to run
        timeout: Timeout in seconds
        error_message: Optional custom error message
        
    Returns:
        Function result
        
    Raises:
        TimeoutError: If timeout is reached
    """
    try:
        return await asyncio.wait_for(func(), timeout=timeout)
    except asyncio.TimeoutError:
        msg = error_message or f"Operation timed out after {timeout}s"
        logger.error(msg)
        raise TimeoutError(msg)


class AsyncBatcher:
    """Batch async operations for efficiency."""
    
    def __init__(self, 
                batch_size: int = 10,
                batch_timeout: float = 1.0):
        """
        Initialize batcher.
        
        Args:
            batch_size: Maximum batch size
            batch_timeout: Maximum time to wait for batch
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending: List[tuple] = []
        self.lock = asyncio.Lock()
        self.event = asyncio.Event()
    
    async def add(self, item: Any) -> Any:
        """Add item to batch and wait for result."""
        future = asyncio.Future()
        
        async with self.lock:
            self.pending.append((item, future))
            
            if len(self.pending) >= self.batch_size:
                self.event.set()
        
        # Start batch processor if needed
        if len(self.pending) == 1:
            asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self):
        """Process pending batch."""
        try:
            # Wait for batch to fill or timeout
            await asyncio.wait_for(
                self.event.wait(),
                timeout=self.batch_timeout
            )
        except asyncio.TimeoutError:
            pass
        
        async with self.lock:
            if not self.pending:
                return
            
            batch = self.pending[:]
            self.pending.clear()
            self.event.clear()
        
        # Process batch
        items = [item for item, _ in batch]
        futures = [future for _, future in batch]
        
        try:
            results = await self.process_batch(items)
            
            # Set results
            for future, result in zip(futures, results):
                future.set_result(result)
        except Exception as e:
            # Set exception for all futures
            for future in futures:
                future.set_exception(e)
    
    async def process_batch(self, items: List[Any]) -> List[Any]:
        """
        Process a batch of items. Override in subclass.
        
        Args:
            items: List of items to process
            
        Returns:
            List of results
        """
        raise NotImplementedError


class AsyncCircuitBreaker:
    """Circuit breaker for async operations."""
    
    def __init__(self,
                failure_threshold: int = 5,
                recovery_timeout: float = 60.0,
                expected_exception: type = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Time before attempting recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
        self.lock = asyncio.Lock()
    
    async def call(self, func: Callable) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Async function to call
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        async with self.lock:
            # Check circuit state
            if self.state == "open":
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time > self.recovery_timeout):
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise Exception("Circuit breaker is open")
        
        try:
            result = await func()
            
            async with self.lock:
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info("Circuit breaker closed")
            
            return result
            
        except self.expected_exception as e:
            async with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e


# Example usage
if __name__ == "__main__":
    async def example():
        # Rate limiter example
        rate_limiter = AsyncRateLimiter(max_calls=5, time_window=1.0)
        
        async def api_call(i):
            async with rate_limiter():
                print(f"API call {i} at {time.time():.2f}")
                await asyncio.sleep(0.1)
                return i * 2
        
        # Task pool example
        pool = AsyncTaskPool(max_concurrent=3)
        await pool.start()
        
        # Submit tasks
        task_ids = []
        for i in range(10):
            task_id = await pool.submit(api_call, i)
            task_ids.append(task_id)
        
        # Get results
        results = []
        for task_id in task_ids:
            result = await pool.get_result(task_id)
            results.append(result)
        
        print(f"Results: {results}")
        
        await pool.stop()
    
    # Run example
    asyncio.run(example())