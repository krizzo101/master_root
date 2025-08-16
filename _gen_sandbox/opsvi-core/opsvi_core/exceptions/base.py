"""Exception classes for opsvi-core.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviCoreError(OPSVIError):
    """Base exception for all opsvi-core errors."""
    pass

class OpsviCoreConfigurationError(OpsviCoreError):
    """Configuration-related errors in opsvi-core."""
    pass

class OpsviCoreConnectionError(OpsviCoreError):
    """Connection-related errors in opsvi-core."""
    pass

class OpsviCoreValidationError(OpsviCoreError):
    """Validation-related errors in opsvi-core."""
    pass

class OpsviCoreTimeoutError(OpsviCoreError):
    """Timeout-related errors in opsvi-core."""
    pass

class OpsviCoreResourceError(OpsviCoreError):
    """Resource-related errors in opsvi-core."""
    pass

class OpsviCoreInitializationError(OpsviCoreError):
    """Initialization-related errors in opsvi-core."""
    pass

class OpsviCoreShutdownError(OpsviCoreError):
    """Shutdown-related errors in opsvi-core."""
    pass

# Library-specific exceptions

