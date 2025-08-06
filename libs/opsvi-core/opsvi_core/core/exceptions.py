"""
Custom exception hierarchy for OPSVI Core Library.

Provides structured error handling with specific exception types for different error scenarios.
"""


class OpsviError(Exception):
    """Base exception for all opsvi core errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(OpsviError):
    """Raised when configuration validation fails."""

    pass


class InitializationError(OpsviError):
    """Raised when core components fail to initialize."""

    pass


class ValidationError(OpsviError):
    """Raised on validation failures in data models."""

    pass


class ExternalServiceError(OpsviError):
    """Raised when external service interactions fail."""

    pass


class DatabaseConnectionError(ExternalServiceError):
    """Database connection related errors."""

    pass


class AuthenticationError(OpsviError):
    """Raised when authentication or authorization fails."""

    pass


class ResourceNotFoundError(OpsviError):
    """Raised when a requested resource is not found."""

    pass


class TimeoutError(OpsviError):
    """Raised when operations exceed their timeout limits."""

    pass


class RateLimitError(ExternalServiceError):
    """Raised when rate limits are exceeded."""

    pass


class NetworkError(ExternalServiceError):
    """Raised when network-related errors occur."""

    pass


class SerializationError(OpsviError):
    """Raised when data serialization/deserialization fails."""

    pass
