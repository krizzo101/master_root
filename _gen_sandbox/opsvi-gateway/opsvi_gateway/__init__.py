"""opsvi-gateway - Multi-interface gateway and API management.

Comprehensive opsvi-gateway library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviGatewayManager
from .config.settings import OpsviGatewaySettings, get_settings
from .exceptions.base import OpsviGatewayError, OpsviGatewayConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports
from .coordinators.base import OpsviGatewayCoordinator

__all__ = [
    # Core
    OpsviGatewayManager,
    OpsviGatewaySettings, get_settings,
    OpsviGatewayError, OpsviGatewayConfigurationError,
    # Manager
    OpsviGatewayCoordinator,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
