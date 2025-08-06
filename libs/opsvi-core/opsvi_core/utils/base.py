"""
Base utilities for OPSVI Core.

Provides common utility functions and helpers.
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from opsvi_foundation import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            e,
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            e,
                            current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def timing_decorator(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to measure function execution time."""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug("Function %s completed in %.3fs", func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.debug(
                "Function %s failed after %.3fs: %s", func.__name__, duration, e
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug("Function %s completed in %.3fs", func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.debug(
                "Function %s failed after %.3fs: %s", func.__name__, duration, e
            )
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class AsyncLock:
    """Async context manager for locking."""

    def __init__(self):
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()


class RateLimiter:
    """Simple rate limiter."""

    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire permission to make a call."""
        async with self._lock:
            now = time.time()
            # Remove old calls outside the time window
            self._calls = [
                call_time
                for call_time in self._calls
                if now - call_time < self.time_window
            ]

            if len(self._calls) < self.max_calls:
                self._calls.append(now)
                return True
            return False

    async def wait_and_acquire(self) -> None:
        """Wait until permission is available and acquire it."""
        while not await self.acquire():
            await asyncio.sleep(0.1)


def safe_dict_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation."""
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def chunk_list(lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def gather_with_limit(limit: int, *coroutines) -> list[Any]:
    """Run coroutines with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)

    async def limited_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*[limited_coro(coro) for coro in coroutines])


def format_bytes(bytes_count: int) -> str:
    """Format bytes in human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_seconds = seconds % 3600
        minutes = int(remaining_seconds // 60)
        return f"{hours}h {minutes}m"
