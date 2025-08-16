"""Exception classes for opsvi-orchestration.


"""

from opsvi_foundation.exceptions.base import OPSVIError


class OpsviOrchestrationError(OPSVIError):
    """Base exception for all opsvi-orchestration errors."""

    pass


class OpsviOrchestrationConfigurationError(OpsviOrchestrationError):
    """Configuration-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationConnectionError(OpsviOrchestrationError):
    """Connection-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationValidationError(OpsviOrchestrationError):
    """Validation-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationTimeoutError(OpsviOrchestrationError):
    """Timeout-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationResourceError(OpsviOrchestrationError):
    """Resource-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationInitializationError(OpsviOrchestrationError):
    """Initialization-related errors in opsvi-orchestration."""

    pass


class OpsviOrchestrationShutdownError(OpsviOrchestrationError):
    """Shutdown-related errors in opsvi-orchestration."""

    pass


# Library-specific exceptions
