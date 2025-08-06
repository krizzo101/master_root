"""
Configuration management for OPSVI Core Library.

Provides type-safe configuration using Pydantic V2 with environment variable support.
"""

import logging

from pydantic import Field
from pydantic_settings import BaseSettings

from .exceptions import ConfigurationError


class AppConfig(BaseSettings):
    """
    Application configuration schema with environment variable support.

    Attributes:
        app_name: Name of the application
        environment: Execution environment (development, staging, production)
        debug: Enable debug mode
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        database_url: Database connection URL (optional)
    """

    app_name: str = Field("opsvi", description="Name of the application")
    environment: str = Field("development", description="Execution environment")
    debug: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("INFO", description="Logging level")
    database_url: str | None = Field(None, description="Database connection URL")

    class Config:
        env_prefix = "OPSVI_"
        env_file = ".env"
        case_sensitive = False


def load_config() -> AppConfig:
    """
    Loads application configuration with validation and environment variable support.

    Returns:
        AppConfig: Validated configuration object

    Raises:
        ConfigurationError: If configuration loading fails
    """
    try:
        config = AppConfig()
        return config
    except Exception as e:
        logging.exception("Failed to load configuration: %s", e)
        raise ConfigurationError(f"Configuration loading failed: {e}") from e


# Instantiate configuration at module load
config = load_config()
