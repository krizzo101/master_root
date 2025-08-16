"""
Exception hierarchy for opsvi-agents.

Provides structured error handling across all opsvi-agents components.
"""

from __future__ import annotations

from typing import Any, Optional

from opsvi_foundation.core.exceptions import OPSVIError


class AgentsError(OPSVIError):
    """Base exception for all opsvi-agents errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)


class AgentsConfigurationError(AgentsError):
    """Configuration-related errors in opsvi-agents."""


class AgentsConnectionError(AgentsError):
    """Connection-related errors in opsvi-agents."""


class AgentsValidationError(AgentsError):
    """Validation-related errors in opsvi-agents."""


class AgentsTimeoutError(AgentsError):
    """Timeout-related errors in opsvi-agents."""


class AgentsResourceError(AgentsError):
    """Resource-related errors in opsvi-agents."""
