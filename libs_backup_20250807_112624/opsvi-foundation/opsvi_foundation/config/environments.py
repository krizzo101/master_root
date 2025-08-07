"""
Environment-specific configuration management.

Provides dev/staging/prod configs, environment detection, and
environment-specific configuration loading.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from opsvi_foundation.patterns import ComponentError


class EnvironmentError(ComponentError):
    """Raised when environment configuration fails."""


class Environment(Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""

    name: str
    environment: Environment
    debug: bool = False
    log_level: str = "INFO"
    database_url: str | None = None
    redis_url: str | None = None
    api_keys: dict[str, str] = field(default_factory=dict)
    feature_flags: dict[str, bool] = field(default_factory=dict)
    custom_settings: dict[str, Any] = field(default_factory=dict)


class EnvironmentDetector:
    """Detects and manages environment configuration."""

    def __init__(self):
        """Initialize environment detector."""
        self._current_environment: Environment | None = None
        self._config_cache: dict[str, EnvironmentConfig] = {}

    def detect_environment(self) -> Environment:
        """
        Detect current environment.

        Returns:
            Current environment
        """
        if self._current_environment:
            return self._current_environment

        # Check environment variables
        env_var = os.getenv("OPSVI_ENVIRONMENT", "").lower()

        if env_var in ["dev", "development"]:
            self._current_environment = Environment.DEVELOPMENT
        elif env_var in ["staging", "stage"]:
            self._current_environment = Environment.STAGING
        elif env_var in ["prod", "production"]:
            self._current_environment = Environment.PRODUCTION
        elif env_var in ["test", "testing"]:
            self._current_environment = Environment.TESTING
        else:
            # Auto-detect based on common patterns
            hostname = os.getenv("HOSTNAME", "").lower()
            if any(word in hostname for word in ["dev", "local", "test"]):
                self._current_environment = Environment.DEVELOPMENT
            elif any(word in hostname for word in ["staging", "stage", "preprod"]):
                self._current_environment = Environment.STAGING
            elif any(word in hostname for word in ["prod", "production", "live"]):
                self._current_environment = Environment.PRODUCTION
            else:
                # Default to development
                self._current_environment = Environment.DEVELOPMENT

        return self._current_environment

    def set_environment(self, environment: Environment) -> None:
        """
        Set current environment.

        Args:
            environment: Environment to set
        """
        self._current_environment = environment

    def get_environment(self) -> Environment:
        """Get current environment."""
        return self.detect_environment()

    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.get_environment() == Environment.DEVELOPMENT

    def is_staging(self) -> bool:
        """Check if current environment is staging."""
        return self.get_environment() == Environment.STAGING

    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.get_environment() == Environment.PRODUCTION

    def is_testing(self) -> bool:
        """Check if current environment is testing."""
        return self.get_environment() == Environment.TESTING


class EnvironmentConfigLoader:
    """Loads environment-specific configurations."""

    def __init__(self, config_dir: str | None = None):
        """
        Initialize config loader.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir or os.getenv("OPSVI_CONFIG_DIR", "./config")
        self.detector = EnvironmentDetector()
        self._configs: dict[str, EnvironmentConfig] = {}

    def load_config(
        self,
        environment: Environment | None = None,
    ) -> EnvironmentConfig:
        """
        Load configuration for environment.

        Args:
            environment: Environment to load config for (uses detected if None)

        Returns:
            Environment configuration
        """
        env = environment or self.detector.get_environment()
        env_name = env.value

        if env_name in self._configs:
            return self._configs[env_name]

        # Try to load from file
        config = self._load_from_file(env_name)
        if config:
            self._configs[env_name] = config
            return config

        # Create default config
        config = self._create_default_config(env)
        self._configs[env_name] = config
        return config

    def _load_from_file(self, environment_name: str) -> EnvironmentConfig | None:
        """
        Load configuration from file.

        Args:
            environment_name: Environment name

        Returns:
            Environment configuration or None if not found
        """
        config_paths = [
            Path(self.config_dir) / f"{environment_name}.json",
            Path(self.config_dir) / f"{environment_name}.yaml",
            Path(self.config_dir) / f"{environment_name}.yml",
            Path(self.config_dir) / f"{environment_name}.toml",
            Path(self.config_dir) / f"{environment_name}.ini",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    return self._parse_config_file(config_path, environment_name)
                except Exception as e:
                    print(f"Failed to load config from {config_path}: {e}")

        return None

    def _parse_config_file(
        self,
        config_path: Path,
        environment_name: str,
    ) -> EnvironmentConfig:
        """
        Parse configuration file.

        Args:
            config_path: Path to configuration file
            environment_name: Environment name

        Returns:
            Environment configuration
        """
        suffix = config_path.suffix.lower()

        if suffix == ".json":
            with open(config_path) as f:
                data = json.load(f)
        elif suffix in [".yaml", ".yml"]:
            import yaml

            with open(config_path) as f:
                data = yaml.safe_load(f)
        elif suffix == ".toml":
            import tomllib

            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        elif suffix == ".ini":
            import configparser

            parser = configparser.ConfigParser()
            parser.read(config_path)
            data = dict(parser)
        else:
            raise EnvironmentError(f"Unsupported config file format: {suffix}")

        return self._create_config_from_dict(data, environment_name)

    def _create_config_from_dict(
        self,
        data: dict[str, Any],
        environment_name: str,
    ) -> EnvironmentConfig:
        """
        Create configuration from dictionary.

        Args:
            data: Configuration data
            environment_name: Environment name

        Returns:
            Environment configuration
        """
        environment = Environment(environment_name)

        return EnvironmentConfig(
            name=environment_name,
            environment=environment,
            debug=data.get("debug", environment == Environment.DEVELOPMENT),
            log_level=data.get("log_level", "INFO"),
            database_url=data.get("database_url"),
            redis_url=data.get("redis_url"),
            api_keys=data.get("api_keys", {}),
            feature_flags=data.get("feature_flags", {}),
            custom_settings=data.get("custom_settings", {}),
        )

    def _create_default_config(self, environment: Environment) -> EnvironmentConfig:
        """
        Create default configuration for environment.

        Args:
            environment: Environment

        Returns:
            Default environment configuration
        """
        if environment == Environment.DEVELOPMENT:
            return EnvironmentConfig(
                name="development",
                environment=environment,
                debug=True,
                log_level="DEBUG",
                database_url="sqlite:///dev.db",
                redis_url="redis://localhost:6379/0",
                feature_flags={
                    "experimental_features": True,
                    "debug_mode": True,
                    "hot_reload": True,
                },
            )
        if environment == Environment.STAGING:
            return EnvironmentConfig(
                name="staging",
                environment=environment,
                debug=False,
                log_level="INFO",
                database_url=os.getenv("STAGING_DATABASE_URL"),
                redis_url=os.getenv("STAGING_REDIS_URL"),
                feature_flags={
                    "experimental_features": True,
                    "debug_mode": False,
                    "hot_reload": False,
                },
            )
        if environment == Environment.PRODUCTION:
            return EnvironmentConfig(
                name="production",
                environment=environment,
                debug=False,
                log_level="WARNING",
                database_url=os.getenv("PRODUCTION_DATABASE_URL"),
                redis_url=os.getenv("PRODUCTION_REDIS_URL"),
                feature_flags={
                    "experimental_features": False,
                    "debug_mode": False,
                    "hot_reload": False,
                },
            )
        # TESTING
        return EnvironmentConfig(
            name="testing",
            environment=environment,
            debug=True,
            log_level="DEBUG",
            database_url="sqlite:///test.db",
            redis_url="redis://localhost:6379/1",
            feature_flags={
                "experimental_features": True,
                "debug_mode": True,
                "hot_reload": False,
            },
        )

    def save_config(self, config: EnvironmentConfig) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
        """
        config_dir = Path(self.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / f"{config.name}.json"

        data = {
            "debug": config.debug,
            "log_level": config.log_level,
            "database_url": config.database_url,
            "redis_url": config.redis_url,
            "api_keys": config.api_keys,
            "feature_flags": config.feature_flags,
            "custom_settings": config.custom_settings,
        }

        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    def reload_config(
        self,
        environment: Environment | None = None,
    ) -> EnvironmentConfig:
        """
        Reload configuration for environment.

        Args:
            environment: Environment to reload config for

        Returns:
            Reloaded environment configuration
        """
        env = environment or self.detector.get_environment()
        env_name = env.value

        # Clear cache
        if env_name in self._configs:
            del self._configs[env_name]

        return self.load_config(env)


class EnvironmentManager:
    """Manages multiple environment configurations."""

    def __init__(self):
        """Initialize environment manager."""
        self.detector = EnvironmentDetector()
        self.loader = EnvironmentConfigLoader()
        self._current_config: EnvironmentConfig | None = None

    def get_current_config(self) -> EnvironmentConfig:
        """
        Get current environment configuration.

        Returns:
            Current environment configuration
        """
        if not self._current_config:
            self._current_config = self.loader.load_config()
        return self._current_config

    def get_config(self, environment: Environment) -> EnvironmentConfig:
        """
        Get configuration for specific environment.

        Args:
            environment: Environment

        Returns:
            Environment configuration
        """
        return self.loader.load_config(environment)

    def set_environment(self, environment: Environment) -> None:
        """
        Set current environment.

        Args:
            environment: Environment to set
        """
        self.detector.set_environment(environment)
        self._current_config = None  # Clear cache

    def get_environment(self) -> Environment:
        """Get current environment."""
        return self.detector.get_environment()

    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.detector.is_development()

    def is_staging(self) -> bool:
        """Check if current environment is staging."""
        return self.detector.is_staging()

    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.detector.is_production()

    def is_testing(self) -> bool:
        """Check if current environment is testing."""
        return self.detector.is_testing()

    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """
        Get feature flag value.

        Args:
            flag_name: Feature flag name
            default: Default value if flag not found

        Returns:
            Feature flag value
        """
        config = self.get_current_config()
        return config.feature_flags.get(flag_name, default)

    def get_api_key(self, service_name: str) -> str | None:
        """
        Get API key for service.

        Args:
            service_name: Service name

        Returns:
            API key or None if not found
        """
        config = self.get_current_config()
        return config.api_keys.get(service_name)

    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """
        Get custom setting value.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value
        """
        config = self.get_current_config()
        return config.custom_settings.get(key, default)


# Global environment manager
environment_manager = EnvironmentManager()


def environment_config(environment: Environment):
    """
    Decorator for environment-specific configuration.

    Args:
        environment: Environment for configuration
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Set environment temporarily
            original_env = environment_manager.get_environment()
            environment_manager.set_environment(environment)

            try:
                return func(*args, **kwargs)
            finally:
                # Restore original environment
                environment_manager.set_environment(original_env)

        return wrapper

    return decorator


def feature_flag(flag_name: str, default: bool = False):
    """
    Decorator for feature flag-based execution.

    Args:
        flag_name: Feature flag name
        default: Default value if flag not found
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if environment_manager.get_feature_flag(flag_name, default):
                return func(*args, **kwargs)
            # Return None or raise exception based on context
            return None

        return wrapper

    return decorator
