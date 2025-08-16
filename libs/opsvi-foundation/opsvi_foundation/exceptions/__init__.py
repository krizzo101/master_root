"""Exception classes for opsvi-foundation.

Comprehensive exception handling for the OPSVI ecosystem
"""

from .base import (
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

__all__ = [
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
]
