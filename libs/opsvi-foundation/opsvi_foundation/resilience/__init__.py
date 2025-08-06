"""
Resilience module for opsvi-foundation.

Provides circuit breakers, retry mechanisms, and fault tolerance.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from .retry import RetryExecutor, RetryConfig, ExponentialBackoff, retry
from .timeout import (
    Timeout,
    TimeoutConfig,
    TimeoutError,
    DeadlineContext,
    timeout_manager,
    with_timeout,
    wait_for
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "RetryExecutor",
    "RetryConfig",
    "ExponentialBackoff",
    "retry",
    "Timeout",
    "TimeoutConfig",
    "TimeoutError",
    "DeadlineContext",
    "timeout_manager",
    "with_timeout",
    "wait_for",
]
