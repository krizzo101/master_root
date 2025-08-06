"""
Circuit breaker pattern implementation.

Provides fault tolerance and resilience for external service calls.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes to close from half-open
    timeout: int = 30  # Request timeout in seconds
    expected_exception: type = Exception  # Exception type to catch


class CircuitBreaker:
    """Circuit breaker implementation with timeout and failure tracking."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state()

        if self.state == CircuitState.OPEN:
            raise RuntimeError("Circuit breaker is OPEN")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_function(func, *args, **kwargs),
                timeout=self.config.timeout,
            )

            await self._on_success()
            return result

        except TimeoutError:
            await self._on_failure()
            raise TimeoutError(
                f"Function timed out after {self.config.timeout} seconds",
            )
        except self.config.expected_exception:
            await self._on_failure()
            raise
        except Exception as e:
            await self._on_failure()
            raise RuntimeError(f"Unexpected error: {e}")

    async def _execute_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    async def _check_state(self) -> None:
        """Check and update circuit breaker state."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN or (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }
