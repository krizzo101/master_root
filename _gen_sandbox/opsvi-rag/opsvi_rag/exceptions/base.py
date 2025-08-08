"""Exception classes for opsvi-rag.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviRagError(OPSVIError):
    """Base exception for all opsvi-rag errors."""
    pass

class OpsviRagConfigurationError(OpsviRagError):
    """Configuration-related errors in opsvi-rag."""
    pass

class OpsviRagConnectionError(OpsviRagError):
    """Connection-related errors in opsvi-rag."""
    pass

class OpsviRagValidationError(OpsviRagError):
    """Validation-related errors in opsvi-rag."""
    pass

class OpsviRagTimeoutError(OpsviRagError):
    """Timeout-related errors in opsvi-rag."""
    pass

class OpsviRagResourceError(OpsviRagError):
    """Resource-related errors in opsvi-rag."""
    pass

class OpsviRagInitializationError(OpsviRagError):
    """Initialization-related errors in opsvi-rag."""
    pass

class OpsviRagShutdownError(OpsviRagError):
    """Shutdown-related errors in opsvi-rag."""
    pass

# Library-specific exceptions

