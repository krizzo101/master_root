"""
Caching module for opsvi-core.

Provides cache backend implementations and cache management utilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base caching infrastructure
from .base import (
    CacheBackend,
    CacheError,
    CacheManager,
)

# Cache implementations
from .in_memory import InMemoryCache

__all__ = [
    # Base classes
    "CacheBackend",
    "CacheError",
    "CacheManager",
    # Implementations
    "InMemoryCache",
]

__version__ = "1.0.0"
