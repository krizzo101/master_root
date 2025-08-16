"""Retry and backoff utilities for opsvi-foundation.

Provides decorators and strategies for retrying operations with
configurable backoff strategies.
"""

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Optional, Type, TypeVar, Tuple

from ..config.settings import FoundationConfig
from ..core.base import ComponentError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BackoffStrategy:
    """Base class for backoff strategies."""

    def __init__(self, base_delay: float = 1.0):
        """Initialize backoff strategy.

        Args:
            base_delay: Base delay in seconds
        """
        self.base_delay = base_delay
        self.attempt = 0

    def next_delay(self) -> float:
        """Get the next delay duration.

        Returns:
            Delay in seconds for the next retry
        """
        self.attempt += 1
        return self._calculate_delay()

    def _calculate_delay(self) -> float:
        """Calculate the actual delay for the current attempt.

        Returns:
            Delay in seconds
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Reset the backoff strategy to initial state."""
        self.attempt = 0


class ExponentialBackoff(BackoffStrategy):
    """Exponential backoff strategy with optional jitter."""

    def __init__(
        self,
        base_delay: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        """Initialize exponential backoff strategy.

        Args:
            base_delay: Base delay in seconds
            factor: Multiplication factor for each retry
            max_delay: Maximum delay in seconds
            jitter: Whether to add random jitter to delays
        """
        super().__init__(base_delay)
        self.factor = factor
        self.max_delay = max_delay
        self.jitter = jitter

    def _calculate_delay(self) -> float:
        """Calculate exponential backoff delay with optional jitter.

        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.factor ** (self.attempt - 1)), self.max_delay
        )

        if self.jitter:
            # Add random jitter up to 25% of the delay
            jitter_amount = delay * 0.25 * random.random()
            delay = delay + jitter_amount

        return delay


class LinearBackoff(BackoffStrategy):
    """Linear backoff strategy."""

    def __init__(
        self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 60.0
    ):
        """Initialize linear backoff strategy.

        Args:
            base_delay: Base delay in seconds
            increment: Increment for each retry
            max_delay: Maximum delay in seconds
        """
        super().__init__(base_delay)
        self.increment = increment
        self.max_delay = max_delay

    def _calculate_delay(self) -> float:
        """Calculate linear backoff delay.

        Returns:
            Delay in seconds
        """
        delay = self.base_delay + (self.increment * (self.attempt - 1))
        return min(delay, self.max_delay)


class ConstantBackoff(BackoffStrategy):
    """Constant delay backoff strategy."""

    def _calculate_delay(self) -> float:
        """Return constant delay.

        Returns:
            Constant delay in seconds
        """
        return self.base_delay


def retry(
    max_attempts: Optional[int] = None,
    delay: Optional[float] = None,
    backoff: Optional[BackoffStrategy] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    config: Optional[FoundationConfig] = None,
) -> Callable:
    """Decorator for retrying functions with configurable backoff.

    Works with both synchronous and asynchronous functions.

    Args:
        max_attempts: Maximum number of attempts (uses config default if None)
        delay: Initial delay between retries (uses config default if None)
        backoff: Backoff strategy to use (creates exponential if None)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt)
        config: Optional FoundationConfig for defaults

    Returns:
        Decorated function with retry capability

    Example:
        @retry(max_attempts=3, delay=1.0)
        async def fetch_data():
            # May fail but will be retried
            return await api_call()
    """
    # Use provided config or create default
    if config is None:
        config = FoundationConfig(library_name="retry", version="1.0.0")

    # Use provided values or config defaults
    actual_max_attempts = max_attempts or config.max_retries
    actual_delay = delay or config.retry_delay

    # Create backoff strategy if not provided
    if backoff is None:
        backoff = ExponentialBackoff(
            base_delay=actual_delay, factor=config.backoff_factor
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Actual decorator implementation."""

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            """Async wrapper with retry logic."""
            backoff.reset()
            last_exception = None

            for attempt in range(1, actual_max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == actual_max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {actual_max_attempts} attempts: {e}"
                        )
                        raise

                    delay_seconds = backoff.next_delay()
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{actual_max_attempts}), "
                        f"retrying in {delay_seconds:.2f}s: {e}"
                    )

                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    await asyncio.sleep(delay_seconds)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise ComponentError(f"Retry logic error in {func.__name__}")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Synchronous wrapper with retry logic."""
            import time

            backoff.reset()
            last_exception = None

            for attempt in range(1, actual_max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == actual_max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {actual_max_attempts} attempts: {e}"
                        )
                        raise

                    delay_seconds = backoff.next_delay()
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{actual_max_attempts}), "
                        f"retrying in {delay_seconds:.2f}s: {e}"
                    )

                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    time.sleep(delay_seconds)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise ComponentError(f"Retry logic error in {func.__name__}")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_async(
    max_attempts: Optional[int] = None,
    delay: Optional[float] = None,
    backoff: Optional[BackoffStrategy] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    config: Optional[FoundationConfig] = None,
) -> Callable:
    """Async-only version of retry decorator.

    This is a convenience function that ensures the decorated function
    is treated as async even if the decorator can't auto-detect it.

    Args:
        Same as retry()

    Returns:
        Decorated async function with retry capability
    """
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        exceptions=exceptions,
        on_retry=on_retry,
        config=config,
    )


class RetryContext:
    """Context manager for retry operations with manual control.

    Useful when you need more control over the retry loop.

    Example:
        async with RetryContext(max_attempts=3) as retry_ctx:
            while retry_ctx.should_retry():
                try:
                    result = await api_call()
                    retry_ctx.success()
                    return result
                except Exception as e:
                    await retry_ctx.handle_failure(e)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff: Optional[BackoffStrategy] = None,
        config: Optional[FoundationConfig] = None,
    ):
        """Initialize retry context.

        Args:
            max_attempts: Maximum number of attempts
            backoff: Backoff strategy to use
            config: Optional FoundationConfig for defaults
        """
        if config is None:
            config = FoundationConfig(library_name="retry", version="1.0.0")

        self.max_attempts = max_attempts or config.max_retries
        self.backoff = backoff or ExponentialBackoff(
            base_delay=config.retry_delay, factor=config.backoff_factor
        )
        self.attempt = 0
        self.succeeded = False
        self.last_exception: Optional[Exception] = None

    def should_retry(self) -> bool:
        """Check if another retry attempt should be made.

        Returns:
            True if should retry, False otherwise
        """
        return not self.succeeded and self.attempt < self.max_attempts

    def success(self) -> None:
        """Mark the operation as successful."""
        self.succeeded = True

    async def handle_failure(self, exception: Exception) -> None:
        """Handle a failure and prepare for retry.

        Args:
            exception: The exception that occurred

        Raises:
            The exception if max attempts reached
        """
        self.attempt += 1
        self.last_exception = exception

        if self.attempt >= self.max_attempts:
            logger.error(f"Max retry attempts ({self.max_attempts}) reached")
            raise exception

        delay = self.backoff.next_delay()
        logger.warning(
            f"Attempt {self.attempt}/{self.max_attempts} failed, "
            f"retrying in {delay:.2f}s: {exception}"
        )
        await asyncio.sleep(delay)

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass

    async def __aenter__(self):
        """Async enter context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit context manager."""
        pass


__all__ = [
    "retry",
    "retry_async",
    "BackoffStrategy",
    "ExponentialBackoff",
    "LinearBackoff",
    "ConstantBackoff",
    "RetryContext",
]
