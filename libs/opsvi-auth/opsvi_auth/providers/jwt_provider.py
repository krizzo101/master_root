"""JWT-based authentication provider for OPSVI Auth library."""

import asyncio
import logging
import secrets
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import jwt
from pydantic import Field, ConfigDict

from .base import (
    BaseAuthProvider,
    AuthConfig,
    AuthResult,
    User,
    Token,
    AuthStatus,
    Permission,
    AuthError,
    AuthenticationError,
    TokenError,
)

logger = logging.getLogger(__name__)


class JWTConfig(AuthConfig):
    """Configuration for JWT authentication provider."""

    # JWT-specific configuration
    issuer: Optional[str] = Field(default=None, description="Token issuer")
    audience: Optional[str] = Field(default=None, description="Token audience")
    allow_refresh: bool = Field(default=True, description="Allow token refresh")

    # User storage (in-memory for demo, should be replaced with database)
    users: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="User storage"
    )
    roles: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Role storage"
    )

    model_config = ConfigDict(env_prefix="OPSVI_AUTH_JWT_")


class JWTProvider(BaseAuthProvider):
    """JWT-based authentication provider implementation."""

    def __init__(self, config: JWTConfig, **kwargs: Any) -> None:
        """Initialize JWT provider.

        Args:
            config: JWT configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.jwt_config = config
        self._revoked_tokens: set = set()
        self._user_roles: Dict[str, List[str]] = {}

    async def _initialize_provider(self) -> None:
        """Initialize JWT provider."""
        if not self.jwt_config.token_secret:
            # Generate a secure secret if not provided
            self.jwt_config.token_secret = secrets.token_urlsafe(32)
            logger.warning("No token secret provided, generated a new one")

        # Initialize default roles if none exist
        if not self.jwt_config.roles:
            self.jwt_config.roles = {
                "admin": {
                    "id": "admin",
                    "name": "Administrator",
                    "description": "Full system access",
                    "permissions": [Permission.ADMIN.value],
                },
                "user": {
                    "id": "user",
                    "name": "User",
                    "description": "Standard user access",
                    "permissions": [Permission.READ.value, Permission.WRITE.value],
                },
                "readonly": {
                    "id": "readonly",
                    "name": "Read Only",
                    "description": "Read-only access",
                    "permissions": [Permission.READ.value],
                },
            }

        logger.info("JWT provider initialized successfully")

    async def _shutdown_provider(self) -> None:
        """Shutdown JWT provider."""
        # Clear caches
        self._users_cache.clear()
        self._tokens_cache.clear()
        self._revoked_tokens.clear()
        self._user_roles.clear()
        logger.info("JWT provider shutdown successfully")

    async def _check_provider_health(self) -> bool:
        """Check JWT provider health."""
        try:
            # Check if we can create and validate a test token
            test_payload = {
                "test": True,
                "exp": datetime.utcnow() + timedelta(seconds=60),
            }
            test_token = jwt.encode(
                test_payload,
                self.jwt_config.token_secret,
                algorithm=self.jwt_config.token_algorithm,
            )
            jwt.decode(
                test_token,
                self.jwt_config.token_secret,
                algorithms=[self.jwt_config.token_algorithm],
            )
            return True
        except Exception as e:
            logger.error(f"JWT provider health check failed: {e}")
            return False

    async def _authenticate_user(self, credentials: Dict[str, Any]) -> AuthResult:
        """Authenticate a user with username/password."""
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return AuthResult(
                success=False,
                status=AuthStatus.UNAUTHENTICATED,
                message="Username and password are required",
            )

        # Find user in storage
        user_data = None
        for user_id, user_info in self.jwt_config.users.items():
            if user_info.get("username") == username:
                user_data = user_info
                break

        if not user_data:
            return AuthResult(
                success=False,
                status=AuthStatus.UNAUTHENTICATED,
                message="Invalid credentials",
            )

        # Verify password (in production, use proper password hashing)
        stored_password_hash = user_data.get("password_hash")
        if not stored_password_hash or not self._verify_password(
            password, stored_password_hash
        ):
            return AuthResult(
                success=False,
                status=AuthStatus.UNAUTHENTICATED,
                message="Invalid credentials",
            )

        # Check if user is active
        if not user_data.get("is_active", True):
            return AuthResult(
                success=False,
                status=AuthStatus.LOCKED,
                message="User account is locked",
            )

        # Create user object
        user = User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data.get("email"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            is_active=user_data.get("is_active", True),
            is_verified=user_data.get("is_verified", False),
            created_at=user_data.get("created_at", datetime.utcnow()),
            updated_at=user_data.get("updated_at", datetime.utcnow()),
        )

        # Generate tokens
        token = await self._generate_tokens(user)

        return AuthResult(
            success=True,
            user=user,
            token=token,
            status=AuthStatus.AUTHENTICATED,
            message="Authentication successful",
        )

    async def _validate_token(self, token: str) -> AuthResult:
        """Validate a JWT token."""
        try:
            # Check if token is revoked
            if token in self._revoked_tokens:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="Token has been revoked",
                )

            # Decode and validate token
            payload = jwt.decode(
                token,
                self.jwt_config.token_secret,
                algorithms=[self.jwt_config.token_algorithm],
                issuer=self.jwt_config.issuer,
                audience=self.jwt_config.audience,
            )

            # Check if token is expired
            exp_timestamp = payload.get("exp")
            if (
                exp_timestamp
                and datetime.utcfromtimestamp(exp_timestamp) < datetime.utcnow()
            ):
                return AuthResult(
                    success=False,
                    status=AuthStatus.EXPIRED,
                    message="Token has expired",
                )

            # Get user from payload
            user_id = payload.get("sub")
            if not user_id:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="Invalid token payload",
                )

            # Get user data
            user_data = self.jwt_config.users.get(user_id)
            if not user_data:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="User not found",
                )

            # Create user object
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                is_active=user_data.get("is_active", True),
                is_verified=user_data.get("is_verified", False),
                created_at=user_data.get("created_at", datetime.utcnow()),
                updated_at=user_data.get("updated_at", datetime.utcnow()),
            )

            # Create token object
            token_obj = Token(
                access_token=token,
                refresh_token=payload.get("refresh_token"),
                token_type="Bearer",
                expires_at=(
                    datetime.utcfromtimestamp(exp_timestamp)
                    if exp_timestamp
                    else datetime.utcnow() + timedelta(hours=1)
                ),
                user_id=user_id,
                scopes=payload.get("scopes", []),
            )

            return AuthResult(
                success=True,
                user=user,
                token=token_obj,
                status=AuthStatus.AUTHENTICATED,
                message="Token is valid",
            )

        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                status=AuthStatus.EXPIRED,
                message="Token has expired",
            )
        except jwt.InvalidTokenError as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Invalid token: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Token validation failed",
            )

    async def _refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh an authentication token."""
        if not self.jwt_config.allow_refresh:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Token refresh is not allowed",
            )

        try:
            # Validate refresh token
            payload = jwt.decode(
                refresh_token,
                self.jwt_config.token_secret,
                algorithms=[self.jwt_config.token_algorithm],
            )

            # Check if refresh token is expired
            exp_timestamp = payload.get("exp")
            if (
                exp_timestamp
                and datetime.utcfromtimestamp(exp_timestamp) < datetime.utcnow()
            ):
                return AuthResult(
                    success=False,
                    status=AuthStatus.EXPIRED,
                    message="Refresh token has expired",
                )

            # Get user ID from refresh token
            user_id = payload.get("sub")
            if not user_id:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="Invalid refresh token",
                )

            # Get user data
            user_data = self.jwt_config.users.get(user_id)
            if not user_data:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="User not found",
                )

            # Create user object
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                is_active=user_data.get("is_active", True),
                is_verified=user_data.get("is_verified", False),
                created_at=user_data.get("created_at", datetime.utcnow()),
                updated_at=user_data.get("updated_at", datetime.utcnow()),
            )

            # Generate new tokens
            new_token = await self._generate_tokens(user)

            return AuthResult(
                success=True,
                user=user,
                token=new_token,
                status=AuthStatus.AUTHENTICATED,
                message="Token refreshed successfully",
            )

        except jwt.InvalidTokenError as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Invalid refresh token: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Token refresh failed",
            )

    async def _revoke_token(self, token: str) -> bool:
        """Revoke an authentication token."""
        try:
            # Add token to revoked set
            self._revoked_tokens.add(token)

            # Remove from cache if present
            if token in self._tokens_cache:
                del self._tokens_cache[token]

            return True
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            return False

    async def _check_permission(
        self, user_id: str, permission: Permission, resource: Optional[str] = None
    ) -> bool:
        """Check if a user has a specific permission."""
        # Get user roles
        user_roles = self._user_roles.get(user_id, [])

        # Check each role for the required permission
        for role_id in user_roles:
            role_data = self.jwt_config.roles.get(role_id)
            if role_data:
                role_permissions = role_data.get("permissions", [])
                if permission.value in role_permissions:
                    return True

        return False

    async def _generate_tokens(self, user: User) -> Token:
        """Generate access and refresh tokens for a user."""
        now = datetime.utcnow()

        # Create access token payload
        access_payload = {
            "sub": user.id,
            "username": user.username,
            "iat": now,
            "exp": now + timedelta(seconds=self.jwt_config.token_expiry),
            "type": "access",
        }

        if self.jwt_config.issuer:
            access_payload["iss"] = self.jwt_config.issuer

        if self.jwt_config.audience:
            access_payload["aud"] = self.jwt_config.audience

        # Create refresh token payload
        refresh_payload = {
            "sub": user.id,
            "username": user.username,
            "iat": now,
            "exp": now + timedelta(seconds=self.jwt_config.refresh_token_expiry),
            "type": "refresh",
        }

        if self.jwt_config.issuer:
            refresh_payload["iss"] = self.jwt_config.issuer

        if self.jwt_config.audience:
            refresh_payload["aud"] = self.jwt_config.audience

        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            self.jwt_config.token_secret,
            algorithm=self.jwt_config.token_algorithm,
        )
        refresh_token = jwt.encode(
            refresh_payload,
            self.jwt_config.token_secret,
            algorithm=self.jwt_config.token_algorithm,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_at=now + timedelta(seconds=self.jwt_config.token_expiry),
            user_id=user.id,
            scopes=[],
        )

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against its hash."""
        # In production, use proper password hashing (bcrypt, argon2, etc.)
        # This is a simple SHA-256 hash for demonstration
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == stored_hash

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        # In production, use proper password hashing (bcrypt, argon2, etc.)
        # This is a simple SHA-256 hash for demonstration
        return hashlib.sha256(password.encode()).hexdigest()

    async def create_user(
        self, username: str, password: str, email: Optional[str] = None, **kwargs: Any
    ) -> User:
        """Create a new user."""
        # Check if username already exists
        for user_data in self.jwt_config.users.values():
            if user_data.get("username") == username:
                raise AuthenticationError("Username already exists")

        # Create user ID
        user_id = f"user_{len(self.jwt_config.users) + 1}"

        # Hash password
        password_hash = self._hash_password(password)

        # Create user data
        user_data = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **kwargs,
        }

        # Store user
        self.jwt_config.users[user_id] = user_data

        # Create user object
        user = User(
            id=user_id,
            username=username,
            email=email,
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            is_active=True,
            is_verified=False,
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"],
        )

        logger.info(f"Created user: {username}")
        return user

    async def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user."""
        if user_id not in self.jwt_config.users:
            raise AuthenticationError("User not found")

        if role_id not in self.jwt_config.roles:
            raise AuthenticationError("Role not found")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = []

        if role_id not in self._user_roles[user_id]:
            self._user_roles[user_id].append(role_id)

        logger.info(f"Assigned role {role_id} to user {user_id}")
        return True
