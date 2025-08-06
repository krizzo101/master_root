"""
Resilience module for opsvi-core.

Provides fault tolerance, circuit breakers, and retry mechanisms.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Resilience components
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerState,
)
from .retry import (
    RetryConfig,
    RetryError,
    RetryManager,
    RetryStrategy,
)

__all__ = [
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerState",
    # Retry mechanisms
    "RetryConfig",
    "RetryError",
    "RetryManager",
    "RetryStrategy",
]

__version__ = "1.0.0"
