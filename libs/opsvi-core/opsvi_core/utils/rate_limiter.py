"""Rate limiting utilities for opsvi-core.

Provides rate limiting mechanisms using token bucket algorithm
for controlling request rates and preventing system overload.
"""

import asyncio
import functools
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from opsvi_foundation import ComponentError

from ..config.settings import CoreConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimitExceeded(ComponentError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: Optional[float] = None
    ):
        super().__init__(message)
        self.retry_after = retry_after


class TimeWindow(Enum):
    """Time window units for rate limiting."""

    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int
    time_window: TimeWindow
    burst_size: Optional[int] = None
    key_func: Optional[Callable[..., str]] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if self.burst_size is None:
            self.burst_size = self.max_requests
        if self.burst_size < self.max_requests:
            self.burst_size = self.max_requests


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(
        self, capacity: int, refill_rate: float, burst_size: Optional[int] = None
    ):
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
            burst_size: Maximum burst size (defaults to capacity)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.burst_size = burst_size or capacity
        self._tokens = float(capacity)
        self._last_refill = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self.refill_rate

        self._tokens = min(self.capacity, self._tokens + tokens_to_add)
        self._last_refill = now

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, wait_time_if_failed)
        """
        with self._lock:
            self._refill()

            if tokens > self.burst_size:
                # Request exceeds burst size
                return False, float("inf")

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True, 0.0
            else:
                # Calculate wait time
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.refill_rate
                return False, wait_time

    def available_tokens(self) -> int:
        """Get number of available tokens.

        Returns:
            Number of available tokens
        """
        with self._lock:
            self._refill()
            return int(self._tokens)

    def reset(self) -> None:
        """Reset the bucket to full capacity."""
        with self._lock:
            self._tokens = float(self.capacity)
            self._last_refill = time.time()


class RateLimiter:
    """Rate limiter with support for multiple keys and windows."""

    def __init__(
        self,
        max_requests: int,
        time_window: TimeWindow = TimeWindow.MINUTE,
        burst_size: Optional[int] = None,
        enable_multi_tenant: bool = False,
        config: Optional[CoreConfig] = None,
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window for rate limiting
            burst_size: Maximum burst size
            enable_multi_tenant: Enable per-key rate limiting
            config: Optional CoreConfig
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self.enable_multi_tenant = enable_multi_tenant
        self.config = config or CoreConfig()

        # Calculate refill rate (tokens per second)
        self.refill_rate = max_requests / time_window.value

        # Storage for token buckets
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()

        # Statistics
        self._stats = defaultdict(lambda: {"allowed": 0, "rejected": 0, "total": 0})

        # Create default bucket if not multi-tenant
        if not enable_multi_tenant:
            self._buckets["__default__"] = TokenBucket(
                capacity=max_requests,
                refill_rate=self.refill_rate,
                burst_size=burst_size,
            )

    def _get_bucket(self, key: str = "__default__") -> TokenBucket:
        """Get or create a token bucket for a key.

        Args:
            key: The key for the bucket

        Returns:
            Token bucket instance
        """
        if not self.enable_multi_tenant:
            key = "__default__"

        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=self.max_requests,
                    refill_rate=self.refill_rate,
                    burst_size=self.burst_size,
                )
            return self._buckets[key]

    def check_limit(
        self, key: Optional[str] = None, tokens: int = 1
    ) -> tuple[bool, Optional[float]]:
        """Check if request is within rate limit.

        Args:
            key: Optional key for multi-tenant rate limiting
            tokens: Number of tokens to consume

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        bucket_key = key or "__default__"
        bucket = self._get_bucket(bucket_key)

        allowed, wait_time = bucket.consume(tokens)

        # Update statistics
        self._stats[bucket_key]["total"] += 1
        if allowed:
            self._stats[bucket_key]["allowed"] += 1
        else:
            self._stats[bucket_key]["rejected"] += 1

        return allowed, wait_time if not allowed else None

    async def wait_if_needed(self, key: Optional[str] = None, tokens: int = 1) -> None:
        """Wait if rate limit is exceeded.

        Args:
            key: Optional key for multi-tenant rate limiting
            tokens: Number of tokens to consume

        Raises:
            RateLimitExceeded: If wait time is too long
        """
        max_wait = 60.0  # Maximum wait time in seconds

        while True:
            allowed, wait_time = self.check_limit(key, tokens)

            if allowed:
                return

            if wait_time > max_wait:
                raise RateLimitExceeded(
                    f"Rate limit exceeded, retry after {wait_time:.2f} seconds",
                    retry_after=wait_time,
                )

            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limit for a key.

        Args:
            key: Optional key to reset (None resets all)
        """
        with self._lock:
            if key is None:
                for bucket in self._buckets.values():
                    bucket.reset()
            elif key in self._buckets:
                self._buckets[key].reset()

    def get_remaining(self, key: Optional[str] = None) -> int:
        """Get remaining requests for a key.

        Args:
            key: Optional key for multi-tenant rate limiting

        Returns:
            Number of remaining requests
        """
        bucket_key = key or "__default__"
        bucket = self._get_bucket(bucket_key)
        return bucket.available_tokens()

    def get_stats(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiter statistics.

        Args:
            key: Optional key to get stats for (None returns all)

        Returns:
            Dictionary with statistics
        """
        if key:
            stats = dict(
                self._stats.get(key, {"allowed": 0, "rejected": 0, "total": 0})
            )
            stats["remaining"] = self.get_remaining(key)
            return stats
        else:
            all_stats = {}
            for k in list(self._buckets.keys()):
                all_stats[k] = self.get_stats(k)
            return all_stats


