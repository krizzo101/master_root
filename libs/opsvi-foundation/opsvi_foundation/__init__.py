"""
OPSVI Foundation Library

Shared foundation components for the OPSVI ecosystem.
Provides security, resilience, observability, and configuration management.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .config import FoundationConfig, config
from .security import AuthManager, AuthConfig, TokenPayload, sanitize_input
from .resilience import CircuitBreaker, CircuitBreakerConfig, RetryExecutor, RetryConfig, retry
from .patterns import BaseComponent, LifecycleComponent, ComponentError
from .observability import setup_logging, get_logger, log_context

__all__ = [
    # Configuration
    "FoundationConfig",
    "config",
    # Security
    "AuthManager",
    "AuthConfig",
    "TokenPayload",
    "sanitize_input",
    # Resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "RetryExecutor",
    "RetryConfig",
    "retry",
    # Patterns
    "BaseComponent",
    "LifecycleComponent",
    "ComponentError",
    # Observability
    "setup_logging",
    "get_logger",
    "log_context",
]
