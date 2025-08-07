"""opsvi-fs - File system and storage management.

Comprehensive opsvi-fs library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import BaseComponent, ComponentError
from .config.settings import LibraryConfig, LibrarySettings
from .exceptions.base import LibraryError, LibraryConfigurationError

# Service-specific exports
from .providers.base import True
from .schemas.models import 

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    BaseComponent, ComponentError,
    LibraryConfig, LibrarySettings,
    LibraryError, LibraryConfigurationError,
    # Service
    True,
    ,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
