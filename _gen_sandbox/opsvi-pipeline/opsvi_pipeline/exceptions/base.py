"""Exception classes for opsvi-pipeline.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviPipelineError(OPSVIError):
    """Base exception for all opsvi-pipeline errors."""
    pass

class OpsviPipelineConfigurationError(OpsviPipelineError):
    """Configuration-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineConnectionError(OpsviPipelineError):
    """Connection-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineValidationError(OpsviPipelineError):
    """Validation-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineTimeoutError(OpsviPipelineError):
    """Timeout-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineResourceError(OpsviPipelineError):
    """Resource-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineInitializationError(OpsviPipelineError):
    """Initialization-related errors in opsvi-pipeline."""
    pass

class OpsviPipelineShutdownError(OpsviPipelineError):
    """Shutdown-related errors in opsvi-pipeline."""
    pass

# Library-specific exceptions

