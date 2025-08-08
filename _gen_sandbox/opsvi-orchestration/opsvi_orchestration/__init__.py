"""opsvi-orchestration - Workflow and task orchestration.

Comprehensive opsvi-orchestration library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviOrchestrationManager
from .config.settings import OpsviOrchestrationSettings, get_settings
from .exceptions.base import OpsviOrchestrationError, OpsviOrchestrationConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports
from .coordinators.base import OpsviOrchestrationCoordinator

__all__ = [
    # Core
    OpsviOrchestrationManager,
    OpsviOrchestrationSettings, get_settings,
    OpsviOrchestrationError, OpsviOrchestrationConfigurationError,
    # Manager
    OpsviOrchestrationCoordinator,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
