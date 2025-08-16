"""opsvi-http - HTTP client and server functionality.

Comprehensive opsvi-http library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviHttpManager
from .config.settings import OpsviHttpSettings, get_settings
from .exceptions.base import OpsviHttpError, OpsviHttpConfigurationError

# Service-specific exports
from .providers.base import OpsviHttpProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviHttpManager,
    OpsviHttpSettings, get_settings,
    OpsviHttpError, OpsviHttpConfigurationError,
    # Service
    OpsviHttpProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
