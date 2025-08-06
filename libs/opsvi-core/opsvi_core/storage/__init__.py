"""
Storage module for opsvi-core.

Provides storage abstractions, repositories, and connection management.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base storage infrastructure
from .base import (
    FileStorage,
    KeyValueStore,
    StorageBackend,
    StorageConfig,
    StorageError,
    StorageManager,
)

__all__ = [
    # Base classes
    "FileStorage",
    "KeyValueStore",
    "StorageBackend",
    "StorageConfig",
    "StorageError",
    "StorageManager",
]

__version__ = "1.0.0"
