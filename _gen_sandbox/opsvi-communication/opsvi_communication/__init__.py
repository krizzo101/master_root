"""opsvi-communication - Communication and messaging systems.

Comprehensive opsvi-communication library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviCommunicationManager
from .config.settings import OpsviCommunicationSettings, get_settings
from .exceptions.base import OpsviCommunicationError, OpsviCommunicationConfigurationError

# Service-specific exports
from .providers.base import OpsviCommunicationProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviCommunicationManager,
    OpsviCommunicationSettings, get_settings,
    OpsviCommunicationError, OpsviCommunicationConfigurationError,
    # Service
    OpsviCommunicationProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
