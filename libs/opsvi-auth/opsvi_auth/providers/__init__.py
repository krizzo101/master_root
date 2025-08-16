"""Authentication providers module for OPSVI Auth library."""

from .base import (
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

from .jwt_provider import (
    JWTProvider,
    JWTConfig,
)

__all__ = [
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
    "JWTProvider",
    "JWTConfig",
]
