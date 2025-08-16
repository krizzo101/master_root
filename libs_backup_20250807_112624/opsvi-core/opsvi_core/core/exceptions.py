"""
Exception hierarchy for opsvi-core.

Provides structured error handling across all opsvi-core components.
"""

from __future__ import annotations

from typing import Any, Optional

from opsvi_foundation.core.exceptions import OPSVIError


class CoreError(OPSVIError):
    """Base exception for all opsvi-core errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)


class CoreConfigurationError(CoreError):
    """Configuration-related errors in opsvi-core."""


class CoreConnectionError(CoreError):
    """Connection-related errors in opsvi-core."""


class CoreValidationError(CoreError):
    """Validation-related errors in opsvi-core."""


class CoreTimeoutError(CoreError):
    """Timeout-related errors in opsvi-core."""


class CoreResourceError(CoreError):
    """Resource-related errors in opsvi-core."""
