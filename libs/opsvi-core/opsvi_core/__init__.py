"""opsvi-core - Core functionality for OPSVI applications.

Comprehensive opsvi-core library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import (
    ServiceRegistry,
    EventBus,
    StateManager,
    ServiceInfo,
    ServiceStatus,
    CoreConfig,
    CoreError,
    ServiceRegistryError,
    EventBusError,
    StateManagerError,
)

__all__ = [
    # Core components
    "ServiceRegistry",
    "EventBus",
    "StateManager",
    "ServiceInfo",
    "ServiceStatus",
    "CoreConfig",
    # Exceptions
    "CoreError",
    "ServiceRegistryError",
    "EventBusError",
    "StateManagerError",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
