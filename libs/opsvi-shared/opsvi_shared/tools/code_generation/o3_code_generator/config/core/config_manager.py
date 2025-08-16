"""
Configuration management for the O3 Code Generator.

This module provides centralized configuration management with support for
environment variable overrides and YAML file configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class ConfigManager:
    """
    Configuration manager with env var overrides and YAML fallback.

    Priority order:
    1. Environment variables
    2. YAML configuration file
    3. Hardcoded defaults
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration manager."""
        self.logger = get_logger()
        self.config_path = (
            Path(config_path) if config_path else Path(__file__).parent / "config.yaml"
        )
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config_data = yaml.safe_load(f) or {}
                self.logger.log_debug(f"Loaded config from {self.config_path}")
            else:
                self.logger.log_warning(f"Config file not found: {self.config_path}")
                self._config_data = {}
        except Exception as e:
            self.logger.log_error(f"Failed to load config: {e}")
            self._config_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with env var override.

        Args:
            key: Configuration key (supports dot notation like 'openai.api_key')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Check environment variable first (convert dot notation to uppercase with underscores)
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Check YAML config with dot notation support
        try:
            value = self._config_data
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            pass

        # Return default
        return default

    def get_api_key(self) -> str:
        """Get OpenAI API key from env or config."""
        api_key = self.get("openai.api_key") or self.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment or config")
        return api_key

    def get_api_base_url(self) -> Optional[str]:
        """Get OpenAI API base URL."""
        return self.get("openai.base_url") or self.get("OPENAI_BASE_URL")

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration with defaults."""
        return {
            "level": self.get("logging.level", "INFO"),
            "format": self.get(
                "logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            "enable_debug_log": self.get("logging.enable_debug_log", False),
        }

    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration with defaults."""
        return {
            "default_model": self.get("model.default", "gpt-4o-mini"),
            "timeout": self.get("model.timeout", 30),
            "max_retries": self.get("model.max_retries", 3),
        }
