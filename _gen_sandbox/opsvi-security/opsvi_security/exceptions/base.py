"""Exception classes for opsvi-security.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviSecurityError(OPSVIError):
    """Base exception for all opsvi-security errors."""
    pass

class OpsviSecurityConfigurationError(OpsviSecurityError):
    """Configuration-related errors in opsvi-security."""
    pass

class OpsviSecurityConnectionError(OpsviSecurityError):
    """Connection-related errors in opsvi-security."""
    pass

class OpsviSecurityValidationError(OpsviSecurityError):
    """Validation-related errors in opsvi-security."""
    pass

class OpsviSecurityTimeoutError(OpsviSecurityError):
    """Timeout-related errors in opsvi-security."""
    pass

class OpsviSecurityResourceError(OpsviSecurityError):
    """Resource-related errors in opsvi-security."""
    pass

class OpsviSecurityInitializationError(OpsviSecurityError):
    """Initialization-related errors in opsvi-security."""
    pass

class OpsviSecurityShutdownError(OpsviSecurityError):
    """Shutdown-related errors in opsvi-security."""
    pass

# Library-specific exceptions

