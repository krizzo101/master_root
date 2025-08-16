"""
Resource isolation and bulkhead pattern implementation.

Provides thread pools, semaphores, resource limiting, and isolation
mechanisms to prevent cascading failures.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from opsvi_foundation.patterns import ComponentError


class BulkheadError(ComponentError):
    """Raised when bulkhead operation fails."""


class ResourceExhaustedError(BulkheadError):
    """Raised when bulkhead resources are exhausted."""


class BulkheadState(Enum):
    """Bulkhead states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead pattern."""

    max_concurrent_calls: int = 10
    max_wait_duration: float = 5.0
    max_queue_size: int = 100
    isolation_timeout: float = 30.0
    failure_threshold: int = 5
    recovery_timeout: float = 60.0


T = TypeVar("T")


class Bulkhead:
    """Bulkhead pattern implementation for resource isolation."""

    def __init__(self, config: BulkheadConfig):
        """
        Initialize bulkhead.

        Args:
            config: Bulkhead configuration
        """
        self.config = config
        self.state = BulkheadState.OPEN
        self.semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        self.queue = asyncio.Queue(maxsize=config.max_queue_size)
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with bulkhead protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            ResourceExhaustedError: If bulkhead is exhausted
            BulkheadError: If execution fails
        """
        if self.state == BulkheadState.CLOSED:
            raise ResourceExhaustedError("Bulkhead is closed")

        try:
            async with self.semaphore:
                return await self._execute_with_timeout(func, *args, **kwargs)
        except TimeoutError:
            await self._record_failure()
            raise ResourceExhaustedError("Bulkhead timeout exceeded")
        except Exception as e:
            await self._record_failure()
            raise BulkheadError(f"Bulkhead execution failed: {e!s}") from e

    async def _execute_with_timeout(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with timeout."""
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.isolation_timeout,
            )
        # For synchronous functions, run in thread pool
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, func, *args, **kwargs),
            timeout=self.config.isolation_timeout,
        )

    async def _record_failure(self) -> None:
        """Record a failure and potentially close the bulkhead."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()

            if self.failure_count >= self.config.failure_threshold:
                self.state = BulkheadState.CLOSED
                # Schedule recovery
                asyncio.create_task(self._schedule_recovery())

    async def _schedule_recovery(self) -> None:
        """Schedule bulkhead recovery."""
        await asyncio.sleep(self.config.recovery_timeout)
        async with self._lock:
            self.state = BulkheadState.HALF_OPEN
            self.failure_count = 0

    async def reset(self) -> None:
        """Reset bulkhead to open state."""
        async with self._lock:
            self.state = BulkheadState.OPEN
            self.failure_count = 0

    @property
    def is_open(self) -> bool:
        """Check if bulkhead is open."""
        return self.state == BulkheadState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if bulkhead is closed."""
        return self.state == BulkheadState.CLOSED

    @property
    def available_permits(self) -> int:
        """Get number of available permits."""
        return self.semaphore._value


class ThreadPoolBulkhead:
    """Thread pool-based bulkhead for synchronous operations."""

    def __init__(self, config: BulkheadConfig):
        """
        Initialize thread pool bulkhead.

        Args:
            config: Bulkhead configuration
        """
        self.config = config
        self.executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent_calls,
            thread_name_prefix="bulkhead",
        )
        self.active_tasks = 0
        self._lock = threading.Lock()

    def execute(self, func: Callable[..., T], *args, **kwargs) -> Future[T]:
        """
        Execute function in thread pool.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Future containing the result

        Raises:
            ResourceExhaustedError: If thread pool is exhausted
        """
        with self._lock:
            if self.active_tasks >= self.config.max_concurrent_calls:
                raise ResourceExhaustedError("Thread pool exhausted")
            self.active_tasks += 1

        try:
            future = self.executor.submit(func, *args, **kwargs)
            future.add_done_callback(self._on_task_complete)
            return future
        except Exception:
            with self._lock:
                self.active_tasks -= 1
            raise

    def _on_task_complete(self, future: Future) -> None:
        """Callback when task completes."""
        with self._lock:
            self.active_tasks -= 1

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown thread pool.

        Args:
            wait: Whether to wait for tasks to complete
        """
        self.executor.shutdown(wait=wait)

    @property
    def active_task_count(self) -> int:
        """Get number of active tasks."""
        with self._lock:
            return self.active_tasks


class ResourceLimiter:
    """Resource limiter for controlling resource usage."""

    def __init__(self, max_resources: int):
        """
        Initialize resource limiter.

        Args:
            max_resources: Maximum number of resources
        """
        self.max_resources = max_resources
        self.used_resources = 0
        self._lock = asyncio.Lock()
        self._waiters: list[asyncio.Future] = []

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire a resource.

        Args:
            timeout: Timeout for acquisition

        Returns:
            True if resource acquired, False if timeout
        """
        async with self._lock:
            if self.used_resources < self.max_resources:
                self.used_resources += 1
                return True

            # Wait for resource to become available
            waiter = asyncio.Future()
            self._waiters.append(waiter)

        try:
            if timeout is not None:
                await asyncio.wait_for(waiter, timeout=timeout)
            else:
                await waiter
            return True
        except TimeoutError:
            # Remove waiter if timeout
            async with self._lock:
                if waiter in self._waiters:
                    self._waiters.remove(waiter)
            return False

    async def release(self) -> None:
        """Release a resource."""
        async with self._lock:
            if self.used_resources > 0:
                self.used_resources -= 1

                # Wake up next waiter
                if self._waiters:
                    waiter = self._waiters.pop(0)
                    waiter.set_result(None)

    @property
    def available_resources(self) -> int:
        """Get number of available resources."""
        return max(0, self.max_resources - self.used_resources)

    @property
    def utilization(self) -> float:
        """Get resource utilization percentage."""
        return (self.used_resources / self.max_resources) * 100


class IsolationManager:
    """Manager for multiple bulkheads and resource limiters."""

    def __init__(self):
        """Initialize isolation manager."""
        self.bulkheads: dict[str, Bulkhead] = {}
        self.thread_pools: dict[str, ThreadPoolBulkhead] = {}
        self.resource_limiters: dict[str, ResourceLimiter] = {}

    def add_bulkhead(self, name: str, config: BulkheadConfig) -> Bulkhead:
        """
        Add a bulkhead.

        Args:
            name: Bulkhead name
            config: Bulkhead configuration

        Returns:
            Created bulkhead
        """
        bulkhead = Bulkhead(config)
        self.bulkheads[name] = bulkhead
        return bulkhead

    def add_thread_pool(self, name: str, config: BulkheadConfig) -> ThreadPoolBulkhead:
        """
        Add a thread pool bulkhead.

        Args:
            name: Thread pool name
            config: Bulkhead configuration

        Returns:
            Created thread pool bulkhead
        """
        thread_pool = ThreadPoolBulkhead(config)
        self.thread_pools[name] = thread_pool
        return thread_pool

    def add_resource_limiter(self, name: str, max_resources: int) -> ResourceLimiter:
        """
        Add a resource limiter.

        Args:
            name: Limiter name
            max_resources: Maximum resources

        Returns:
            Created resource limiter
        """
        limiter = ResourceLimiter(max_resources)
        self.resource_limiters[name] = limiter
        return limiter

    def get_bulkhead(self, name: str) -> Bulkhead | None:
        """Get bulkhead by name."""
        return self.bulkheads.get(name)

    def get_thread_pool(self, name: str) -> ThreadPoolBulkhead | None:
        """Get thread pool by name."""
        return self.thread_pools.get(name)

    def get_resource_limiter(self, name: str) -> ResourceLimiter | None:
        """Get resource limiter by name."""
        return self.resource_limiters.get(name)

    async def reset_all(self) -> None:
        """Reset all bulkheads."""
        for bulkhead in self.bulkheads.values():
            await bulkhead.reset()

    def shutdown_all(self) -> None:
        """Shutdown all thread pools."""
        for thread_pool in self.thread_pools.values():
            thread_pool.shutdown()


# Global isolation manager
isolation_manager = IsolationManager()
