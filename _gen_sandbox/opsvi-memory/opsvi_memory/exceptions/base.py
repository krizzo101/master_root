"""Exception classes for opsvi-memory.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviMemoryError(OPSVIError):
    """Base exception for all opsvi-memory errors."""
    pass

class OpsviMemoryConfigurationError(OpsviMemoryError):
    """Configuration-related errors in opsvi-memory."""
    pass

class OpsviMemoryConnectionError(OpsviMemoryError):
    """Connection-related errors in opsvi-memory."""
    pass

class OpsviMemoryValidationError(OpsviMemoryError):
    """Validation-related errors in opsvi-memory."""
    pass

class OpsviMemoryTimeoutError(OpsviMemoryError):
    """Timeout-related errors in opsvi-memory."""
    pass

class OpsviMemoryResourceError(OpsviMemoryError):
    """Resource-related errors in opsvi-memory."""
    pass

class OpsviMemoryInitializationError(OpsviMemoryError):
    """Initialization-related errors in opsvi-memory."""
    pass

class OpsviMemoryShutdownError(OpsviMemoryError):
    """Shutdown-related errors in opsvi-memory."""
    pass

# Library-specific exceptions

