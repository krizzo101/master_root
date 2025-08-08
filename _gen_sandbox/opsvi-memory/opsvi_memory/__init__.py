"""opsvi-memory - Memory and caching systems.

Comprehensive opsvi-memory library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviMemoryManager
from .config.settings import OpsviMemorySettings, get_settings
from .exceptions.base import OpsviMemoryError, OpsviMemoryConfigurationError

# Service-specific exports
from .providers.base import OpsviMemoryProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviMemoryManager,
    OpsviMemorySettings, get_settings,
    OpsviMemoryError, OpsviMemoryConfigurationError,
    # Service
    OpsviMemoryProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
