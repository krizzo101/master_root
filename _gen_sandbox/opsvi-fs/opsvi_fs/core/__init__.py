"""Core module for opsvi-fs.

Provides base classes and core functionality.
"""

from .base import OpsviFsManagerError, OpsviFsManagerConfigurationError, OpsviFsManagerInitializationError

__all__ = [
    "OpsviFsManagerError",
    "OpsviFsManagerConfigurationError",
    "OpsviFsManagerInitializationError",
]
