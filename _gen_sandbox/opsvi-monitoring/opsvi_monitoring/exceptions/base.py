"""Exception classes for opsvi-monitoring.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviMonitoringError(OPSVIError):
    """Base exception for all opsvi-monitoring errors."""
    pass

class OpsviMonitoringConfigurationError(OpsviMonitoringError):
    """Configuration-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringConnectionError(OpsviMonitoringError):
    """Connection-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringValidationError(OpsviMonitoringError):
    """Validation-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringTimeoutError(OpsviMonitoringError):
    """Timeout-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringResourceError(OpsviMonitoringError):
    """Resource-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringInitializationError(OpsviMonitoringError):
    """Initialization-related errors in opsvi-monitoring."""
    pass

class OpsviMonitoringShutdownError(OpsviMonitoringError):
    """Shutdown-related errors in opsvi-monitoring."""
    pass

# Library-specific exceptions

