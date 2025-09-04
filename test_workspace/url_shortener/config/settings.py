"""Configuration settings for URL shortener service."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_name: str = Field(default="URL Shortener", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # Database settings
    database_url: str = Field(default="url_shortener.db", env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DB_POOL_SIZE")

    # URL shortener settings
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    min_code_length: int = Field(default=6, env="MIN_CODE_LENGTH")
    max_url_length: int = Field(default=2048, env="MAX_URL_LENGTH")
    default_expiry_days: Optional[int] = Field(default=None, env="DEFAULT_EXPIRY_DAYS")

    # Security settings
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    enable_api_key: bool = Field(default=False, env="ENABLE_API_KEY")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # Cache settings
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # seconds

    # Maintenance settings
    cleanup_interval: int = Field(default=3600, env="CLEANUP_INTERVAL")  # seconds
    enable_auto_cleanup: bool = Field(default=True, env="ENABLE_AUTO_CLEANUP")

    @validator("base_url")
    def validate_base_url(cls, v):
        """Ensure base_url doesn't end with a slash."""
        return v.rstrip("/")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance.
    """
    return Settings()


# Create settings instance
settings = get_settings()
