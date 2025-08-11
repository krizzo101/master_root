"""Base exceptions for opsvi-foundation.

Comprehensive exception handling for the OPSVI ecosystem
"""

from typing import Optional, Any, Dict


class LibraryError(Exception):
    """Base exception for all OPSVI library errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize library error.

        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class LibraryConfigurationError(LibraryError):
    """Configuration-related errors."""

    pass


class LibraryInitializationError(LibraryError):
    """Initialization-related errors."""

    pass


class LibraryValidationError(LibraryError):
    """Validation-related errors."""

    pass


class LibraryConnectionError(LibraryError):
    """Connection-related errors."""

    pass


class LibraryTimeoutError(LibraryError):
    """Timeout-related errors."""

    pass


class LibraryAuthenticationError(LibraryError):
    """Authentication-related errors."""

    pass


class LibraryAuthorizationError(LibraryError):
    """Authorization-related errors."""

    pass


class LibraryResourceError(LibraryError):
    """Resource-related errors."""

    pass


class LibraryStateError(LibraryError):
    """State-related errors."""

    pass


class LibraryOperationError(LibraryError):
    """Operation-related errors."""

    pass
