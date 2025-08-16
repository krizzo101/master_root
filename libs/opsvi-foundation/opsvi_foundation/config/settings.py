"""Configuration settings for opsvi-foundation.

Comprehensive configuration management for the OPSVI ecosystem
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from ..core.base import BaseSettings as BaseComponentSettings


class LibraryConfig(BaseComponentSettings):
    """Configuration for OPSVI libraries."""

    # Core configuration
    enabled: bool = Field(default=True, description="Whether the library is enabled")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Library-specific configuration
    library_name: str = Field(description="Name of the library")
    version: str = Field(description="Library version")

    class Config:
        env_prefix = "OPSVI_LIBRARY_"


class LibrarySettings(BaseSettings):
    """Global library settings."""

    # Environment configuration
    environment: str = Field(default="production", description="Environment name")
    instance_id: str = Field(default="default", description="Instance identifier")

    # Logging configuration
    log_format: str = Field(default="json", description="Log format (json, text)")
    log_file: Optional[str] = Field(default=None, description="Log file path")

    # Performance configuration
    max_workers: int = Field(default=10, description="Maximum number of workers")
    timeout: float = Field(default=30.0, description="Default timeout in seconds")

    # Security configuration
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    secrets_backend: str = Field(default="env", description="Secrets backend type")

    class Config:
        env_prefix = "OPSVI_"
        case_sensitive = False


class FoundationConfig(BaseComponentSettings):
    """Configuration for opsvi-foundation library."""

    # Foundation-specific settings
    enable_utilities: bool = Field(default=True, description="Enable utility functions")
    enable_retry: bool = Field(default=True, description="Enable retry mechanisms")
    enable_backoff: bool = Field(default=True, description="Enable backoff strategies")

    # Retry configuration
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Initial retry delay in seconds"
    )
    backoff_factor: float = Field(
        default=2.0, description="Backoff multiplication factor"
    )

    class Config:
        env_prefix = "OPSVI_FOUNDATION_"
