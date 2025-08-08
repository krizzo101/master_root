"""opsvi-pipeline - Data processing pipeline orchestration.

Comprehensive opsvi-pipeline library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviPipelineManager
from .config.settings import OpsviPipelineSettings, get_settings
from .exceptions.base import OpsviPipelineError, OpsviPipelineConfigurationError

# Service-specific exports

# RAG-specific exports

# Manager-specific exports
from .coordinators.base import OpsviPipelineCoordinator

__all__ = [
    # Core
    OpsviPipelineManager,
    OpsviPipelineSettings, get_settings,
    OpsviPipelineError, OpsviPipelineConfigurationError,
    # Manager
    OpsviPipelineCoordinator,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
