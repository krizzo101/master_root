"""
Rate limiting utilities and implementations.

Provides token bucket, sliding window, and distributed rate limiting
for controlling request rates and preventing abuse.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from opsvi_foundation.patterns import ComponentError


class RateLimitError(ComponentError):
    """Raised when rate limit is exceeded."""


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    rate: int = 100  # requests per time window
    window: float = 60.0  # time window in seconds
    burst_size: int = 10  # burst allowance
    distributed: bool = False  # whether to use distributed rate limiting


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: int, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        Acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire
            timeout: Timeout for acquisition

        Returns:
            True if tokens acquired, False if timeout
        """
        async with self._lock:
            await self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if timeout is None:
                return False

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            if wait_time > timeout:
                return False

            # Wait for tokens
            await asyncio.sleep(wait_time)
            await self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    @property
    def available_tokens(self) -> float:
        """Get number of available tokens."""
        return self.tokens


class SlidingWindow:
    """Sliding window rate limiter implementation."""

    def __init__(self, rate: int, window: float):
        """
        Initialize sliding window.

        Args:
            rate: Maximum requests per window
            window: Time window in seconds
        """
        self.rate = rate
        self.window = window
        self.requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make request.

        Args:
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        async with self._lock:
            now = time.time()

            # Remove expired requests
            cutoff = now - self.window
            self.requests = [
                req_time for req_time in self.requests if req_time > cutoff
            ]

            if len(self.requests) < self.rate:
                self.requests.append(now)
                return True

            if timeout is None:
                return False

            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = oldest_request + self.window - now

            if wait_time > timeout:
                return False

            # Wait and try again
            await asyncio.sleep(wait_time)
            return await self.acquire(timeout - wait_time)

    @property
    def current_requests(self) -> int:
        """Get current number of requests in window."""
        now = time.time()
        cutoff = now - self.window
        return len([req_time for req_time in self.requests if req_time > cutoff])


