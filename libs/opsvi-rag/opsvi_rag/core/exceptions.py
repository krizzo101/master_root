"""
RAG-specific exceptions.

Extends foundation exceptions with RAG domain errors.
"""

from opsvi_foundation import ComponentError


class RAGError(ComponentError):
    """Base exception for opsvi-rag."""

    pass


class RAGValidationError(RAGError):
    """Validation error specific to opsvi-rag."""

    pass


class RAGConfigurationError(RAGError):
    """Configuration error specific to opsvi-rag."""

    pass
