"""Exception classes for opsvi-gateway.


"""

from opsvi_foundation.exceptions.base import OPSVIError

class OpsviGatewayError(OPSVIError):
    """Base exception for all opsvi-gateway errors."""
    pass

class OpsviGatewayConfigurationError(OpsviGatewayError):
    """Configuration-related errors in opsvi-gateway."""
    pass

class OpsviGatewayConnectionError(OpsviGatewayError):
    """Connection-related errors in opsvi-gateway."""
    pass

class OpsviGatewayValidationError(OpsviGatewayError):
    """Validation-related errors in opsvi-gateway."""
    pass

class OpsviGatewayTimeoutError(OpsviGatewayError):
    """Timeout-related errors in opsvi-gateway."""
    pass

class OpsviGatewayResourceError(OpsviGatewayError):
    """Resource-related errors in opsvi-gateway."""
    pass

class OpsviGatewayInitializationError(OpsviGatewayError):
    """Initialization-related errors in opsvi-gateway."""
    pass

class OpsviGatewayShutdownError(OpsviGatewayError):
    """Shutdown-related errors in opsvi-gateway."""
    pass

# Library-specific exceptions

