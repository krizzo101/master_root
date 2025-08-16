"""Tests for OPSVI Auth provider functionality."""

import pytest
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from opsvi_auth import (
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
    JWTProvider,
    JWTConfig,
)
from opsvi_foundation import ComponentError


class MockAuthProvider(BaseAuthProvider):
    """Mock authentication provider for testing."""

    async def _initialize_provider(self) -> None:
        """Initialize mock provider."""
        pass

    async def _shutdown_provider(self) -> None:
        """Shutdown mock provider."""
        pass

    async def _check_provider_health(self) -> bool:
        """Check mock provider health."""
        return True

    async def _authenticate_user(self, credentials: Dict[str, Any]) -> AuthResult:
        """Mock user authentication."""
        username = credentials.get("username")
        password = credentials.get("password")

        if username == "testuser" and password == "testpass":
            user = User(
                id="user_1",
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                is_active=True,
                is_verified=True,
            )

            token = Token(
                access_token="mock_access_token",
                refresh_token="mock_refresh_token",
                token_type="Bearer",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                user_id="user_1",
                scopes=["read", "write"],
            )

            return AuthResult(
                success=True,
                user=user,
                token=token,
                status=AuthStatus.AUTHENTICATED,
                message="Authentication successful",
            )
        else:
            return AuthResult(
                success=False,
                status=AuthStatus.UNAUTHENTICATED,
                message="Invalid credentials",
            )

    async def _validate_token(self, token: str) -> AuthResult:
        """Mock token validation."""
        if token == "valid_token":
            user = User(
                id="user_1",
                username="testuser",
                email="test@example.com",
                is_active=True,
                is_verified=True,
            )

            token_obj = Token(
                access_token=token,
                refresh_token="mock_refresh_token",
                token_type="Bearer",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                user_id="user_1",
                scopes=["read", "write"],
            )

            return AuthResult(
                success=True,
                user=user,
                token=token_obj,
                status=AuthStatus.AUTHENTICATED,
                message="Token is valid",
            )
        else:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Invalid token",
            )

    async def _refresh_token(self, refresh_token: str) -> AuthResult:
        """Mock token refresh."""
        if refresh_token == "valid_refresh_token":
            user = User(
                id="user_1",
                username="testuser",
                email="test@example.com",
                is_active=True,
                is_verified=True,
            )

            token = Token(
                access_token="new_access_token",
                refresh_token="new_refresh_token",
                token_type="Bearer",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                user_id="user_1",
                scopes=["read", "write"],
            )

            return AuthResult(
                success=True,
                user=user,
                token=token,
                status=AuthStatus.AUTHENTICATED,
                message="Token refreshed successfully",
            )
        else:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Invalid refresh token",
            )

    async def _revoke_token(self, token: str) -> bool:
        """Mock token revocation."""
        return token in ["valid_token", "mock_access_token"]

    async def _check_permission(
        self, user_id: str, permission: Permission, resource: Optional[str] = None
    ) -> bool:
        """Mock permission check."""
        if user_id == "user_1":
            if permission == Permission.READ:
                return True
            elif permission == Permission.WRITE:
                return True
            elif permission == Permission.ADMIN:
                return False
        return False


@pytest.fixture
def auth_config():
    """Create a test auth configuration."""
    return AuthConfig(
        auth_type=AuthType.JWT,
        enabled=True,
        debug=False,
        token_secret="test_secret_key",
        token_algorithm="HS256",
        token_expiry=3600,
        refresh_token_expiry=86400,
    )


@pytest.fixture
def jwt_config():
    """Create a test JWT configuration."""
    return JWTConfig(
        auth_type=AuthType.JWT,
        enabled=True,
        debug=False,
        token_secret="test_jwt_secret_key",
        token_algorithm="HS256",
        token_expiry=3600,
        refresh_token_expiry=86400,
        allow_refresh=True,
    )


@pytest.fixture
def mock_provider(auth_config):
    """Create a mock authentication provider."""
    return MockAuthProvider(auth_config)


