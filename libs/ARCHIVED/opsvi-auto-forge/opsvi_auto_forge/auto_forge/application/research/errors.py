"""Custom error hierarchy for the research stack."""

from typing import Any, Dict, Optional


class ResearchError(Exception):
    """Base exception for all research-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(ResearchError):
    """Raised when configuration is invalid or missing."""


class ClientError(ResearchError):
    """Raised when MCP client operations fail."""

    def __init__(
        self, message: str, client_name: str, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.client_name = client_name


class OrchestrationError(ResearchError):
    """Raised when orchestration of multiple clients fails."""


class ValidationError(ResearchError):
    """Raised when data validation fails."""


class PersistenceError(ResearchError):
    """Raised when persistence operations fail."""


class SynthesisError(ResearchError):
    """Raised when research synthesis fails."""
