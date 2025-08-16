"""
Secret management and configuration.

Provides secure secret storage, environment-based secrets, and
secret rotation capabilities for sensitive configuration data.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from opsvi_foundation.patterns import ComponentError


class SecretError(ComponentError):
    """Raised when secret operation fails."""


class SecretSource(Enum):
    """Secret sources."""

    ENVIRONMENT = "environment"
    FILE = "file"
    VAULT = "vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    AZURE_KEY_VAULT = "azure_key_vault"
    GOOGLE_SECRET_MANAGER = "google_secret_manager"


@dataclass
class SecretConfig:
    """Secret configuration."""

    name: str
    source: SecretSource
    key: str
    default_value: str | None = None
    required: bool = True
    encrypted: bool = False
    rotation_interval: int | None = None  # days
    last_rotation: float | None = None


class SecretManager:
    """Manages secrets from various sources."""

    def __init__(self):
        """Initialize secret manager."""
        self.secrets: dict[str, SecretConfig] = {}
        self.cache: dict[str, str] = {}
        self._encryption_key: bytes | None = None

    def add_secret(self, config: SecretConfig) -> None:
        """
        Add secret configuration.

        Args:
            config: Secret configuration
        """
        self.secrets[config.name] = config

    def remove_secret(self, name: str) -> None:
        """
        Remove secret configuration.

        Args:
            name: Secret name
        """
        self.secrets.pop(name, None)
        self.cache.pop(name, None)

    def get_secret(self, name: str, refresh: bool = False) -> str | None:
        """
        Get secret value.

        Args:
            name: Secret name
            refresh: Whether to refresh from source

        Returns:
            Secret value or None if not found
        """
        if name not in self.secrets:
            raise SecretError(f"Secret '{name}' not configured")

        if not refresh and name in self.cache:
            return self.cache[name]

        config = self.secrets[name]
        value = self._load_secret(config)

        if value is None and config.required:
            raise SecretError(f"Required secret '{name}' not found")

        if value is not None:
            self.cache[name] = value

        return value

    def _load_secret(self, config: SecretConfig) -> str | None:
        """
        Load secret from source.

        Args:
            config: Secret configuration

        Returns:
            Secret value or None if not found
        """
        if config.source == SecretSource.ENVIRONMENT:
            return self._load_from_environment(config)
        if config.source == SecretSource.FILE:
            return self._load_from_file(config)
        if config.source == SecretSource.VAULT:
            return self._load_from_vault(config)
        if config.source == SecretSource.AWS_SECRETS_MANAGER:
            return self._load_from_aws_secrets_manager(config)
        if config.source == SecretSource.AZURE_KEY_VAULT:
            return self._load_from_azure_key_vault(config)
        if config.source == SecretSource.GOOGLE_SECRET_MANAGER:
            return self._load_from_google_secret_manager(config)
        raise SecretError(f"Unsupported secret source: {config.source}")

    def _load_from_environment(self, config: SecretConfig) -> str | None:
        """Load secret from environment variable."""
        value = os.getenv(config.key)
        if value and config.encrypted:
            return self._decrypt_value(value)
        return value

    def _load_from_file(self, config: SecretConfig) -> str | None:
        """Load secret from file."""
        try:
            file_path = Path(config.key)
            if file_path.exists():
                value = file_path.read_text().strip()
                if config.encrypted:
                    return self._decrypt_value(value)
                return value
        except Exception as e:
            print(f"Failed to load secret from file {config.key}: {e}")
        return None

    def _load_from_vault(self, config: SecretConfig) -> str | None:
        """Load secret from HashiCorp Vault."""
        try:
            # In a real implementation, this would use the hvac library
            # to connect to HashiCorp Vault
            import hvac

            # Placeholder implementation
            vault_url = os.getenv("VAULT_URL")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_url or not vault_token:
                return None

            client = hvac.Client(url=vault_url, token=vault_token)

            # Parse key as path:field
            if ":" in config.key:
                path, field = config.key.split(":", 1)
            else:
                path = config.key
                field = "value"

            response = client.secrets.kv.v2.read_secret_version(path=path)
            if response and "data" in response and "data" in response["data"]:
                value = response["data"]["data"].get(field)
                if value and config.encrypted:
                    return self._decrypt_value(value)
                return value
        except Exception as e:
            print(f"Failed to load secret from Vault {config.key}: {e}")
        return None

    def _load_from_aws_secrets_manager(self, config: SecretConfig) -> str | None:
        """Load secret from AWS Secrets Manager."""
        try:
            import boto3

            # Parse key as secret_name:field
            if ":" in config.key:
                secret_name, field = config.key.split(":", 1)
            else:
                secret_name = config.key
                field = None

            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                secret_data = json.loads(response["SecretString"])
                if field:
                    value = secret_data.get(field)
                else:
                    value = secret_data

                if value and config.encrypted:
                    return self._decrypt_value(value)
                return value
        except Exception as e:
            print(f"Failed to load secret from AWS Secrets Manager {config.key}: {e}")
        return None

    def _load_from_azure_key_vault(self, config: SecretConfig) -> str | None:
        """Load secret from Azure Key Vault."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            # Parse key as vault_url:secret_name
            if ":" in config.key:
                vault_url, secret_name = config.key.split(":", 1)
            else:
                vault_url = os.getenv("AZURE_KEY_VAULT_URL")
                secret_name = config.key

            if not vault_url:
                return None

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            response = client.get_secret(secret_name)
            value = response.value

            if value and config.encrypted:
                return self._decrypt_value(value)
            return value
        except Exception as e:
            print(f"Failed to load secret from Azure Key Vault {config.key}: {e}")
        return None

    def _load_from_google_secret_manager(self, config: SecretConfig) -> str | None:
        """Load secret from Google Secret Manager."""
        try:
            from google.cloud import secretmanager

            # Parse key as project_id:secret_id
            if ":" in config.key:
                project_id, secret_id = config.key.split(":", 1)
            else:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
                secret_id = config.key

            if not project_id:
                return None

            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

            response = client.access_secret_version(request={"name": name})
            value = response.payload.data.decode("UTF-8")

            if value and config.encrypted:
                return self._decrypt_value(value)
            return value
        except Exception as e:
            print(f"Failed to load secret from Google Secret Manager {config.key}: {e}")
        return None

    def set_encryption_key(self, key: str | bytes) -> None:
        """
        Set encryption key for decrypting secrets.

        Args:
            key: Encryption key
        """
        if isinstance(key, str):
            self._encryption_key = key.encode("utf-8")
        else:
            self._encryption_key = key

    def _decrypt_value(self, encrypted_value: str) -> str | None:
        """
        Decrypt a value.

        Args:
            encrypted_value: Encrypted value

        Returns:
            Decrypted value or None if decryption fails
        """
        if not self._encryption_key:
            raise SecretError("Encryption key not set")

        try:
            # Simple base64 + XOR decryption for demonstration
            # In production, use proper encryption like AES
            decoded = base64.b64decode(encrypted_value)
            decrypted = bytes(
                a ^ b for a, b in zip(decoded, self._encryption_key, strict=False)
            )
            return decrypted.decode("utf-8")
        except Exception as e:
            print(f"Failed to decrypt value: {e}")
            return None

    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a value.

        Args:
            value: Value to encrypt

        Returns:
            Encrypted value
        """
        if not self._encryption_key:
            raise SecretError("Encryption key not set")

        # Simple base64 + XOR encryption for demonstration
        # In production, use proper encryption like AES
        value_bytes = value.encode("utf-8")
        encrypted = bytes(
            a ^ b for a, b in zip(value_bytes, self._encryption_key, strict=False)
        )
        return base64.b64encode(encrypted).decode("utf-8")

    def refresh_secrets(self) -> None:
        """Refresh all secrets from their sources."""
        self.cache.clear()
        for name in self.secrets:
            self.get_secret(name, refresh=True)

    def get_secret_hash(self, name: str) -> str | None:
        """
        Get hash of secret value for comparison.

        Args:
            name: Secret name

        Returns:
            Hash of secret value or None if not found
        """
        value = self.get_secret(name)
        if value:
            return hashlib.sha256(value.encode("utf-8")).hexdigest()
        return None

    def validate_secrets(self) -> dict[str, bool]:
        """
        Validate all configured secrets.

        Returns:
            Dictionary mapping secret names to validation status
        """
        results = {}
        for name, config in self.secrets.items():
            try:
                value = self.get_secret(name)
                results[name] = value is not None or not config.required
            except Exception:
                results[name] = False
        return results


class SecretRotator:
    """Handles secret rotation."""

    def __init__(self, secret_manager: SecretManager):
        """
        Initialize secret rotator.

        Args:
            secret_manager: Secret manager instance
        """
        self.secret_manager = secret_manager
        self.rotation_history: dict[str, list] = {}

    def should_rotate(self, secret_name: str) -> bool:
        """
        Check if secret should be rotated.

        Args:
            secret_name: Secret name

        Returns:
            True if secret should be rotated
        """
        if secret_name not in self.secret_manager.secrets:
            return False

        config = self.secret_manager.secrets[secret_name]
        if not config.rotation_interval:
            return False

        import time

        current_time = time.time()
        last_rotation = config.last_rotation or 0

        # Convert days to seconds
        rotation_interval_seconds = config.rotation_interval * 24 * 60 * 60

        return current_time - last_rotation > rotation_interval_seconds

    def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Rotate a secret.

        Args:
            secret_name: Secret name
            new_value: New secret value

        Returns:
            True if rotation successful
        """
        if secret_name not in self.secret_manager.secrets:
            return False

        config = self.secret_manager.secrets[secret_name]

        try:
            # Update the secret value
            if config.source == SecretSource.ENVIRONMENT:
                # For environment variables, we can't update them at runtime
                # In a real implementation, this would trigger a restart or use a different mechanism
                print(
                    f"Warning: Cannot rotate environment variable {config.key} at runtime",
                )
                return False
            if config.source == SecretSource.FILE:
                # Update file
                file_path = Path(config.key)
                file_path.write_text(new_value)
            else:
                # For other sources, we would update the secret in the service
                print(
                    f"Warning: Secret rotation not implemented for source {config.source}",
                )
                return False

            # Update cache
            self.secret_manager.cache[secret_name] = new_value

            # Update rotation timestamp
            import time

            config.last_rotation = time.time()

            # Record rotation
            if secret_name not in self.rotation_history:
                self.rotation_history[secret_name] = []

            self.rotation_history[secret_name].append(
                {"timestamp": config.last_rotation, "source": config.source.value},
            )

            return True
        except Exception as e:
            print(f"Failed to rotate secret {secret_name}: {e}")
            return False

    def get_rotation_history(self, secret_name: str) -> list:
        """
        Get rotation history for a secret.

        Args:
            secret_name: Secret name

        Returns:
            List of rotation records
        """
        return self.rotation_history.get(secret_name, [])


# Global secret manager
secret_manager = SecretManager()


def secret(name: str, source: SecretSource, key: str, **kwargs):
    """
    Decorator for accessing secrets.

    Args:
        name: Secret name
        source: Secret source
        key: Secret key
        **kwargs: Additional configuration
    """

    def decorator(func):
        config = SecretConfig(name=name, source=source, key=key, **kwargs)
        secret_manager.add_secret(config)

        def wrapper(*args, **kwargs):
            secret_value = secret_manager.get_secret(name)
            # Inject secret value as first argument
            return func(secret_value, *args, **kwargs)

        return wrapper

    return decorator


def require_secret(name: str):
    """
    Decorator to require a secret for function execution.

    Args:
        name: Secret name
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            secret_value = secret_manager.get_secret(name)
            if not secret_value:
                raise SecretError(f"Required secret '{name}' not available")
            return func(*args, **kwargs)

        return wrapper

    return decorator