class TestAuthConfig:
    """Test auth configuration."""

    def test_auth_config_defaults(self):
        """Test auth config default values."""
        config = AuthConfig(auth_type=AuthType.JWT)

        assert config.auth_type == AuthType.JWT
        assert config.enabled is True
        assert config.debug is False
        assert config.token_algorithm == "HS256"
        assert config.token_expiry == 3600
        assert config.refresh_token_expiry == 86400
        assert config.session_timeout == 1800
        assert config.max_sessions_per_user == 5
        assert config.max_login_attempts == 5
        assert config.lockout_duration == 300
        assert config.password_min_length == 8
        assert config.require_strong_password is True
        assert config.enable_mfa is False
        assert config.provider_config == {}

    def test_auth_config_custom_values(self):
        """Test auth config with custom values."""
        config = AuthConfig(
            auth_type=AuthType.OAUTH2,
            enabled=False,
            debug=True,
            token_secret="custom_secret",
            token_algorithm="RS256",
            token_expiry=7200,
            refresh_token_expiry=172800,
            session_timeout=3600,
            max_sessions_per_user=10,
            max_login_attempts=3,
            lockout_duration=600,
            password_min_length=12,
            require_strong_password=False,
            enable_mfa=True,
            provider_config={"custom": "value"},
        )

        assert config.auth_type == AuthType.OAUTH2
        assert config.enabled is False
        assert config.debug is True
        assert config.token_secret == "custom_secret"
        assert config.token_algorithm == "RS256"
        assert config.token_expiry == 7200
        assert config.refresh_token_expiry == 172800
        assert config.session_timeout == 3600
        assert config.max_sessions_per_user == 10
        assert config.max_login_attempts == 3
        assert config.lockout_duration == 600
        assert config.password_min_length == 12
        assert config.require_strong_password is False
        assert config.enable_mfa is True
        assert config.provider_config == {"custom": "value"}


class TestUser:
    """Test user model."""

    def test_user_creation(self):
        """Test user creation."""
        user = User(
            id="user_1",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=True,
        )

        assert user.id == "user_1"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.is_verified is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_defaults(self):
        """Test user default values."""
        user = User(
            id="user_1",
            username="testuser",
        )

        assert user.id == "user_1"
        assert user.username == "testuser"
        assert user.email is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.is_active is True
        assert user.is_verified is False


class TestRole:
    """Test role model."""

    def test_role_creation(self):
        """Test role creation."""
        role = Role(
            id="role_1",
            name="admin",
            description="Administrator role",
            permissions=[Permission.ADMIN, Permission.READ, Permission.WRITE],
        )

        assert role.id == "role_1"
        assert role.name == "admin"
        assert role.description == "Administrator role"
        assert len(role.permissions) == 3
        assert Permission.ADMIN in role.permissions
        assert Permission.READ in role.permissions
        assert Permission.WRITE in role.permissions
        assert isinstance(role.created_at, datetime)


