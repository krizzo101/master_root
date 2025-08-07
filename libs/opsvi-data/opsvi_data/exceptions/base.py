"""Exception classes for opsvi-data.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviDataError(OPSVIError):
    """Base exception for all opsvi-data errors."""
    pass

class OpsviDataConfigurationError(OpsviDataError):
    """Configuration-related errors in opsvi-data."""
    pass

class OpsviDataConnectionError(OpsviDataError):
    """Connection-related errors in opsvi-data."""
    pass

class OpsviDataValidationError(OpsviDataError):
    """Validation-related errors in opsvi-data."""
    pass

class OpsviDataTimeoutError(OpsviDataError):
    """Timeout-related errors in opsvi-data."""
    pass

class OpsviDataResourceError(OpsviDataError):
    """Resource-related errors in opsvi-data."""
    pass

class OpsviDataInitializationError(OpsviDataError):
    """Initialization-related errors in opsvi-data."""
    pass

class OpsviDataShutdownError(OpsviDataError):
    """Shutdown-related errors in opsvi-data."""
    pass

# Library-specific exceptions

