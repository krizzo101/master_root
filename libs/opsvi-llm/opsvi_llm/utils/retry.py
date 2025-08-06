"""
Retry utilities for OPSVI LLM Library.

Provides exponential backoff retry logic for handling transient failures.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Type variable for function return type
T = TypeVar("T")

# Common exceptions that should trigger retries
RETRYABLE_EXCEPTIONS = (Exception,)  # Broad exception handling - customize as needed


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: type | tuple = RETRYABLE_EXCEPTIONS,
    log_retries: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that adds exponential backoff retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exceptions: Exception types that should trigger retries
        log_retries: Whether to log retry attempts

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            @retry(
                stop=stop_after_attempt(max_retries + 1),  # +1 for initial attempt
                wait=wait_exponential(multiplier=base_delay, max=max_delay),
                retry=retry_if_exception_type(exceptions),
                before_sleep=(
                    before_sleep_log(logger, logging.WARNING) if log_retries else None
                ),
                after=after_log(logger, logging.INFO) if log_retries else None,
            )
            async def _retry_func() -> T:
                return await func(*args, **kwargs)

            return await _retry_func()

        return wrapper

    return decorator


def retry_sync_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: type | tuple = RETRYABLE_EXCEPTIONS,
    log_retries: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that adds exponential backoff retry logic to synchronous functions.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exceptions: Exception types that should trigger retries
        log_retries: Whether to log retry attempts

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            @retry(
                stop=stop_after_attempt(max_retries + 1),  # +1 for initial attempt
                wait=wait_exponential(multiplier=base_delay, max=max_delay),
                retry=retry_if_exception_type(exceptions),
                before_sleep=(
                    before_sleep_log(logger, logging.WARNING) if log_retries else None
                ),
                after=after_log(logger, logging.INFO) if log_retries else None,
            )
            def _retry_func() -> T:
                return func(*args, **kwargs)

            return _retry_func()

        return wrapper

    return decorator


class RetryConfig:
    """Configuration class for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: type | tuple = RETRYABLE_EXCEPTIONS,
        log_retries: bool = True,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exceptions: Exception types that should trigger retries
            log_retries: Whether to log retry attempts
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = exceptions
        self.log_retries = log_retries

    def get_retry_decorator(self, is_async: bool = True) -> Callable:
        """
        Get the appropriate retry decorator.

        Args:
            is_async: Whether the function is async

        Returns:
            Retry decorator function
        """
        if is_async:
            return retry_with_backoff(
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                exceptions=self.exceptions,
                log_retries=self.log_retries,
            )
        else:
            return retry_sync_with_backoff(
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                exceptions=self.exceptions,
                log_retries=self.log_retries,
            )
