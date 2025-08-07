"""Exceptions module for opsvi-fs.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviFsError,
    OpsviFsConfigurationError,
    OpsviFsConnectionError,
    OpsviFsValidationError,
    OpsviFsTimeoutError,
    OpsviFsResourceError,
    OpsviFsInitializationError,
)

__all__ = [
    "OpsviFsError",
    "OpsviFsConfigurationError",
    "OpsviFsConnectionError",
    "OpsviFsValidationError",
    "OpsviFsTimeoutError",
    "OpsviFsResourceError",
    "OpsviFsInitializationError",
]
