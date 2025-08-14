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
from .persistence import (
    PersistenceBackend,
    PersistenceError,
    JSONBackend,
    MemoryBackend,
    RedisBackend,
)
from .middleware import (
    AuthMiddleware,
    BasicAuthMiddleware,
    TokenAuthMiddleware,
    MetricsMiddleware,
    PrometheusMetricsMiddleware,
    TracingMiddleware,
    OpenTelemetryMiddleware,
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
    # Persistence
    "PersistenceBackend",
    "PersistenceError",
    "JSONBackend",
    "MemoryBackend",
    "RedisBackend",
    # Middleware
    "AuthMiddleware",
    "BasicAuthMiddleware",
    "TokenAuthMiddleware",
    "MetricsMiddleware",
    "PrometheusMetricsMiddleware",
    "TracingMiddleware",
    "OpenTelemetryMiddleware",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
