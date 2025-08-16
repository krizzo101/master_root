"""Core module for opsvi-memory.

Provides base classes and core functionality.
"""

from .base import OpsviMemoryManagerError, OpsviMemoryManagerConfigurationError, OpsviMemoryManagerInitializationError

__all__ = [
    "OpsviMemoryManagerError",
    "OpsviMemoryManagerConfigurationError",
    "OpsviMemoryManagerInitializationError",
]
