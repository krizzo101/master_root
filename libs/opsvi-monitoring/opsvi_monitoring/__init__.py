"""opsvi-monitoring - Monitoring and observability.

Comprehensive opsvi-monitoring library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

from .config.settings import OpsviMonitoringSettings, get_settings

# Core exports
from .core.base import BaseComponent, ComponentError
from .exceptions.base import LibraryConfigurationError, LibraryError

# Service-specific exports
# from .providers.base import Provider  # Commented out - fix needed
# from .schemas.models import Model  # Commented out - fix needed

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    "BaseComponent",
    "ComponentError",
    "OpsviMonitoringSettings",
    "get_settings",
    "LibraryError",
    "LibraryConfigurationError",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
