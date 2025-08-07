"""Exceptions module for opsvi-memory.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviMemoryError,
    OpsviMemoryConfigurationError,
    OpsviMemoryConnectionError,
    OpsviMemoryValidationError,
    OpsviMemoryTimeoutError,
    OpsviMemoryResourceError,
    OpsviMemoryInitializationError,
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
