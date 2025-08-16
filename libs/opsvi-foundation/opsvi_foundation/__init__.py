"""opsvi-foundation - Foundation library providing base components and utilities.

Comprehensive opsvi-foundation library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import BaseComponent, ComponentError
from .config.settings import LibraryConfig, LibrarySettings
from .exceptions.base import LibraryError, LibraryConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    BaseComponent, ComponentError,
    LibraryConfig, LibrarySettings,
    LibraryError, LibraryConfigurationError,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