class TestToken:
    """Test token model."""

    def test_token_creation(self):
        """Test token creation."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = Token(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            token_type="Bearer",
            expires_at=expires_at,
            user_id="user_1",
            scopes=["read", "write"],
        )

        assert token.access_token == "access_token_123"
        assert token.refresh_token == "refresh_token_123"
        assert token.token_type == "Bearer"
        assert token.expires_at == expires_at
        assert token.user_id == "user_1"
        assert token.scopes == ["read", "write"]


class TestAuthResult:
    """Test auth result model."""

    def test_auth_result_success(self):
        """Test successful auth result."""
        user = User(id="user_1", username="testuser")
        token = Token(
            access_token="token_123",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            user_id="user_1",
        )

        result = AuthResult(
            success=True,
            user=user,
            token=token,
            status=AuthStatus.AUTHENTICATED,
            message="Success",
            metadata={"key": "value"},
        )

        assert result.success is True
        assert result.user == user
        assert result.token == token
        assert result.status == AuthStatus.AUTHENTICATED
        assert result.message == "Success"
        assert result.metadata == {"key": "value"}

    def test_auth_result_failure(self):
        """Test failed auth result."""
        result = AuthResult(
            success=False,
            status=AuthStatus.UNAUTHENTICATED,
            message="Invalid credentials",
        )

        assert result.success is False
        assert result.user is None
        assert result.token is None
        assert result.status == AuthStatus.UNAUTHENTICATED
        assert result.message == "Invalid credentials"


class TestMockAuthProvider:
    """Test mock authentication provider functionality."""

    @pytest.mark.asyncio
    async def test_provider_initialization(self, auth_config):
        """Test authentication provider initialization."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        assert provider._initialized
        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_authentication_success(self, auth_config):
        """Test successful user authentication."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.authenticate(
                {
                    "username": "testuser",
                    "password": "testpass",
                }
            )

            assert result.success is True
            assert result.user is not None
            assert result.user.username == "testuser"
            assert result.token is not None
            assert result.status == AuthStatus.AUTHENTICATED
            assert result.message == "Authentication successful"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_authentication_failure(self, auth_config):
        """Test failed user authentication."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.authenticate(
                {
                    "username": "wronguser",
                    "password": "wrongpass",
                }
            )

            assert result.success is False
            assert result.user is None
            assert result.token is None
            assert result.status == AuthStatus.UNAUTHENTICATED
            assert result.message == "Invalid credentials"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_token_validation_success(self, auth_config):
        """Test successful token validation."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.validate_token("valid_token")

            assert result.success is True
            assert result.user is not None
            assert result.token is not None
            assert result.status == AuthStatus.AUTHENTICATED
            assert result.message == "Token is valid"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_token_validation_failure(self, auth_config):
        """Test failed token validation."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.validate_token("invalid_token")

            assert result.success is False
            assert result.user is None
            assert result.token is None
            assert result.status == AuthStatus.INVALID
            assert result.message == "Invalid token"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_token_refresh_success(self, auth_config):
        """Test successful token refresh."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.refresh_token("valid_refresh_token")

            assert result.success is True
            assert result.user is not None
            assert result.token is not None
            assert result.status == AuthStatus.AUTHENTICATED
            assert result.message == "Token refreshed successfully"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_token_refresh_failure(self, auth_config):
        """Test failed token refresh."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            result = await provider.refresh_token("invalid_refresh_token")

            assert result.success is False
            assert result.user is None
            assert result.token is None
            assert result.status == AuthStatus.INVALID
            assert result.message == "Invalid refresh token"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_token_revocation(self, auth_config):
        """Test token revocation."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            # Test successful revocation
            success = await provider.revoke_token("valid_token")
            assert success is True

            # Test failed revocation
            success = await provider.revoke_token("invalid_token")
            assert success is False

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_permission_check(self, auth_config):
        """Test permission checking."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            # Test successful permission check
            has_permission = await provider.check_permission("user_1", Permission.READ)
            assert has_permission is True

            has_permission = await provider.check_permission("user_1", Permission.WRITE)
            assert has_permission is True

            # Test failed permission check
            has_permission = await provider.check_permission("user_1", Permission.ADMIN)
            assert has_permission is False

            has_permission = await provider.check_permission("user_2", Permission.READ)
            assert has_permission is False

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_health_check(self, auth_config):
        """Test provider health check."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            is_healthy = await provider.health_check()
            assert is_healthy is True

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_stats(self, auth_config):
        """Test provider statistics."""
        provider = MockAuthProvider(auth_config)
        await provider.initialize()

        try:
            stats = provider.get_stats()

            assert "uptime_seconds" in stats
            assert "total_authentications" in stats
            assert "error_count" in stats
            assert "success_rate" in stats
            assert "cached_users" in stats
            assert "cached_tokens" in stats
            assert "initialized" in stats
            assert stats["initialized"] is True
            assert stats["total_authentications"] == 0
            assert stats["error_count"] == 0

        finally:
            await provider.shutdown()


class TestJWTProvider:
    """Test JWT authentication provider functionality."""

    @pytest.mark.asyncio
    async def test_jwt_provider_initialization(self, jwt_config):
        """Test JWT provider initialization."""
        provider = JWTProvider(jwt_config)
        await provider.initialize()

        assert provider._initialized
        assert provider.jwt_config.token_secret is not None
        assert len(provider.jwt_config.roles) > 0
        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_jwt_provider_create_user(self, jwt_config):
        """Test JWT provider user creation."""
        provider = JWTProvider(jwt_config)
        await provider.initialize()

        try:
            user = await provider.create_user(
                username="newuser",
                password="newpass123",
                email="newuser@example.com",
                first_name="New",
                last_name="User",
            )

            assert user.username == "newuser"
            assert user.email == "newuser@example.com"
            assert user.first_name == "New"
            assert user.last_name == "User"
            assert user.is_active is True
            assert user.is_verified is False

            # Verify user was stored
            assert user.id in provider.jwt_config.users

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_jwt_provider_authentication(self, jwt_config):
        """Test JWT provider authentication."""
        provider = JWTProvider(jwt_config)
        await provider.initialize()

        try:
            # Create a user first
            user = await provider.create_user(
                username="testuser",
                password="testpass123",
                email="testuser@example.com",
            )

            # Test successful authentication
            result = await provider.authenticate(
                {
                    "username": "testuser",
                    "password": "testpass123",
                }
            )

            assert result.success is True
            assert result.user is not None
            assert result.user.username == "testuser"
            assert result.token is not None
            assert result.token.access_token is not None
            assert result.token.refresh_token is not None
            assert result.status == AuthStatus.AUTHENTICATED

            # Test failed authentication
            result = await provider.authenticate(
                {
                    "username": "testuser",
                    "password": "wrongpass",
                }
            )

            assert result.success is False
            assert result.status == AuthStatus.UNAUTHENTICATED

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_jwt_provider_token_validation(self, jwt_config):
        """Test JWT provider token validation."""
        provider = JWTProvider(jwt_config)
        await provider.initialize()

        try:
            # Create a user and get a token
            user = await provider.create_user(
                username="testuser",
                password="testpass123",
            )

            auth_result = await provider.authenticate(
                {
                    "username": "testuser",
                    "password": "testpass123",
                }
            )

            token = auth_result.token.access_token

            # Test successful token validation
            result = await provider.validate_token(token)
            assert result.success is True
            assert result.user is not None
            assert result.status == AuthStatus.AUTHENTICATED

            # Test failed token validation
            result = await provider.validate_token("invalid_token")
            assert result.success is False
            assert result.status == AuthStatus.INVALID

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_jwt_provider_role_assignment(self, jwt_config):
        """Test JWT provider role assignment."""
        provider = JWTProvider(jwt_config)
        await provider.initialize()

        try:
            # Create a user
            user = await provider.create_user(
                username="testuser",
                password="testpass123",
            )

            # Assign a role
            success = await provider.assign_role(user.id, "user")
            assert success is True

            # Test permission check
            has_permission = await provider.check_permission(user.id, Permission.READ)
            assert has_permission is True

            has_permission = await provider.check_permission(user.id, Permission.ADMIN)
            assert has_permission is False

        finally:
            await provider.shutdown()


class TestAuthExceptions:
    """Test authentication exception classes."""

    def test_auth_error_inheritance(self):
        """Test auth error inheritance."""
        error = AuthError("Test error")
        assert isinstance(error, AuthError)
        assert isinstance(error, ComponentError)
        assert str(error) == "Test error"

    def test_authentication_error_inheritance(self):
        """Test authentication error inheritance."""
        error = AuthenticationError("Authentication error")
        assert isinstance(error, AuthError)
        assert str(error) == "Authentication error"

    def test_authorization_error_inheritance(self):
        """Test authorization error inheritance."""
        error = AuthorizationError("Authorization error")
        assert isinstance(error, AuthError)
        assert str(error) == "Authorization error"

    def test_token_error_inheritance(self):
        """Test token error inheritance."""
        error = TokenError("Token error")
        assert isinstance(error, AuthError)
        assert str(error) == "Token error"

    def test_provider_error_inheritance(self):
        """Test provider error inheritance."""
        error = ProviderError("Provider error")
        assert isinstance(error, AuthError)
        assert str(error) == "Provider error"


class TestAuthEnums:
    """Test authentication enumerations."""

    def test_auth_type_values(self):
        """Test auth type values."""
        assert AuthType.JWT.value == "jwt"
        assert AuthType.OAUTH2.value == "oauth2"
        assert AuthType.API_KEY.value == "api_key"
        assert AuthType.SESSION.value == "session"
        assert AuthType.LDAP.value == "ldap"
        assert AuthType.SAML.value == "saml"
        assert AuthType.OPENID_CONNECT.value == "openid_connect"

    def test_permission_values(self):
        """Test permission values."""
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.DELETE.value == "delete"
        assert Permission.ADMIN.value == "admin"
        assert Permission.EXECUTE.value == "execute"

    def test_auth_status_values(self):
        """Test auth status values."""
        assert AuthStatus.AUTHENTICATED.value == "authenticated"
        assert AuthStatus.UNAUTHENTICATED.value == "unauthenticated"
        assert AuthStatus.EXPIRED.value == "expired"
        assert AuthStatus.INVALID.value == "invalid"
        assert AuthStatus.LOCKED.value == "locked"
