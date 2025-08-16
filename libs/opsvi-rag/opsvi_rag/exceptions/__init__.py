"""Exceptions module for opsvi-rag.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviRagError,
    OpsviRagConfigurationError,
    OpsviRagConnectionError,
    OpsviRagValidationError,
    OpsviRagTimeoutError,
    OpsviRagResourceError,
    OpsviRagInitializationError,
)

__all__ = [
    "OpsviRagError",
    "OpsviRagConfigurationError",
    "OpsviRagConnectionError",
    "OpsviRagValidationError",
    "OpsviRagTimeoutError",
    "OpsviRagResourceError",
    "OpsviRagInitializationError",
]
