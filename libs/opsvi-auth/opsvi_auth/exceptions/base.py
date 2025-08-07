"""Exception classes for opsvi-auth.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviAuthError(OPSVIError):
    """Base exception for all opsvi-auth errors."""
    pass

class OpsviAuthConfigurationError(OpsviAuthError):
    """Configuration-related errors in opsvi-auth."""
    pass

class OpsviAuthConnectionError(OpsviAuthError):
    """Connection-related errors in opsvi-auth."""
    pass

class OpsviAuthValidationError(OpsviAuthError):
    """Validation-related errors in opsvi-auth."""
    pass

class OpsviAuthTimeoutError(OpsviAuthError):
    """Timeout-related errors in opsvi-auth."""
    pass

class OpsviAuthResourceError(OpsviAuthError):
    """Resource-related errors in opsvi-auth."""
    pass

class OpsviAuthInitializationError(OpsviAuthError):
    """Initialization-related errors in opsvi-auth."""
    pass

class OpsviAuthShutdownError(OpsviAuthError):
    """Shutdown-related errors in opsvi-auth."""
    pass

# Library-specific exceptions

