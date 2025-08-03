"""
Security utilities for the ACCF Research Agent.

This module provides security-related utilities including secrets management.
"""

import os
import logging
from typing import Optional
from ..core.settings import Settings

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secrets and sensitive configuration."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._secrets_cache: dict = {}

    def get_secret(
        self, secret_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get a secret value from environment or AWS Secrets Manager."""

        # First check environment variables
        env_var = f"ACCF_{secret_name.upper()}"
        if env_var in os.environ:
            return os.environ[env_var]

        # Check cache
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]

        # Try AWS Secrets Manager if enabled
        if self.settings.aws_secrets_manager_enabled:
            try:
                import boto3

                client = boto3.client(
                    "secretsmanager", region_name=self.settings.aws_region
                )
                response = client.get_secret_value(SecretId=secret_name)
                secret_value = response["SecretString"]
                self._secrets_cache[secret_name] = secret_value
                return secret_value
            except Exception as e:
                logger.warning(f"Failed to get secret {secret_name} from AWS: {e}")

        return default

    def set_secret(self, secret_name: str, value: str) -> None:
        """Set a secret value in the cache."""
        self._secrets_cache[secret_name] = value

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._secrets_cache.clear()


def validate_api_key(api_key: str) -> bool:
    """Validate an API key format."""
    if not api_key:
        return False

    # Basic validation - check if it looks like a valid API key
    if len(api_key) < 10:
        return False

    # Add more specific validation as needed
    return True


def sanitize_log_message(message: str) -> str:
    """Sanitize a log message to remove sensitive information."""
    # Remove potential API keys, passwords, etc.
    import re

    # Replace API keys (common patterns)
    message = re.sub(r"sk-[a-zA-Z0-9]{20,}", "sk-***", message)
    message = re.sub(r"pk-[a-zA-Z0-9]{20,}", "pk-***", message)

    # Replace passwords
    message = re.sub(
        r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?', "password=***", message
    )

    return message
