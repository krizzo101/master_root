"""
Authentication and authorization utilities for opsvi-core.

Provides JWT validation, API key management, and authentication helpers.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import jwt
from cryptography.fernet import Fernet
from pydantic import BaseModel

from ..core.exceptions import AuthenticationError, AuthorizationError
from ..core.logging import get_logger

logger = get_logger(__name__)


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    api_key_length: int = 32
    encryption_key: str | None = None


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    user_id: str
    email: str
    roles: list[str]
    exp: datetime
    iat: datetime


class AuthManager:
    """Centralized authentication and authorization manager."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self._cipher = None
        if config.encryption_key:
            self._cipher = Fernet(config.encryption_key.encode())

        logger.info("AuthManager initialized")

    def generate_jwt(self, user_id: str, email: str, roles: list[str]) -> str:
        """Generate a JWT token for the user."""
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "email": email,
            "roles": roles,
            "iat": now,
            "exp": now + timedelta(hours=self.config.jwt_expiry_hours),
        }

        try:
            token = jwt.encode(
                payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm
            )
            logger.info("JWT generated", user_id=user_id)
            return token
        except Exception as e:
            logger.error("Failed to generate JWT", error=str(e))
            raise AuthenticationError(f"Failed to generate token: {e}") from e

    def validate_jwt(self, token: str) -> TokenPayload:
        """Validate and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
            token_payload = TokenPayload(
                user_id=payload["user_id"],
                email=payload["email"],
                roles=payload["roles"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
            )
            logger.debug("JWT validated", user_id=token_payload.user_id)
            return token_payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired") from None
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e

    def generate_api_key(self, prefix: str = "opsvi") -> str:
        """Generate a secure API key."""
        key = secrets.token_urlsafe(self.config.api_key_length)
        api_key = f"{prefix}_{key}"
        logger.info("API key generated", prefix=prefix)
        return api_key

    def hash_api_key(self, api_key: str, salt: str | None = None) -> tuple[str, str]:
        """Hash an API key for secure storage."""
        if salt is None:
            salt = secrets.token_hex(16)

        key_hash = hashlib.pbkdf2_hmac(
            "sha256", api_key.encode(), salt.encode(), 100000
        )
        return key_hash.hex(), salt

    def verify_api_key(self, api_key: str, stored_hash: str, salt: str) -> bool:
        """Verify an API key against its stored hash."""
        key_hash, _ = self.hash_api_key(api_key, salt)
        return hmac.compare_digest(key_hash, stored_hash)

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._cipher:
            raise AuthenticationError("Encryption key not configured")

        encrypted = self._cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._cipher:
            raise AuthenticationError("Encryption key not configured")

        try:
            decrypted = self._cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise AuthenticationError(f"Failed to decrypt data: {e}") from e

    def check_permission(self, user_roles: list[str], required_role: str) -> bool:
        """Check if user has required permission."""
        has_permission = required_role in user_roles or "admin" in user_roles
        logger.debug(
            "Permission check",
            required_role=required_role,
            has_permission=has_permission,
        )
        return has_permission

    def require_permission(self, user_roles: list[str], required_role: str) -> None:
        """Require user to have specific permission or raise exception."""
        if not self.check_permission(user_roles, required_role):
            raise AuthorizationError(
                f"Required role '{required_role}' not found in user roles"
            )


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if len(data) > max_length:
        raise AuthenticationError(f"Input exceeds maximum length of {max_length}")

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "(", ")", "|", "`"]
    sanitized = data
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    return sanitized.strip()
