"""
Core module for opsvi-rag.

Domain-specific configuration and exceptions.
"""

from .config import RAGConfig, config
from .exceptions import RAGConfigurationError, RAGError, RAGValidationError

__all__ = [
    "RAGConfig",
    "config",
    "RAGError",
    "RAGValidationError",
    "RAGConfigurationError",
]
