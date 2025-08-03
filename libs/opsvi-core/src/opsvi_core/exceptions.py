"""OPSVI Core Exceptions."""


class OPSVIError(Exception):
    """Base exception for all OPSVI errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(OPSVIError):
    """Raised when there's a configuration error."""

    pass


class ValidationError(OPSVIError):
    """Raised when data validation fails."""

    pass


class ConnectionError(OPSVIError):
    """Raised when connection to external services fails."""

    pass


class TimeoutError(OPSVIError):
    """Raised when operations timeout."""

    pass
