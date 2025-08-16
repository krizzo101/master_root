"""opsvi-deploy - Deployment and infrastructure management.

Comprehensive opsvi-deploy library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviDeployManager
from .config.settings import OpsviDeploySettings, get_settings
from .exceptions.base import OpsviDeployError, OpsviDeployConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports
from .coordinators.base import OpsviDeployCoordinator

__all__ = [
    # Core
    OpsviDeployManager,
    OpsviDeploySettings, get_settings,
    OpsviDeployError, OpsviDeployConfigurationError,
    # Manager
    OpsviDeployCoordinator,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
