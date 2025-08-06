"""
Rate limiting utilities for OPSVI LLM Library.

Provides rate limiting functionality to prevent API quota exhaustion.
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting behavior."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    window_size: float = 60.0  # seconds


class RateLimiter:
    """
    Rate limiter for API requests with sliding window support.

    Provides token bucket and sliding window rate limiting to prevent
    API quota exhaustion and ensure fair usage.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize the rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.request_times: deque = deque()
        self.tokens_available = config.burst_size
        self.last_token_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make a request.

        Args:
            timeout: Maximum time to wait for permission

        Returns:
            bool: True if permission granted, False if timeout
        """
        async with self._lock:
            start_time = time.time()

            while True:
                # Check if we can make a request
                if self._can_make_request():
                    self._record_request()
                    return True

                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    logger.warning("Rate limit timeout exceeded")
                    return False

                # Calculate wait time
                wait_time = self._calculate_wait_time()
                if timeout:
                    wait_time = min(wait_time, timeout - (time.time() - start_time))

                if wait_time <= 0:
                    continue

                # Wait before retrying
                await asyncio.sleep(wait_time)

    def _can_make_request(self) -> bool:
        """Check if a request can be made."""
        current_time = time.time()

        # Refill tokens
        self._refill_tokens(current_time)

        # Check token bucket
        if self.tokens_available <= 0:
            return False

        # Check sliding window
        return self._check_sliding_window(current_time)

    def _refill_tokens(self, current_time: float) -> None:
        """Refill tokens based on time elapsed."""
        time_elapsed = current_time - self.last_token_refill
        tokens_to_add = (time_elapsed / 60.0) * self.config.requests_per_minute

        self.tokens_available = min(
            self.config.burst_size, self.tokens_available + tokens_to_add
        )
        self.last_token_refill = current_time

    def _check_sliding_window(self, current_time: float) -> bool:
        """Check sliding window rate limit."""
        # Remove old requests outside the window
        while (
            self.request_times
            and (current_time - self.request_times[0]) > self.config.window_size
        ):
            self.request_times.popleft()

        # Check if we're within the limit
        return len(self.request_times) < self.config.requests_per_minute

    def _record_request(self) -> None:
        """Record a request."""
        current_time = time.time()
        self.request_times.append(current_time)
        self.tokens_available -= 1

    def _calculate_wait_time(self) -> float:
        """Calculate how long to wait before next request."""
        current_time = time.time()

        # Calculate token bucket wait time
        if self.tokens_available <= 0:
            tokens_needed = 1 - self.tokens_available
            token_wait_time = (tokens_needed / self.config.requests_per_minute) * 60.0
        else:
            token_wait_time = 0.0

        # Calculate sliding window wait time
        if self.request_times:
            oldest_request = self.request_times[0]
            window_wait_time = max(
                0, self.config.window_size - (current_time - oldest_request)
            )
        else:
            window_wait_time = 0.0

        return max(token_wait_time, window_wait_time)

    def get_stats(self) -> dict[str, Any]:
        """Get current rate limiter statistics."""
        current_time = time.time()

        # Clean up old requests
        while (
            self.request_times
            and (current_time - self.request_times[0]) > self.config.window_size
        ):
            self.request_times.popleft()

        return {
            "tokens_available": self.tokens_available,
            "requests_in_window": len(self.request_times),
            "window_size": self.config.window_size,
            "requests_per_minute": self.config.requests_per_minute,
            "burst_size": self.config.burst_size,
        }


class RateLimitManager:
    """
    Manager for multiple rate limiters.

    Provides centralized management of rate limiters for different
    API endpoints or services.
    """

    def __init__(self):
        """Initialize the rate limit manager."""
        self.limiters: dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

    def add_limiter(self, name: str, config: RateLimitConfig) -> None:
        """
        Add a rate limiter for a specific service.

        Args:
            name: Name of the service/endpoint
            config: Rate limiting configuration
        """
        self.limiters[name] = RateLimiter(config)

    async def acquire(self, name: str, timeout: float | None = None) -> bool:
        """
        Acquire permission from a specific rate limiter.

        Args:
            name: Name of the service/endpoint
            timeout: Maximum time to wait for permission

        Returns:
            bool: True if permission granted, False if timeout

        Raises:
            KeyError: If rate limiter not found
        """
        if name not in self.limiters:
            raise KeyError(f"Rate limiter '{name}' not found")

        return await self.limiters[name].acquire(timeout)

    def get_stats(self, name: str | None = None) -> dict[str, Any]:
        """
        Get statistics for rate limiters.

        Args:
            name: Specific limiter name, or None for all

        Returns:
            Dict containing statistics
        """
        if name:
            if name not in self.limiters:
                raise KeyError(f"Rate limiter '{name}' not found")
            return {name: self.limiters[name].get_stats()}

        return {name: limiter.get_stats() for name, limiter in self.limiters.items()}

    def remove_limiter(self, name: str) -> None:
        """
        Remove a rate limiter.

        Args:
            name: Name of the service/endpoint
        """
        if name in self.limiters:
            del self.limiters[name]


# Global rate limit manager instance
_global_rate_limit_manager = RateLimitManager()


def get_global_rate_limit_manager() -> RateLimitManager:
    """Get the global rate limit manager instance."""
    return _global_rate_limit_manager


def add_global_rate_limiter(name: str, config: RateLimitConfig) -> None:
    """Add a rate limiter to the global manager."""
    _global_rate_limit_manager.add_limiter(name, config)


async def acquire_global_rate_limit(name: str, timeout: float | None = None) -> bool:
    """Acquire permission from the global rate limit manager."""
    return await _global_rate_limit_manager.acquire(name, timeout)
