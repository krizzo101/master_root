"""OPSVI Auth Library.

Comprehensive authentication and authorization for the OPSVI ecosystem.
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__description__ = "Authentication and authorization for OPSVI"

# Core exports
from .providers.base import (
    BaseAuthProvider,
    AuthConfig,
    User,
    Role,
    Token,
    AuthResult,
    AuthType,
    Permission,
    AuthStatus,
    AuthError,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    ProviderError,
)

from .providers.jwt_provider import (
    JWTProvider,
    JWTConfig,
)

# Convenience exports
__all__ = [
    # Core
    "BaseAuthProvider",
    "AuthConfig",
    "User",
    "Role",
    "Token",
    "AuthResult",
    "AuthType",
    "Permission",
    "AuthStatus",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "TokenError",
    "ProviderError",
    # JWT Provider
    "JWTProvider",
    "JWTConfig",
]


def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__


def get_description() -> str:
    """Get the library description."""
    return __description__
