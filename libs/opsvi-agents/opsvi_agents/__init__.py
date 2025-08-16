"""opsvi-agents - Multi-agent system management.

Comprehensive opsvi-agents library for the OPSVI ecosystem
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
# TODO: Implement coordinators and schedulers
# from .coordinators.base import Coordinator
# from .schedulers.base import Scheduler

__all__ = [
    # Core
    "BaseComponent", "ComponentError",
    "LibraryConfig", "LibrarySettings", 
    "LibraryError", "LibraryConfigurationError",
    # Manager - to be implemented
    # "Coordinator",
    # "Scheduler"]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
