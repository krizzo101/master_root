"""Exception classes for opsvi-deploy.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviDeployError(OPSVIError):
    """Base exception for all opsvi-deploy errors."""
    pass

class OpsviDeployConfigurationError(OpsviDeployError):
    """Configuration-related errors in opsvi-deploy."""
    pass

class OpsviDeployConnectionError(OpsviDeployError):
    """Connection-related errors in opsvi-deploy."""
    pass

class OpsviDeployValidationError(OpsviDeployError):
    """Validation-related errors in opsvi-deploy."""
    pass

class OpsviDeployTimeoutError(OpsviDeployError):
    """Timeout-related errors in opsvi-deploy."""
    pass

class OpsviDeployResourceError(OpsviDeployError):
    """Resource-related errors in opsvi-deploy."""
    pass

class OpsviDeployInitializationError(OpsviDeployError):
    """Initialization-related errors in opsvi-deploy."""
    pass

class OpsviDeployShutdownError(OpsviDeployError):
    """Shutdown-related errors in opsvi-deploy."""
    pass

# Library-specific exceptions

