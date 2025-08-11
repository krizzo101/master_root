"""opsvi-rag - Retrieval Augmented Generation system.

Comprehensive opsvi-rag library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import BaseRAGComponent, RAGConfig
from .config.settings import OpsviRagSettings, get_settings
from .exceptions.base import (
    OpsviRagError,
    OpsviRagConfigurationError,
    OpsviRagInitializationError,
)

# RAG-specific exports
from .datastores import QdrantStore, QdrantConfig

__all__ = [
    # Core
    "BaseRAGComponent",
    "RAGConfig",
    "OpsviRagSettings",
    "get_settings",
    "OpsviRagError",
    "OpsviRagConfigurationError",
    "OpsviRagInitializationError",
    # RAG
    "QdrantStore",
    "QdrantConfig",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
