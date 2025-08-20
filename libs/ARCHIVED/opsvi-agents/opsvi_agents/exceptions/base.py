"""Exception classes for opsvi-agents.


"""

from opsvi_foundation.exceptions.base import LibraryError


class OpsviAgentsError(LibraryError):
    """Base exception for all opsvi-agents errors."""

    pass


class OpsviAgentsConfigurationError(OpsviAgentsError):
    """Configuration-related errors in opsvi-agents."""

    pass


class OpsviAgentsConnectionError(OpsviAgentsError):
    """Connection-related errors in opsvi-agents."""

    pass


class OpsviAgentsValidationError(OpsviAgentsError):
    """Validation-related errors in opsvi-agents."""

    pass


class OpsviAgentsTimeoutError(OpsviAgentsError):
    """Timeout-related errors in opsvi-agents."""

    pass


class OpsviAgentsResourceError(OpsviAgentsError):
    """Resource-related errors in opsvi-agents."""

    pass


class OpsviAgentsInitializationError(OpsviAgentsError):
    """Initialization-related errors in opsvi-agents."""

    pass


class OpsviAgentsShutdownError(OpsviAgentsError):
    """Shutdown-related errors in opsvi-agents."""

    pass


class AgentExecutionError(OpsviAgentsError):
    """Error during agent execution."""

    pass


# Library-specific exceptions
