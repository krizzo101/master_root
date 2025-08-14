"""opsvi-foundation - Foundation library providing base components and utilities.

Comprehensive opsvi-foundation library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import BaseComponent, ComponentError, BaseSettings
from .config.settings import LibraryConfig, LibrarySettings, FoundationConfig
from .exceptions.base import (
    LibraryError,
    LibraryConfigurationError,
    LibraryInitializationError,
    LibraryValidationError,
    LibraryConnectionError,
    LibraryTimeoutError,
    LibraryAuthenticationError,
    LibraryAuthorizationError,
    LibraryResourceError,
    LibraryStateError,
    LibraryOperationError,
)
from .utils.retry import (
    retry,
    retry_async,
    BackoffStrategy,
    ExponentialBackoff,
    LinearBackoff,
    ConstantBackoff,
    RetryContext,
)

__all__ = [
    # Core
    "BaseComponent",
    "ComponentError",
    "BaseSettings",
    "LibraryConfig",
    "LibrarySettings",
    "FoundationConfig",
    # Exceptions
    "LibraryError",
    "LibraryConfigurationError",
    "LibraryInitializationError",
    "LibraryValidationError",
    "LibraryConnectionError",
    "LibraryTimeoutError",
    "LibraryAuthenticationError",
    "LibraryAuthorizationError",
    "LibraryResourceError",
    "LibraryStateError",
    "LibraryOperationError",
    # Retry utilities
    "retry",
    "retry_async",
    "BackoffStrategy",
    "ExponentialBackoff",
    "LinearBackoff",
    "ConstantBackoff",
    "RetryContext",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
