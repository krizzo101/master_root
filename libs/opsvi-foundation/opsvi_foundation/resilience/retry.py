"""
Retry mechanisms with exponential backoff.

Provides configurable retry logic with various backoff strategies.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


class BackoffStrategy(ABC):
    """Abstract base class for backoff strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        pass


class ExponentialBackoff(BackoffStrategy):
    """Exponential backoff with optional jitter."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0,
                 multiplier: float = 2.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter to avoid thundering herd
            delay *= (0.5 + random.random() * 0.5)

        return delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = None
    exceptions: tuple[type, ...] = (Exception,)
    timeout: Optional[float] = None

    def __post_init__(self):
        if self.backoff_strategy is None:
            self.backoff_strategy = ExponentialBackoff()


class RetryExecutor:
    """Executes functions with retry logic."""

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                # Execute with optional timeout
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        self._execute_function(func, *args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await self._execute_function(func, *args, **kwargs)

                return result

            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(f"Function timed out after {self.config.timeout} seconds")
            except self.config.exceptions as e:
                last_exception = e
            except Exception as e:
                # Unexpected exception, don't retry
                raise

            # Don't wait after the last attempt
            if attempt < self.config.max_attempts - 1:
                delay = self.config.backoff_strategy.get_delay(attempt)
                await asyncio.sleep(delay)

        # All attempts exhausted
        raise RuntimeError(f"Function failed after {self.config.max_attempts} attempts: {last_exception}")

    async def _execute_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)


def retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to functions."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            executor = RetryExecutor(config)
            return await executor.execute(func, *args, **kwargs)

        return wrapper
    return decorator
