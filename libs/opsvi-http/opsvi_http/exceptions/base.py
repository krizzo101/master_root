"""Exception classes for opsvi-http.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviHttpError(OPSVIError):
    """Base exception for all opsvi-http errors."""
    pass

class OpsviHttpConfigurationError(OpsviHttpError):
    """Configuration-related errors in opsvi-http."""
    pass

class OpsviHttpConnectionError(OpsviHttpError):
    """Connection-related errors in opsvi-http."""
    pass

class OpsviHttpValidationError(OpsviHttpError):
    """Validation-related errors in opsvi-http."""
    pass

class OpsviHttpTimeoutError(OpsviHttpError):
    """Timeout-related errors in opsvi-http."""
    pass

class OpsviHttpResourceError(OpsviHttpError):
    """Resource-related errors in opsvi-http."""
    pass

class OpsviHttpInitializationError(OpsviHttpError):
    """Initialization-related errors in opsvi-http."""
    pass

class OpsviHttpShutdownError(OpsviHttpError):
    """Shutdown-related errors in opsvi-http."""
    pass

# Library-specific exceptions

