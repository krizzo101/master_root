"""opsvi-core - Core functionality for OPSVI applications.

Comprehensive opsvi-core library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviCoreManager
from .config.settings import OpsviCoreSettings, get_settings
from .exceptions.base import OpsviCoreError, OpsviCoreConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviCoreManager,
    OpsviCoreSettings, get_settings,
    OpsviCoreError, OpsviCoreConfigurationError,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
