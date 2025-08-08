"""opsvi-agents - Multi-agent system management.

Comprehensive opsvi-agents library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviAgentsManager
from .config.settings import OpsviAgentsSettings, get_settings
from .exceptions.base import OpsviAgentsError, OpsviAgentsConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports
from .coordinators.base import OpsviAgentsCoordinator

__all__ = [
    # Core
    OpsviAgentsManager,
    OpsviAgentsSettings, get_settings,
    OpsviAgentsError, OpsviAgentsConfigurationError,
    # Manager
    OpsviAgentsCoordinator,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
