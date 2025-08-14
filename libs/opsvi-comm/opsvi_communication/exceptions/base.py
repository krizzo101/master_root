"""Exception classes for opsvi-communication.


"""

from opsvi_foundation.exceptions.base import OPSVIError


class OpsviCommunicationError(OPSVIError):
    """Base exception for all opsvi-communication errors."""

    pass


class OpsviCommunicationConfigurationError(OpsviCommunicationError):
    """Configuration-related errors in opsvi-communication."""

    pass


class OpsviCommunicationConnectionError(OpsviCommunicationError):
    """Connection-related errors in opsvi-communication."""

    pass


class OpsviCommunicationValidationError(OpsviCommunicationError):
    """Validation-related errors in opsvi-communication."""

    pass


class OpsviCommunicationTimeoutError(OpsviCommunicationError):
    """Timeout-related errors in opsvi-communication."""

    pass


class OpsviCommunicationResourceError(OpsviCommunicationError):
    """Resource-related errors in opsvi-communication."""

    pass


class OpsviCommunicationInitializationError(OpsviCommunicationError):
    """Initialization-related errors in opsvi-communication."""

    pass


class OpsviCommunicationShutdownError(OpsviCommunicationError):
    """Shutdown-related errors in opsvi-communication."""

    pass


# Library-specific exceptions