class FixedWindow:
    """Fixed window rate limiter implementation."""

    def __init__(self, rate: int, window: float):
        """
        Initialize fixed window.

        Args:
            rate: Maximum requests per window
            window: Time window in seconds
        """
        self.rate = rate
        self.window = window
        self.current_window = int(time.time() // window)
        self.request_count = 0
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make request.

        Args:
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        async with self._lock:
            now = time.time()
            window_start = int(now // self.window)

            # Reset if new window
            if window_start > self.current_window:
                self.current_window = window_start
                self.request_count = 0

            if self.request_count < self.rate:
                self.request_count += 1
                return True

            if timeout is None:
                return False

            # Calculate wait time to next window
            wait_time = (window_start + 1) * self.window - now

            if wait_time > timeout:
                return False

            # Wait for next window
            await asyncio.sleep(wait_time)
            return await self.acquire(timeout - wait_time)

    @property
    def remaining_requests(self) -> int:
        """Get remaining requests in current window."""
        return max(0, self.rate - self.request_count)


class LeakyBucket:
    """Leaky bucket rate limiter implementation."""

    def __init__(self, rate: int, capacity: int):
        """
        Initialize leaky bucket.

        Args:
            rate: Requests per second (leak rate)
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.current_level = 0
        self.last_leak = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make request.

        Args:
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        async with self._lock:
            await self._leak()

            if self.current_level < self.capacity:
                self.current_level += 1
                return True

            if timeout is None:
                return False

            # Calculate wait time
            wait_time = (self.current_level - self.capacity + 1) / self.rate

            if wait_time > timeout:
                return False

            # Wait for space
            await asyncio.sleep(wait_time)
            await self._leak()

            if self.current_level < self.capacity:
                self.current_level += 1
                return True

            return False

    async def _leak(self) -> None:
        """Leak water from bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_leak
        leaked = elapsed * self.rate

        self.current_level = max(0, self.current_level - leaked)
        self.last_leak = now

    @property
    def current_level(self) -> float:
        """Get current bucket level."""
        return self.current_level


class RateLimiter:
    """Main rate limiter class supporting multiple strategies."""

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiter configuration
        """
        self.config = config

        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.limiter = TokenBucket(config.rate, config.burst_size)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.limiter = SlidingWindow(config.rate, config.window)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            self.limiter = FixedWindow(config.rate, config.window)
        elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            self.limiter = LeakyBucket(config.rate, config.burst_size)
        else:
            raise ValueError(f"Unsupported rate limiting strategy: {config.strategy}")

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make request.

        Args:
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        return await self.limiter.acquire(timeout=timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.acquire():
            raise RateLimitError("Rate limit exceeded")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""


class DistributedRateLimiter:
    """Distributed rate limiter for multi-instance deployments."""

    def __init__(self, config: RateLimitConfig, storage_backend: Any = None):
        """
        Initialize distributed rate limiter.

        Args:
            config: Rate limiter configuration
            storage_backend: Storage backend for distributed state
        """
        self.config = config
        self.storage_backend = storage_backend
        self.local_limiter = RateLimiter(config)

    async def acquire(self, key: str, timeout: float | None = None) -> bool:
        """
        Acquire permission for a specific key.

        Args:
            key: Rate limiting key (e.g., user ID, IP address)
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        if self.storage_backend is None:
            # Fall back to local rate limiting
            return await self.local_limiter.acquire(timeout)

        # In a real implementation, this would coordinate with the storage backend
        # to ensure rate limits are enforced across all instances
        # For now, use local rate limiting
        return await self.local_limiter.acquire(timeout)


class RateLimitManager:
    """Manager for multiple rate limiters."""

    def __init__(self):
        """Initialize rate limit manager."""
        self.limiters: dict[str, RateLimiter] = {}
        self.distributed_limiters: dict[str, DistributedRateLimiter] = {}

    def add_limiter(self, name: str, config: RateLimitConfig) -> RateLimiter:
        """
        Add a rate limiter.

        Args:
            name: Limiter name
            config: Rate limiter configuration

        Returns:
            Created rate limiter
        """
        limiter = RateLimiter(config)
        self.limiters[name] = limiter
        return limiter

    def add_distributed_limiter(
        self,
        name: str,
        config: RateLimitConfig,
        storage_backend: Any = None,
    ) -> DistributedRateLimiter:
        """
        Add a distributed rate limiter.

        Args:
            name: Limiter name
            config: Rate limiter configuration
            storage_backend: Storage backend for distributed state

        Returns:
            Created distributed rate limiter
        """
        limiter = DistributedRateLimiter(config, storage_backend)
        self.distributed_limiters[name] = limiter
        return limiter

    def get_limiter(self, name: str) -> RateLimiter | None:
        """Get rate limiter by name."""
        return self.limiters.get(name)

    def get_distributed_limiter(self, name: str) -> DistributedRateLimiter | None:
        """Get distributed rate limiter by name."""
        return self.distributed_limiters.get(name)

    async def acquire(self, name: str, timeout: float | None = None) -> bool:
        """
        Acquire permission from named limiter.

        Args:
            name: Limiter name
            timeout: Timeout for acquisition

        Returns:
            True if permission granted, False if timeout
        """
        limiter = self.get_limiter(name)
        if limiter:
            return await limiter.acquire(timeout)

        distributed_limiter = self.get_distributed_limiter(name)
        if distributed_limiter:
            return await distributed_limiter.acquire("default", timeout)

        raise ValueError(f"Rate limiter '{name}' not found")


# Global rate limit manager
rate_limit_manager = RateLimitManager()


def rate_limit(
    name: str,
    rate: int = 100,
    window: float = 60.0,
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET,
):
    """
    Decorator for rate limiting functions.

    Args:
        name: Rate limiter name
        rate: Requests per time window
        window: Time window in seconds
        strategy: Rate limiting strategy
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            config = RateLimitConfig(strategy=strategy, rate=rate, window=window)

            # Get or create limiter
            limiter = rate_limit_manager.get_limiter(name)
            if not limiter:
                limiter = rate_limit_manager.add_limiter(name, config)

            if not await limiter.acquire():
                raise RateLimitError(f"Rate limit exceeded for '{name}'")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
