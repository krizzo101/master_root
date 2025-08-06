"""
Core module for opsvi-rag.

Domain-specific configuration and exceptions.
"""

from .config import RAGConfig, config
from .exceptions import RAGError, RAGValidationError, RAGConfigurationError

__all__ = [
    "RAGConfig",
    "config", 
    "RAGError",
    "RAGValidationError",
    "RAGConfigurationError",
]
