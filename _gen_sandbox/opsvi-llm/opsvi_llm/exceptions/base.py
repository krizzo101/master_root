"""Exception classes for opsvi-llm.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviLlmError(OPSVIError):
    """Base exception for all opsvi-llm errors."""
    pass

class OpsviLlmConfigurationError(OpsviLlmError):
    """Configuration-related errors in opsvi-llm."""
    pass

class OpsviLlmConnectionError(OpsviLlmError):
    """Connection-related errors in opsvi-llm."""
    pass

class OpsviLlmValidationError(OpsviLlmError):
    """Validation-related errors in opsvi-llm."""
    pass

class OpsviLlmTimeoutError(OpsviLlmError):
    """Timeout-related errors in opsvi-llm."""
    pass

class OpsviLlmResourceError(OpsviLlmError):
    """Resource-related errors in opsvi-llm."""
    pass

class OpsviLlmInitializationError(OpsviLlmError):
    """Initialization-related errors in opsvi-llm."""
    pass

class OpsviLlmShutdownError(OpsviLlmError):
    """Shutdown-related errors in opsvi-llm."""
    pass

# Library-specific exceptions

