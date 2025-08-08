"""opsvi-fs - File system and storage management.

Comprehensive opsvi-fs library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviFsManager
from .config.settings import OpsviFsSettings, get_settings
from .exceptions.base import OpsviFsError, OpsviFsConfigurationError

# Service-specific exports
from .providers.base import OpsviFsProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviFsManager,
    OpsviFsSettings, get_settings,
    OpsviFsError, OpsviFsConfigurationError,
    # Service
    OpsviFsProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
