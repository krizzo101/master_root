"""
Advanced encryption utilities.

Provides AES encryption, key derivation, and secure random generation.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from pydantic import BaseModel

from ..observability import get_logger

logger = get_logger(__name__)


class EncryptionConfig(BaseModel):
    """Configuration for encryption operations."""
    key_length: int = 32
    salt_length: int = 16
    iterations: int = 100000
    algorithm: str = "PBKDF2HMAC"


class AdvancedEncryption:
    """Advanced encryption utilities with AES and RSA support."""

    def __init__(self, config: EncryptionConfig | None = None):
        self.config = config or EncryptionConfig()
        logger.debug("Initialized AdvancedEncryption", config=self.config.model_dump())

    def generate_key(self, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """Generate encryption key from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Optional salt, generated if not provided

        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(self.config.salt_length)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_length,
            salt=salt,
            iterations=self.config.iterations,
        )

        key = kdf.derive(password.encode())
        logger.debug("Generated encryption key", salt_length=len(salt))
        return key, salt

    def encrypt_data(self, data: str | bytes, key: bytes) -> str:
        """Encrypt data using Fernet symmetric encryption.

        Args:
            data: Data to encrypt
            key: Encryption key

        Returns:
            Base64 encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode()

        # Use first 32 bytes for Fernet key
        fernet_key = base64.urlsafe_b64encode(key[:32])
        fernet = Fernet(fernet_key)

        encrypted = fernet.encrypt(data)
        encoded = base64.b64encode(encrypted).decode()

        logger.debug("Encrypted data", data_length=len(data))
        return encoded

    def decrypt_data(self, encrypted_data: str, key: bytes) -> bytes:
        """Decrypt data using Fernet symmetric encryption.

        Args:
            encrypted_data: Base64 encoded encrypted data
            key: Encryption key

        Returns:
            Decrypted data as bytes

        Raises:
            ValueError: If decryption fails
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())

            # Use first 32 bytes for Fernet key
            fernet_key = base64.urlsafe_b64encode(key[:32])
            fernet = Fernet(fernet_key)

            decrypted = fernet.decrypt(encrypted_bytes)
            logger.debug("Decrypted data", data_length=len(decrypted))
            return decrypted

        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise ValueError(f"Decryption failed: {e}")

    def generate_rsa_keypair(self, key_size: int = 2048) -> tuple[bytes, bytes]:
        """Generate RSA public/private key pair.

        Args:
            key_size: RSA key size in bits

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        logger.debug("Generated RSA keypair", key_size=key_size)
        return private_pem, public_pem


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        URL-safe base64 encoded token
    """
    token = secrets.token_urlsafe(length)
    logger.debug("Generated secure token", length=length)
    return token


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Hash password using PBKDF2 with SHA-256.

    Args:
        password: Password to hash
        salt: Optional salt, generated if not provided

    Returns:
        Tuple of (hash_hex, salt_hex)
    """
    if salt is None:
        salt = os.urandom(16)

    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

    logger.debug("Hashed password", salt_length=len(salt))
    return pwd_hash.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Verify password against stored hash.

    Args:
        password: Password to verify
        hash_hex: Stored password hash (hex)
        salt_hex: Stored salt (hex)

    Returns:
        True if password matches
    """
    try:
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)

        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

        result = secrets.compare_digest(pwd_hash, stored_hash)
        logger.debug("Password verification", result=result)
        return result

    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False
