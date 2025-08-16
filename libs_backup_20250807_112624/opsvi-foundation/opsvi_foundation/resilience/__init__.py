"""
Resilience module for opsvi-foundation.

Provides circuit breakers, retry mechanisms, and fault tolerance.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from .retry import ExponentialBackoff, RetryConfig, RetryExecutor, retry
from .timeout import (
    DeadlineContext,
    Timeout,
    TimeoutConfig,
    TimeoutError,
    timeout_manager,
    wait_for,
    with_timeout,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "DeadlineContext",
    "ExponentialBackoff",
    "RetryConfig",
    "RetryExecutor",
    "Timeout",
    "TimeoutConfig",
    "TimeoutError",
    "retry",
    "timeout_manager",
    "wait_for",
    "with_timeout",
]
