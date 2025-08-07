"""
Exception hierarchy for opsvi-rag.

Provides structured error handling across all opsvi-rag components.
"""

from __future__ import annotations

from typing import Any, Optional

from opsvi_foundation.core.exceptions import OPSVIError


class RagError(OPSVIError):
    """Base exception for all opsvi-rag errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)


class RagConfigurationError(RagError):
    """Configuration-related errors in opsvi-rag."""


class RagConnectionError(RagError):
    """Connection-related errors in opsvi-rag."""


class RagValidationError(RagError):
    """Validation-related errors in opsvi-rag."""


class RagTimeoutError(RagError):
    """Timeout-related errors in opsvi-rag."""


class RagResourceError(RagError):
    """Resource-related errors in opsvi-rag."""