def rate_limit(
    max_requests: int,
    time_window: TimeWindow = TimeWindow.MINUTE,
    burst_size: Optional[int] = None,
    key_func: Optional[Callable[..., str]] = None,
    raise_on_limit: bool = True,
    config: Optional[CoreConfig] = None,
) -> Callable:
    """Decorator for rate limiting functions.

    Args:
        max_requests: Maximum requests per time window
        time_window: Time window for rate limiting
        burst_size: Maximum burst size
        key_func: Function to extract key from arguments
        raise_on_limit: Raise exception on limit (vs. wait)
        config: Optional CoreConfig

    Returns:
        Decorated function with rate limiting

    Example:
        @rate_limit(max_requests=100, time_window=TimeWindow.MINUTE)
        async def api_endpoint(user_id: str):
            return await process_request(user_id)
    """
    # Create rate limiter instance
    limiter = RateLimiter(
        max_requests=max_requests,
        time_window=time_window,
        burst_size=burst_size,
        enable_multi_tenant=key_func is not None,
        config=config,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            # Extract key if key_func provided
            key = None
            if key_func:
                try:
                    key = key_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error extracting rate limit key: {e}")
                    key = "__error__"

            # Check rate limit
            allowed, wait_time = limiter.check_limit(key)

            if not allowed:
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for key '{key or '__default__'}', retry after {wait_time:.2f} seconds",
                        retry_after=wait_time,
                    )
                else:
                    await asyncio.sleep(wait_time)
                    # Retry after waiting
                    return await async_wrapper(*args, **kwargs)

            # Execute function
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            # Extract key if key_func provided
            key = None
            if key_func:
                try:
                    key = key_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error extracting rate limit key: {e}")
                    key = "__error__"

            # Check rate limit
            allowed, wait_time = limiter.check_limit(key)

            if not allowed:
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for key '{key or '__default__'}', retry after {wait_time:.2f} seconds",
                        retry_after=wait_time,
                    )
                else:
                    time.sleep(wait_time)
                    # Retry after waiting
                    return sync_wrapper(*args, **kwargs)

            # Execute function
            return func(*args, **kwargs)

        # Attach limiter for inspection
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.rate_limiter = limiter

        return wrapper

    return decorator


