"""opsvi-auth - Authentication and authorization system.

Comprehensive opsvi-auth library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviAuthManager
from .config.settings import OpsviAuthSettings, get_settings
from .exceptions.base import OpsviAuthError, OpsviAuthConfigurationError

# Service-specific exports
from .providers.base import OpsviAuthProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviAuthManager,
    OpsviAuthSettings, get_settings,
    OpsviAuthError, OpsviAuthConfigurationError,
    # Service
    OpsviAuthProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
