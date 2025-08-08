"""opsvi-monitoring - Monitoring and observability.

Comprehensive opsvi-monitoring library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviMonitoringManager
from .config.settings import OpsviMonitoringSettings, get_settings
from .exceptions.base import OpsviMonitoringError, OpsviMonitoringConfigurationError

# Service-specific exports
from .providers.base import OpsviMonitoringProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviMonitoringManager,
    OpsviMonitoringSettings, get_settings,
    OpsviMonitoringError, OpsviMonitoringConfigurationError,
    # Service
    OpsviMonitoringProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
