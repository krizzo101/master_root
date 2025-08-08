"""opsvi-data - Data management and database access.

Comprehensive opsvi-data library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviDataManager
from .config.settings import OpsviDataSettings, get_settings
from .exceptions.base import OpsviDataError, OpsviDataConfigurationError

# Service-specific exports
from .providers.base import OpsviDataProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviDataManager,
    OpsviDataSettings, get_settings,
    OpsviDataError, OpsviDataConfigurationError,
    # Service
    OpsviDataProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
