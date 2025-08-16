"""
Centralized exception framework for OPSVI libraries.

Provides generic exception patterns to eliminate repetition across all libraries.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from opsvi_foundation.patterns.base import ComponentError as OPSVIError


class LibraryError(OPSVIError):
    """Base exception for all library errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)


class LibraryConfigurationError(LibraryError):
    """Configuration-related errors in libraries."""


class LibraryConnectionError(LibraryError):
    """Connection-related errors in libraries."""


class LibraryValidationError(LibraryError):
    """Validation-related errors in libraries."""


class LibraryTimeoutError(LibraryError):
    """Timeout-related errors in libraries."""


class LibraryResourceError(LibraryError):
    """Resource-related errors in libraries."""


class LibraryInitializationError(LibraryError):
    """Initialization-related errors in libraries."""


class LibraryShutdownError(LibraryError):
    """Shutdown-related errors in libraries."""


def create_library_exceptions(library_name: str) -> Dict[str, Type[LibraryError]]:
    """Factory function to create library-specific exception classes."""

    base_name = library_name.title().replace('-', '')

    exceptions = {}

    # Create base exception
    base_exception = type(
        f"{base_name}Error",
        (LibraryError,),
        {"__doc__": f"Base exception for all {library_name} errors."}
    )
    exceptions[f"{base_name}Error"] = base_exception

    # Create specific exceptions
    specific_exceptions = [
        ("ConfigurationError", LibraryConfigurationError),
        ("ConnectionError", LibraryConnectionError),
        ("ValidationError", LibraryValidationError),
        ("TimeoutError", LibraryTimeoutError),
        ("ResourceError", LibraryResourceError),
        ("InitializationError", LibraryInitializationError),
        ("ShutdownError", LibraryShutdownError),
    ]

    for exc_name, base_exc in specific_exceptions:
        exception_class = type(
            f"{base_name}{exc_name}",
            (base_exc,),
            {"__doc__": f"{exc_name.lower().replace('Error', '')}-related errors in {library_name}."}
        )
        exceptions[f"{base_name}{exc_name}"] = exception_class

    return exceptions


def get_library_exception(library_name: str, exception_type: str) -> Type[LibraryError]:
    """Get a specific exception class for a library."""
    exceptions = create_library_exceptions(library_name)
    exception_name = f"{library_name.title().replace('-', '')}{exception_type}"
    return exceptions.get(exception_name, LibraryError)


# Common exception types for easy access
def configuration_error(library_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> LibraryConfigurationError:
    """Create a configuration error for a library."""
    exception_class = get_library_exception(library_name, "ConfigurationError")
    return exception_class(message, details)


def connection_error(library_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> LibraryConnectionError:
    """Create a connection error for a library."""
    exception_class = get_library_exception(library_name, "ConnectionError")
    return exception_class(message, details)


def validation_error(library_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> LibraryValidationError:
    """Create a validation error for a library."""
    exception_class = get_library_exception(library_name, "ValidationError")
    return exception_class(message, details)


def timeout_error(library_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> LibraryTimeoutError:
    """Create a timeout error for a library."""
    exception_class = get_library_exception(library_name, "TimeoutError")
    return exception_class(message, details)


def resource_error(library_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> LibraryResourceError:
    """Create a resource error for a library."""
    exception_class = get_library_exception(library_name, "ResourceError")
    return exception_class(message, details)
