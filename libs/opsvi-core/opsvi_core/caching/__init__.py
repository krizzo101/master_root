"""
Caching module for opsvi-core.

Provides application-specific caching capabilities.
"""

from opsvi_foundation import Cache, CacheError, CacheKeyError, CacheValueError

__all__ = [
    "Cache",
    "CacheError",
    "CacheKeyError",
    "CacheValueError",
]

__version__ = "1.0.0"
