"""Exception classes for opsvi-fs.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviFsError(OPSVIError):
    """Base exception for all opsvi-fs errors."""
    pass

class OpsviFsConfigurationError(OpsviFsError):
    """Configuration-related errors in opsvi-fs."""
    pass

class OpsviFsConnectionError(OpsviFsError):
    """Connection-related errors in opsvi-fs."""
    pass

class OpsviFsValidationError(OpsviFsError):
    """Validation-related errors in opsvi-fs."""
    pass

class OpsviFsTimeoutError(OpsviFsError):
    """Timeout-related errors in opsvi-fs."""
    pass

class OpsviFsResourceError(OpsviFsError):
    """Resource-related errors in opsvi-fs."""
    pass

class OpsviFsInitializationError(OpsviFsError):
    """Initialization-related errors in opsvi-fs."""
    pass

class OpsviFsShutdownError(OpsviFsError):
    """Shutdown-related errors in opsvi-fs."""
    pass

# Library-specific exceptions

