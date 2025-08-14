"""Circuit Breaker pattern implementation for opsvi-foundation.

Provides a circuit breaker mechanism to prevent cascading failures
by temporarily blocking calls to failing services.
"""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from ..config.settings import FoundationConfig
from ..core.base import ComponentError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, calls pass through
    OPEN = "open"  # Failure threshold reached, calls are blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(ComponentError):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)


class CircuitBreakerStats:
    """Statistics for circuit breaker operations."""

    def __init__(self):
        """Initialize statistics."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0
        self.state_transitions: list[tuple[CircuitState, CircuitState, datetime]] = []
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None

    def record_success(self) -> None:
        """Record a successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_time = datetime.utcnow()

    def record_failure(self) -> None:
        """Record a failed call."""
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()

    def record_rejection(self) -> None:
        """Record a rejected call."""
        self.total_calls += 1
        self.rejected_calls += 1

    def record_transition(
        self, from_state: CircuitState, to_state: CircuitState
    ) -> None:
        """Record a state transition."""
        self.state_transitions.append((from_state, to_state, datetime.utcnow()))

    def get_failure_rate(self) -> float:
        """Get the failure rate."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    def get_stats_dict(self) -> Dict[str, Any]:
        """Get statistics as a dictionary."""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "failure_rate": self.get_failure_rate(),
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "last_success_time": self.last_success_time.isoformat()
            if self.last_success_time
            else None,
            "state_transitions": len(self.state_transitions),
        }


class CircuitBreaker:
    """Circuit breaker implementation with configurable thresholds."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception,
        success_threshold: int = 2,
        name: Optional[str] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
        config: Optional[FoundationConfig] = None,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type(s) to catch
            success_threshold: Successes needed in HALF_OPEN to close circuit
            name: Optional name for the circuit breaker
            on_state_change: Callback for state changes
            config: Optional FoundationConfig
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.name = name or "circuit_breaker"
        self.on_state_change = on_state_change
        self.config = config or FoundationConfig(
            library_name="circuit_breaker", version="1.0.0"
        )

        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = Lock()

        # Statistics
        self.stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self.state == CircuitState.HALF_OPEN

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state.

        Args:
            new_state: The new state to transition to
        """
        old_state = self._state
        self._state = new_state
        self.stats.record_transition(old_state, new_state)

        logger.info(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {new_state.value}"
        )

        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit.

        Returns:
            True if recovery timeout has passed
        """
        if self._last_failure_time is None:
            return False

        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self.stats.record_success()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0
                    self._success_count = 0

    def _record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self.stats.record_failure()
            self._last_failure_time = time.time()

            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

            elif self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
                self._failure_count = 0
                self._success_count = 0

    def _check_state(self) -> None:
        """Check and update circuit state."""
        with self._lock:
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                self._success_count = 0

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If circuit is open
        """
        self._check_state()

        if self.is_open:
            self.stats.record_rejection()
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise

    async def call_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute an async function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If circuit is open
        """
        self._check_state()

        if self.is_open:
            self.stats.record_rejection()
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dictionary with statistics
        """
        stats = self.stats.get_stats_dict()
        stats["current_state"] = self.state.value
        stats["failure_count"] = self._failure_count
        stats["success_count"] = self._success_count
        return stats


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exception: Type[Exception] = Exception,
    success_threshold: int = 2,
    name: Optional[str] = None,
    on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    config: Optional[FoundationConfig] = None,
) -> Callable:
    """Decorator for applying circuit breaker pattern to functions.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type(s) to catch
        success_threshold: Successes needed in HALF_OPEN to close circuit
        name: Optional name for the circuit breaker
        on_state_change: Callback for state changes
        config: Optional FoundationConfig

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=60)
        async def api_call():
            return await external_service.call()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create a circuit breaker instance for this function
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold,
            name=name or func.__name__,
            on_state_change=on_state_change,
            config=config,
        )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            """Async wrapper with circuit breaker."""
            return await cb.call_async(func, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Sync wrapper with circuit breaker."""
            return cb.call(func, *args, **kwargs)

        # Attach the circuit breaker instance for inspection
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.circuit_breaker = cb

        return wrapper

    return decorator


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def register(self, name: str, breaker: CircuitBreaker) -> None:
        """Register a circuit breaker.

        Args:
            name: Name for the circuit breaker
            breaker: Circuit breaker instance
        """
        with self._lock:
            self._breakers[name] = breaker
            logger.info(f"Registered circuit breaker: {name}")

    def unregister(self, name: str) -> None:
        """Unregister a circuit breaker.

        Args:
            name: Name of the circuit breaker
        """
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                logger.info(f"Unregistered circuit breaker: {name}")

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name.

        Args:
            name: Name of the circuit breaker

        Returns:
            Circuit breaker instance or None
        """
        with self._lock:
            return self._breakers.get(name)

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers.

        Returns:
            Dictionary of circuit breakers
        """
        with self._lock:
            return dict(self._breakers)

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers.

        Returns:
            Dictionary of statistics by breaker name
        """
        with self._lock:
            return {
                name: breaker.get_stats() for name, breaker in self._breakers.items()
            }


# Global circuit breaker manager instance
_manager = CircuitBreakerManager()


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager.

    Returns:
        Circuit breaker manager instance
    """
    return _manager


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitState",
    "CircuitBreakerStats",
    "circuit_breaker",
    "CircuitBreakerManager",
    "get_circuit_breaker_manager",
]
