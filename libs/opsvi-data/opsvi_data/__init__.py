"""opsvi-data - Data services for OPSVI applications.

Comprehensive data library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Provider exports
from .providers.arango_provider import (
    ArangoDBProvider,
    ArangoDBConfig,
    ArangoDBError,
)

from .providers.postgresql_provider import (
    PostgreSQLProvider,
    PostgreSQLConfig,
    PostgreSQLError,
)

from .providers.redis_provider import (
    RedisProvider,
    RedisConfig,
    RedisError,
)

__all__ = [
    # ArangoDB
    "ArangoDBProvider",
    "ArangoDBConfig",
    "ArangoDBError",
    # PostgreSQL
    "PostgreSQLProvider",
    "PostgreSQLConfig",
    "PostgreSQLError",
    # Redis
    "RedisProvider",
    "RedisConfig",
    "RedisError",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
