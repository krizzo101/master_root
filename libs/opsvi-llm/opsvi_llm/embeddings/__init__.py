"""
Embeddings module for opsvi-llm.

Provides embedding generation, similarity computation, and search capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

__all__ = [
    "get_logger",
    "ComponentError",
    "BaseComponent",
]

__version__ = "1.0.0"
