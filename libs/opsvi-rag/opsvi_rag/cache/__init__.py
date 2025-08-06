"""
Cache module for opsvi-rag.

Provides caching capabilities for queries, embeddings, documents, and responses.
"""

from opsvi_foundation import (
    BaseComponent,
    Cache,
    CacheError,
    ComponentError,
    get_logger,
)

__all__ = [
    "get_logger",
    "ComponentError",
    "BaseComponent",
    "Cache",
    "CacheError",
]

__version__ = "1.0.0"
