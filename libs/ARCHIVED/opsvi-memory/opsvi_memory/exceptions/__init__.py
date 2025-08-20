"""Exceptions module for opsvi-memory.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviMemoryConfigurationError,
    OpsviMemoryConnectionError,
    OpsviMemoryError,
    OpsviMemoryInitializationError,
    OpsviMemoryResourceError,
    OpsviMemoryTimeoutError,
    OpsviMemoryValidationError,
)

__all__ = [
    "OpsviMemoryError",
    "OpsviMemoryConfigurationError",
    "OpsviMemoryConnectionError",
    "OpsviMemoryValidationError",
    "OpsviMemoryTimeoutError",
    "OpsviMemoryResourceError",
    "OpsviMemoryInitializationError",
]
