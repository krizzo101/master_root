"""
Circuit breaker pattern implementation for opsvi-core.

Provides fault tolerance and resilience for external service calls.
"""

import asyncio
import builtins
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from ..core.exceptions import ExternalServiceError, TimeoutError
from ..core.logging import get_logger

logger = get_logger(__name__)

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


class CircuitBreakerError(ExternalServiceError):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation with timeout and failure tracking."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()

        logger.info("Circuit breaker initialized", state=self.state.value)

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state()

        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_function(func, *args, **kwargs),
                timeout=self.config.timeout,
            )

            await self._on_success()
            return result

        except builtins.TimeoutError:
            await self._on_failure()
            raise TimeoutError(
                f"Function timed out after {self.config.timeout} seconds"
            )
        except self.config.expected_exception:
            await self._on_failure()
            raise
        except Exception as e:
            await self._on_failure()
            raise ExternalServiceError(f"Unexpected error: {e}")

    async def _execute_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    async def _check_state(self) -> None:
        """Check and update circuit breaker state."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker moved to HALF_OPEN")

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker CLOSED after recovery")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPENED from HALF_OPEN")
            elif (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker OPENED", failure_count=self.failure_count
                )

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
        }

    async def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = 0
            logger.info("Circuit breaker manually reset")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        async with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig()
                self._breakers[name] = CircuitBreaker(config)
                logger.info("Circuit breaker created", name=name)

            return self._breakers[name]

    async def call_with_breaker(
        self,
        name: str,
        func: Callable[..., T],
        config: CircuitBreakerConfig | None = None,
        *args,
        **kwargs,
    ) -> T:
        """Execute function with named circuit breaker."""
        breaker = await self.get_breaker(name, config)
        return await breaker.call(func, *args, **kwargs)

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Get states of all registered circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}

    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()
        logger.info("All circuit breakers reset")


# Global registry instance
registry = CircuitBreakerRegistry()


def circuit_breaker(name: str, config: CircuitBreakerConfig | None = None):
    """Decorator for applying circuit breaker to functions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            return await registry.call_with_breaker(name, func, config, *args, **kwargs)

        return wrapper

    return decorator
