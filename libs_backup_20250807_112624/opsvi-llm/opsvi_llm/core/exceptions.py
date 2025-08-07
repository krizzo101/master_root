"""
Exception hierarchy for opsvi-llm.

Provides structured error handling across all opsvi-llm components.
"""

from __future__ import annotations

from typing import Any, Optional

from opsvi_foundation.core.exceptions import OPSVIError


class LlmError(OPSVIError):
    """Base exception for all opsvi-llm errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)


class LlmConfigurationError(LlmError):
    """Configuration-related errors in opsvi-llm."""


class LlmConnectionError(LlmError):
    """Connection-related errors in opsvi-llm."""


class LlmValidationError(LlmError):
    """Validation-related errors in opsvi-llm."""


class LlmTimeoutError(LlmError):
    """Timeout-related errors in opsvi-llm."""


class LlmResourceError(LlmError):
    """Resource-related errors in opsvi-llm."""
