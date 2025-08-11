"""Base authentication provider interface for OPSVI Auth library.

Comprehensive authentication and authorization abstraction for the OPSVI ecosystem
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncIterator
import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field, ConfigDict

from opsvi_foundation import BaseComponent, ComponentError, BaseSettings

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication type enumeration."""

    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    SESSION = "session"
    LDAP = "ldap"
    SAML = "saml"
    OPENID_CONNECT = "openid_connect"


class Permission(Enum):
    """Permission enumeration."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"


class AuthStatus(Enum):
    """Authentication status enumeration."""

    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    INVALID = "invalid"
    LOCKED = "locked"


class AuthError(ComponentError):
    """Base exception for authentication errors."""

    pass


class AuthenticationError(AuthError):
    """Authentication-specific errors."""

    pass


class AuthorizationError(AuthError):
    """Authorization-specific errors."""

    pass


class TokenError(AuthError):
    """Token-related errors."""

    pass


class ProviderError(AuthError):
    """Provider-specific errors."""

    pass


class AuthConfig(BaseSettings):
    """Base configuration for authentication providers."""

    # Provider configuration
    auth_type: AuthType = Field(description="Authentication type")
    enabled: bool = Field(default=True, description="Enable authentication")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Token configuration
    token_secret: Optional[str] = Field(default=None, description="Token secret key")
    token_algorithm: str = Field(default="HS256", description="Token algorithm")
    token_expiry: int = Field(default=3600, description="Token expiry in seconds")
    refresh_token_expiry: int = Field(
        default=86400, description="Refresh token expiry in seconds"
    )

    # Session configuration
    session_timeout: int = Field(default=1800, description="Session timeout in seconds")
    max_sessions_per_user: int = Field(
        default=5, description="Maximum sessions per user"
    )

    # Rate limiting
    max_login_attempts: int = Field(default=5, description="Maximum login attempts")
    lockout_duration: int = Field(
        default=300, description="Lockout duration in seconds"
    )

    # Security configuration
    password_min_length: int = Field(default=8, description="Minimum password length")
    require_strong_password: bool = Field(
        default=True, description="Require strong password"
    )
    enable_mfa: bool = Field(
        default=False, description="Enable multi-factor authentication"
    )

    # Provider-specific configuration
    provider_config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )

    model_config = ConfigDict(env_prefix="OPSVI_AUTH_")


class User(BaseModel):
    """User model."""

    id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: Optional[str] = Field(default=None, description="Email address")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    is_active: bool = Field(default=True, description="User active status")
    is_verified: bool = Field(default=False, description="Email verification status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Role(BaseModel):
    """Role model."""

    id: str = Field(description="Role ID")
    name: str = Field(description="Role name")
    description: Optional[str] = Field(default=None, description="Role description")
    permissions: List[Permission] = Field(
        default_factory=list, description="Role permissions"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Token(BaseModel):
    """Token model."""

    access_token: str = Field(description="Access token")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_at: datetime = Field(description="Token expiry timestamp")
    user_id: str = Field(description="User ID")
    scopes: List[str] = Field(default_factory=list, description="Token scopes")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AuthResult(BaseModel):
    """Authentication result model."""

    success: bool = Field(description="Authentication success")
    user: Optional[User] = Field(default=None, description="Authenticated user")
    token: Optional[Token] = Field(default=None, description="Authentication token")
    status: AuthStatus = Field(description="Authentication status")
    message: Optional[str] = Field(default=None, description="Result message")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseAuthProvider(BaseComponent):
    """Base class for authentication providers.

    Provides common functionality for all authentication providers in the OPSVI ecosystem.
    """

    def __init__(self, config: AuthConfig, **kwargs: Any) -> None:
        """Initialize authentication provider.

        Args:
            config: Authentication configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(f"auth-provider-{id(self)}", config.model_dump())
        self.config = config
        self._users_cache: Dict[str, User] = {}
        self._tokens_cache: Dict[str, Token] = {}
        self._auth_count = 0
        self._error_count = 0
        self._start_time = datetime.utcnow()

    async def _initialize_impl(self) -> None:
        """Initialize the authentication provider."""
        try:
            await self._initialize_provider()
            logger.info(
                f"Initialized authentication provider: {self.config.auth_type.value}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize authentication provider: {e}")
            raise ProviderError(f"Provider initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown the authentication provider."""
        try:
            await self._shutdown_provider()
            logger.info("Authentication provider shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown authentication provider: {e}")
            raise ProviderError(f"Provider shutdown failed: {e}") from e

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        try:
            # Try a simple health check
            return await self._check_provider_health()
        except Exception as e:
            logger.error(f"Authentication provider health check failed: {e}")
            return False

    @abstractmethod
    async def _initialize_provider(self) -> None:
        """Initialize the specific authentication provider."""
        pass

    @abstractmethod
    async def _shutdown_provider(self) -> None:
        """Shutdown the specific authentication provider."""
        pass

    @abstractmethod
    async def _check_provider_health(self) -> bool:
        """Check provider health."""
        pass

    @abstractmethod
    async def _authenticate_user(self, credentials: Dict[str, Any]) -> AuthResult:
        """Authenticate a user with credentials."""
        pass

    @abstractmethod
    async def _validate_token(self, token: str) -> AuthResult:
        """Validate an authentication token."""
        pass

    @abstractmethod
    async def _refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh an authentication token."""
        pass

    @abstractmethod
    async def _revoke_token(self, token: str) -> bool:
        """Revoke an authentication token."""
        pass

    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """Authenticate a user."""
        if not self._initialized:
            raise AuthenticationError("Authentication provider not initialized")

        self._auth_count += 1

        try:
            result = await self._authenticate_user(credentials)

            if result.success and result.token:
                # Cache the token
                self._tokens_cache[result.token.access_token] = result.token
                if result.user:
                    self._users_cache[result.user.id] = result.user

            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Authentication failed: {e}") from e

    async def validate_token(self, token: str) -> AuthResult:
        """Validate an authentication token."""
        if not self._initialized:
            raise AuthenticationError("Authentication provider not initialized")

        # Check cache first
        if token in self._tokens_cache:
            cached_token = self._tokens_cache[token]
            if datetime.utcnow() < cached_token.expires_at:
                return AuthResult(
                    success=True,
                    user=self._users_cache.get(cached_token.user_id),
                    token=cached_token,
                    status=AuthStatus.AUTHENTICATED,
                )
            else:
                # Remove expired token from cache
                del self._tokens_cache[token]

        try:
            result = await self._validate_token(token)

            if result.success and result.token:
                # Cache the token
                self._tokens_cache[result.token.access_token] = result.token
                if result.user:
                    self._users_cache[result.user.id] = result.user

            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"Token validation failed: {e}")
            raise TokenError(f"Token validation failed: {e}") from e

    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh an authentication token."""
        if not self._initialized:
            raise AuthenticationError("Authentication provider not initialized")

        try:
            result = await self._refresh_token(refresh_token)

            if result.success and result.token:
                # Update cache
                self._tokens_cache[result.token.access_token] = result.token
                if result.user:
                    self._users_cache[result.user.id] = result.user

            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"Token refresh failed: {e}")
            raise TokenError(f"Token refresh failed: {e}") from e

    async def revoke_token(self, token: str) -> bool:
        """Revoke an authentication token."""
        if not self._initialized:
            raise AuthenticationError("Authentication provider not initialized")

        try:
            success = await self._revoke_token(token)

            if success and token in self._tokens_cache:
                # Remove from cache
                del self._tokens_cache[token]

            return success
        except Exception as e:
            self._error_count += 1
            logger.error(f"Token revocation failed: {e}")
            raise TokenError(f"Token revocation failed: {e}") from e

    async def check_permission(
        self, user_id: str, permission: Permission, resource: Optional[str] = None
    ) -> bool:
        """Check if a user has a specific permission."""
        if not self._initialized:
            raise AuthorizationError("Authentication provider not initialized")

        try:
            return await self._check_permission(user_id, permission, resource)
        except Exception as e:
            self._error_count += 1
            logger.error(f"Permission check failed: {e}")
            raise AuthorizationError(f"Permission check failed: {e}") from e

    @abstractmethod
    async def _check_permission(
        self, user_id: str, permission: Permission, resource: Optional[str] = None
    ) -> bool:
        """Check if a user has a specific permission (implementation specific)."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        uptime = datetime.utcnow() - self._start_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_authentications": self._auth_count,
            "error_count": self._error_count,
            "success_rate": (self._auth_count - self._error_count)
            / max(self._auth_count, 1),
            "cached_users": len(self._users_cache),
            "cached_tokens": len(self._tokens_cache),
            "initialized": self._initialized,
        }
