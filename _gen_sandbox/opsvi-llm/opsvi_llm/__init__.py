"""opsvi-llm - LLM integration and management.

Comprehensive opsvi-llm library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import OpsviLlmManager
from .config.settings import OpsviLlmSettings, get_settings
from .exceptions.base import OpsviLlmError, OpsviLlmConfigurationError

# Service-specific exports
from .providers.base import OpsviLlmProvider

# RAG-specific exports

# Manager-specific exports

__all__ = [
    # Core
    OpsviLlmManager,
    OpsviLlmSettings, get_settings,
    OpsviLlmError, OpsviLlmConfigurationError,
    # Service
    OpsviLlmProvider,
]

# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__

def get_author() -> str:
    """Get the library author."""
    return __author__
