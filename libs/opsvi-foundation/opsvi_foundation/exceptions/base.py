"""Exception classes for opsvi-foundation.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviFoundationError(OPSVIError):
    """Base exception for all opsvi-foundation errors."""
    pass

class OpsviFoundationConfigurationError(OpsviFoundationError):
    """Configuration-related errors in opsvi-foundation."""
    pass

class OpsviFoundationConnectionError(OpsviFoundationError):
    """Connection-related errors in opsvi-foundation."""
    pass

class OpsviFoundationValidationError(OpsviFoundationError):
    """Validation-related errors in opsvi-foundation."""
    pass

class OpsviFoundationTimeoutError(OpsviFoundationError):
    """Timeout-related errors in opsvi-foundation."""
    pass

class OpsviFoundationResourceError(OpsviFoundationError):
    """Resource-related errors in opsvi-foundation."""
    pass

class OpsviFoundationInitializationError(OpsviFoundationError):
    """Initialization-related errors in opsvi-foundation."""
    pass

class OpsviFoundationShutdownError(OpsviFoundationError):
    """Shutdown-related errors in opsvi-foundation."""
    pass

# Library-specific exceptions

