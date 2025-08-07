"""
Configuration management.

Handles environment-based configuration with validation and defaults.
"""

import os

from pydantic import BaseModel, Field


class FoundationConfig(BaseModel):
    """Foundation configuration settings."""

    # Environment settings
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security settings
    jwt_secret: str = Field(default="dev-secret", description="JWT signing secret")
    encryption_key: str | None = Field(
        default=None,
        description="Encryption key for sensitive data",
    )
    api_timeout: int = Field(default=30, description="Default API timeout in seconds")
    max_retries: int = Field(default=3, description="Default maximum retry attempts")

    # Circuit breaker settings
    circuit_failure_threshold: int = Field(
        default=5,
        description="Circuit breaker failure threshold",
    )
    circuit_recovery_timeout: int = Field(
        default=60,
        description="Circuit breaker recovery timeout",
    )

    @classmethod
    def from_env(cls) -> "FoundationConfig":
        """Create configuration from environment variables."""
        try:
            return cls(
                environment=os.getenv("OPSVI_ENVIRONMENT", "development"),
                debug=os.getenv("OPSVI_DEBUG", "false").lower() == "true",
                log_level=os.getenv("OPSVI_LOG_LEVEL", "INFO").upper(),
                jwt_secret=os.getenv("OPSVI_JWT_SECRET", "dev-secret"),
                encryption_key=os.getenv("OPSVI_ENCRYPTION_KEY"),
                api_timeout=int(os.getenv("OPSVI_API_TIMEOUT", "30")),
                max_retries=int(os.getenv("OPSVI_MAX_RETRIES", "3")),
                circuit_failure_threshold=int(
                    os.getenv("OPSVI_CIRCUIT_FAILURE_THRESHOLD", "5"),
                ),
                circuit_recovery_timeout=int(
                    os.getenv("OPSVI_CIRCUIT_RECOVERY_TIMEOUT", "60"),
                ),
            )
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.environment not in ["development", "staging", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")


# Global configuration instance
config = FoundationConfig.from_env()