class RateLimiterManager:
    """Manager for multiple rate limiters."""

    def __init__(self):
        """Initialize rate limiter manager."""
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = Lock()

    def create_limiter(
        self,
        name: str,
        max_requests: int,
        time_window: TimeWindow = TimeWindow.MINUTE,
        burst_size: Optional[int] = None,
        enable_multi_tenant: bool = False,
    ) -> RateLimiter:
        """Create and register a rate limiter.

        Args:
            name: Name for the rate limiter
            max_requests: Maximum requests per time window
            time_window: Time window for rate limiting
            burst_size: Maximum burst size
            enable_multi_tenant: Enable per-key rate limiting

        Returns:
            Rate limiter instance
        """
        limiter = RateLimiter(
            max_requests=max_requests,
            time_window=time_window,
            burst_size=burst_size,
            enable_multi_tenant=enable_multi_tenant,
        )

        with self._lock:
            self._limiters[name] = limiter

        logger.info(f"Created rate limiter: {name}")
        return limiter

    def get(self, name: str) -> Optional[RateLimiter]:
        """Get a rate limiter by name.

        Args:
            name: Name of the rate limiter

        Returns:
            Rate limiter instance or None
        """
        with self._lock:
            return self._limiters.get(name)

    def remove(self, name: str) -> None:
        """Remove a rate limiter.

        Args:
            name: Name of the rate limiter
        """
        with self._lock:
            if name in self._limiters:
                del self._limiters[name]
                logger.info(f"Removed rate limiter: {name}")

    def reset_all(self) -> None:
        """Reset all rate limiters."""
        with self._lock:
            for limiter in self._limiters.values():
                limiter.reset()

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all rate limiters.

        Returns:
            Dictionary of statistics by limiter name
        """
        with self._lock:
            return {
                name: limiter.get_stats() for name, limiter in self._limiters.items()
            }


# Global rate limiter manager
_manager = RateLimiterManager()


def get_rate_limiter_manager() -> RateLimiterManager:
    """Get the global rate limiter manager.

    Returns:
        Rate limiter manager instance
    """
    return _manager


# Integration with EventBus to prevent flooding
class EventBusRateLimiter:
    """Rate limiter specifically for EventBus integration."""

    def __init__(
        self,
        event_bus: Any,  # Avoid circular import
        max_events_per_second: int = 100,
        max_burst: int = 200,
    ):
        """Initialize EventBus rate limiter.

        Args:
            event_bus: EventBus instance to protect
            max_events_per_second: Maximum events per second
            max_burst: Maximum burst size
        """
        self.event_bus = event_bus
        self.limiter = RateLimiter(
            max_requests=max_events_per_second,
            time_window=TimeWindow.SECOND,
            burst_size=max_burst,
            enable_multi_tenant=True,
        )

        # Store original publish method
        self._original_publish = event_bus.publish

        # Replace with rate-limited version
        event_bus.publish = self._rate_limited_publish

    async def _rate_limited_publish(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> None:
        """Rate-limited publish method.

        Args:
            event_type: Type of event
            event_data: Event data

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Use event type as rate limit key
        allowed, wait_time = self.limiter.check_limit(event_type)

        if not allowed:
            logger.warning(
                f"Event bus rate limit exceeded for event type '{event_type}', "
                f"retry after {wait_time:.2f} seconds"
            )
            raise RateLimitExceeded(
                f"Event publishing rate limit exceeded for '{event_type}'",
                retry_after=wait_time,
            )

        # Call original publish method
        await self._original_publish(event_type, event_data)

    def restore_original(self) -> None:
        """Restore original EventBus publish method."""
        self.event_bus.publish = self._original_publish


__all__ = [
    "RateLimiter",
    "RateLimitExceeded",
    "RateLimitConfig",
    "TimeWindow",
    "TokenBucket",
    "rate_limit",
    "RateLimiterManager",
    "get_rate_limiter_manager",
    "EventBusRateLimiter",
]
