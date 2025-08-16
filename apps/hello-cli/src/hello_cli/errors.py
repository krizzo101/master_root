"""Error handling for Hello CLI."""


class HelloCliError(Exception):
    """Base exception for Hello CLI."""

    pass


class ValidationError(HelloCliError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(HelloCliError):
    """Raised when configuration is invalid."""

    pass
