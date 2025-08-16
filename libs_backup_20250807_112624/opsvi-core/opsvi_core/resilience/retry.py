"""
Retry mechanisms with exponential backoff for opsvi-core.

Provides configurable retry logic with various backoff strategies.
"""

import asyncio
import builtins
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar

from ..core.exceptions import ExternalServiceError, TimeoutError
from ..core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BackoffStrategy(ABC):
    """Abstract base class for backoff strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        pass


class ExponentialBackoff(BackoffStrategy):
    """Exponential backoff with optional jitter."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (self.multiplier**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter to avoid thundering herd
            delay *= 0.5 + random.random() * 0.5

        return delay


class LinearBackoff(BackoffStrategy):
    """Linear backoff strategy."""

    def __init__(
        self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 30.0
    ):
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay."""
        delay = self.base_delay + (attempt * self.increment)
        return min(delay, self.max_delay)


class FixedBackoff(BackoffStrategy):
    """Fixed delay strategy."""

    def __init__(self, delay: float = 1.0):
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = None
    exceptions: tuple[type, ...] = (Exception,)
    timeout: float | None = None

    def __post_init__(self):
        if self.backoff_strategy is None:
            self.backoff_strategy = ExponentialBackoff()


class RetryError(ExternalServiceError):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class RetryExecutor:
    """Executes functions with retry logic."""

    def __init__(self, config: RetryConfig):
        self.config = config
        logger.info("RetryExecutor initialized", max_attempts=config.max_attempts)

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                start_time = time.time()

                # Execute with optional timeout
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        self._execute_function(func, *args, **kwargs),
                        timeout=self.config.timeout,
                    )
                else:
                    result = await self._execute_function(func, *args, **kwargs)

                execution_time = time.time() - start_time
                logger.info(
                    "Function executed successfully",
                    attempt=attempt + 1,
                    execution_time=execution_time,
                )
                return result

            except builtins.TimeoutError:
                last_exception = TimeoutError(
                    f"Function timed out after {self.config.timeout} seconds"
                )
                logger.warning(
                    "Function timed out",
                    attempt=attempt + 1,
                    timeout=self.config.timeout,
                )
            except self.config.exceptions as e:
                last_exception = e
                logger.warning("Function failed", attempt=attempt + 1, error=str(e))
            except Exception as e:
                # Unexpected exception, don't retry
                logger.error("Unexpected error, not retrying", error=str(e))
                raise

            # Don't wait after the last attempt
            if attempt < self.config.max_attempts - 1:
                delay = self.config.backoff_strategy.get_delay(attempt)
                logger.debug(
                    "Waiting before retry", delay=delay, next_attempt=attempt + 2
                )
                await asyncio.sleep(delay)

        # All attempts exhausted
        error_msg = f"Function failed after {self.config.max_attempts} attempts"
        logger.error(error_msg, last_error=str(last_exception))
        raise RetryError(error_msg, self.config.max_attempts, last_exception)

    async def _execute_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)


def retry(config: RetryConfig | None = None):
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


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type, ...] = (Exception,),
    timeout: float | None = None,
):
    """Convenience decorator for exponential backoff retry."""
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_strategy=ExponentialBackoff(base_delay, max_delay, multiplier, jitter),
        exceptions=exceptions,
        timeout=timeout,
    )
    return retry(config)


def retry_with_linear_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    increment: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple[type, ...] = (Exception,),
    timeout: float | None = None,
):
    """Convenience decorator for linear backoff retry."""
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_strategy=LinearBackoff(base_delay, increment, max_delay),
        exceptions=exceptions,
        timeout=timeout,
    )
    return retry(config)


def retry_with_fixed_delay(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type, ...] = (Exception,),
    timeout: float | None = None,
):
    """Convenience decorator for fixed delay retry."""
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_strategy=FixedBackoff(delay),
        exceptions=exceptions,
        timeout=timeout,
    )
    return retry(config)
