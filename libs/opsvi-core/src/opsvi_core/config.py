"""OPSVI Core Configuration Management."""

import os
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

from .exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class Config(BaseModel):
    """Base configuration class for OPSVI applications."""

    app_name: str = Field(..., description="Application name")
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "OPSVI_"
        case_sensitive = False


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_class: type[Config] = Config):
        self.config_class = config_class
        self._config: Config | None = None
        self._env_file: Path | None = None

    def load_from_env(self, env_file: Path | None = None) -> Config:
        """Load configuration from environment variables and optional .env file."""
        if env_file and env_file.exists():
            self._env_file = env_file
            self._load_env_file(env_file)

        try:
            self._config = self.config_class()
            logger.info(
                "Configuration loaded successfully",
                app_name=self._config.app_name,
                environment=self._config.environment,
            )
            return self._config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _load_env_file(self, env_file: Path) -> None:
        """Load environment variables from .env file."""
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            logger.info("Environment file loaded", file=str(env_file))
        except Exception as e:
            logger.warning(
                "Failed to load environment file", file=str(env_file), error=str(e)
            )

    @property
    def config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            raise ConfigurationError(
                "Configuration not loaded. Call load_from_env() first."
            )
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self.config, key, default)
