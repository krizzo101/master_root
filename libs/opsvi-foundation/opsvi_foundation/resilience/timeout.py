"""
Timeout management utilities.

Provides configurable timeouts and deadline propagation.
"""

from __future__ import annotations

import asyncio
import builtins
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TypeVar

from pydantic import BaseModel

from ..observability import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class TimeoutConfig(BaseModel):
    """Configuration for timeout operations."""

    default_timeout: float = 30.0
    max_timeout: float = 300.0
    min_timeout: float = 0.1


class TimeoutError(Exception):
    """Raised when an operation times out."""

    def __init__(self, timeout: float, operation: str = "operation"):
        self.timeout = timeout
        self.operation = operation
        super().__init__(f"{operation} timed out after {timeout}s")


class Timeout:
    """Timeout management with deadline propagation."""

    def __init__(self, config: TimeoutConfig | None = None):
        self.config = config or TimeoutConfig()
        logger.debug("Initialized Timeout", config=self.config.model_dump())

    @asynccontextmanager
    async def timeout_context(self, timeout: float, operation: str = "operation"):
        """Async context manager for timeout operations.

        Args:
            timeout: Timeout in seconds
            operation: Operation name for error messages

        Raises:
            TimeoutError: If operation times out
        """
        if timeout < self.config.min_timeout:
            timeout = self.config.min_timeout
        elif timeout > self.config.max_timeout:
            timeout = self.config.max_timeout

        start_time = time.time()
        logger.debug("Starting timeout context", timeout=timeout, operation=operation)

        try:
            async with asyncio.timeout(timeout):
                yield

        except builtins.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(
                "Operation timed out",
                timeout=timeout,
                elapsed=elapsed,
                operation=operation,
            )
            raise TimeoutError(timeout, operation)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "Operation failed",
                error=str(e),
                elapsed=elapsed,
                operation=operation,
            )
            raise

        else:
            elapsed = time.time() - start_time
            logger.debug("Operation completed", elapsed=elapsed, operation=operation)

    async def run_with_timeout(
        self,
        coro: Awaitable[T],
        timeout: float | None = None,
        operation: str = "operation",
    ) -> T:
        """Run coroutine with timeout.

        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds, uses default if None
            operation: Operation name for error messages

        Returns:
            Result of the coroutine

        Raises:
            TimeoutError: If operation times out
        """
        if timeout is None:
            timeout = self.config.default_timeout

        async with self.timeout_context(timeout, operation):
            return await coro

    def timeout_decorator(
        self,
        timeout: float | None = None,
        operation: str | None = None,
    ):
        """Decorator to add timeout to async functions.

        Args:
            timeout: Timeout in seconds, uses default if None
            operation: Operation name, uses function name if None
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            async def wrapper(*args, **kwargs) -> T:
                op_name = operation or func.__name__
                coro = func(*args, **kwargs)
                return await self.run_with_timeout(coro, timeout, op_name)

            return wrapper

        return decorator


class DeadlineContext:
    """Context for deadline propagation across operations."""

    def __init__(self, deadline: float):
        self.deadline = deadline
        self.start_time = time.time()

    def remaining_time(self) -> float:
        """Get remaining time until deadline.

        Returns:
            Remaining seconds, 0 if deadline passed
        """
        remaining = self.deadline - time.time()
        return max(0.0, remaining)

    def is_expired(self) -> bool:
        """Check if deadline has passed.

        Returns:
            True if deadline has passed
        """
        return time.time() >= self.deadline

    @asynccontextmanager
    async def timeout_remaining(self, operation: str = "operation"):
        """Create timeout context for remaining time.

        Args:
            operation: Operation name for error messages

        Raises:
            TimeoutError: If deadline has passed or operation times out
        """
        remaining = self.remaining_time()

        if remaining <= 0:
            logger.error("Deadline already passed", operation=operation)
            raise TimeoutError(0, f"deadline for {operation}")

        timeout_mgr = Timeout()
        async with timeout_mgr.timeout_context(remaining, operation):
            yield


# Global timeout instance
timeout_manager = Timeout()


def with_timeout(timeout: float | None = None, operation: str | None = None):
    """Decorator to add timeout to async functions.

    Args:
        timeout: Timeout in seconds
        operation: Operation name
    """
    return timeout_manager.timeout_decorator(timeout, operation)


async def wait_for(
    coro: Awaitable[T],
    timeout: float,
    operation: str = "operation",
) -> T:
    """Wait for coroutine with timeout.

    Args:
        coro: Coroutine to wait for
        timeout: Timeout in seconds
        operation: Operation name

    Returns:
        Result of the coroutine

    Raises:
        TimeoutError: If operation times out
    """
    return await timeout_manager.run_with_timeout(coro, timeout, operation)
