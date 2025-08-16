"""opsvi-security - Security and encryption utilities.

Comprehensive opsvi-security library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviSecurityManager
from .config.settings import OpsviSecuritySettings, get_settings
from .exceptions.base import OpsviSecurityError, OpsviSecurityConfigurationError

# Service-specific exports
from .providers.base import OpsviSecurityProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviSecurityManager,
    OpsviSecuritySettings, get_settings,
    OpsviSecurityError, OpsviSecurityConfigurationError,
    # Service
    OpsviSecurityProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
