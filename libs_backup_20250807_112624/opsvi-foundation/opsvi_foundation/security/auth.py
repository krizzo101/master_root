"""
Authentication and authorization utilities.

Provides JWT validation, API key management, and authentication helpers.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import jwt
from cryptography.fernet import Fernet
from pydantic import BaseModel


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

        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
        )

    def validate_jwt(self, token: str) -> TokenPayload:
        """Validate and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
            )
            return TokenPayload(
                user_id=payload["user_id"],
                email=payload["email"],
                roles=payload["roles"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    def generate_api_key(self, prefix: str = "opsvi") -> str:
        """Generate a secure API key."""
        key = secrets.token_urlsafe(self.config.api_key_length)
        return f"{prefix}_{key}"

    def hash_api_key(self, api_key: str, salt: str | None = None) -> tuple[str, str]:
        """Hash an API key for secure storage."""
        if salt is None:
            salt = secrets.token_hex(16)

        key_hash = hashlib.pbkdf2_hmac(
            "sha256",
            api_key.encode(),
            salt.encode(),
            100000,
        )
        return key_hash.hex(), salt

    def verify_api_key(self, api_key: str, stored_hash: str, salt: str) -> bool:
        """Verify an API key against its stored hash."""
        key_hash, _ = self.hash_api_key(api_key, salt)
        return hmac.compare_digest(key_hash, stored_hash)

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._cipher:
            raise ValueError("Encryption key not configured")

        encrypted = self._cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._cipher:
            raise ValueError("Encryption key not configured")

        decrypted = self._cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if len(data) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "(", ")", "|", "`"]
    sanitized = data
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    return sanitized.strip()
