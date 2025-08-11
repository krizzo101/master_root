"""
DRY Configuration Manager - Centralized Configuration Handling

Eliminates configuration pattern duplication across plugins and clients.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ConfigValidationRule:
    """Configuration validation rule."""

    required: bool = False
    type_check: Optional[Type] = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    default: Any = None


class ConfigurationError(Exception):
    """Configuration related errors."""

    pass


class ConfigValidator:
    """Validates configuration against defined rules."""

    def __init__(self, rules: Dict[str, ConfigValidationRule]):
        self.rules = rules

    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate configuration against rules.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        for key, rule in self.rules.items():
            if rule.required and key not in config:
                errors.append(f"Required configuration key missing: {key}")
                continue

            if key not in config:
                # Set default if available
                if rule.default is not None:
                    config[key] = rule.default
                continue

            value = config[key]

            # Type checking
            if rule.type_check and not isinstance(value, rule.type_check):
                errors.append(
                    f"Configuration key '{key}' must be of type {rule.type_check.__name__}, got {type(value).__name__}"
                )

            # Choice validation
            if rule.choices and value not in rule.choices:
                errors.append(
                    f"Configuration key '{key}' must be one of {rule.choices}, got '{value}'"
                )

            # Range validation for numeric types
            if isinstance(value, (int, float)):
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(
                        f"Configuration key '{key}' must be >= {rule.min_value}, got {value}"
                    )
                if rule.max_value is not None and value > rule.max_value:
                    errors.append(
                        f"Configuration key '{key}' must be <= {rule.max_value}, got {value}"
                    )

            # Pattern validation for strings
            if rule.pattern and isinstance(value, str):
                import re

                if not re.match(rule.pattern, value):
                    errors.append(
                        f"Configuration key '{key}' does not match required pattern: {rule.pattern}"
                    )

        return len(errors) == 0, errors


class ConfigLoaderBase(ABC):
    """Abstract base for configuration loaders."""

    @abstractmethod
    def load(self, source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Load configuration from source."""
        pass

    @abstractmethod
    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """Save configuration to destination."""
        pass


class JSONConfigLoader(ConfigLoaderBase):
    """JSON configuration loader."""

    def load(self, source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Load configuration from JSON file or dict."""
        if isinstance(source, dict):
            return source.copy()

        try:
            with open(source, "r") as f:
                return json.load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load JSON config from {source}: {e}")

    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """Save configuration to JSON file."""
        try:
            with open(destination, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save JSON config to {destination}: {e}"
            )


class YAMLConfigLoader(ConfigLoaderBase):
    """YAML configuration loader."""

    def load(self, source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Load configuration from YAML file or dict."""
        if isinstance(source, dict):
            return source.copy()

        try:
            with open(source, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load YAML config from {source}: {e}")

    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """Save configuration to YAML file."""
        try:
            with open(destination, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save YAML config to {destination}: {e}"
            )


class EnvironmentConfigLoader(ConfigLoaderBase):
    """Environment variable configuration loader."""

    def __init__(self, prefix: str = "ASEA_"):
        self.prefix = prefix

    def load(self, source: Union[str, Path, Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix) :].lower()

                # Try to parse as JSON for complex values
                try:
                    config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    config[config_key] = value

        return config

    def save(
        self, config: Dict[str, Any], destination: Union[str, Path] = None
    ) -> bool:
        """Environment variables can't be saved persistently."""
        return False


class ConfigManager:
    """
    Centralized configuration manager eliminating config duplication.

    Eliminates duplication of:
    - Configuration loading patterns
    - Validation logic
    - Environment variable handling
    - Default value management
    - Configuration merging
    """

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.config_dir.mkdir(exist_ok=True)

        self._loaders = {
            "json": JSONConfigLoader(),
            "yaml": YAMLConfigLoader(),
            "yml": YAMLConfigLoader(),
            "env": EnvironmentConfigLoader(),
        }

        self._cached_configs: Dict[str, Dict[str, Any]] = {}
        self._validators: Dict[str, ConfigValidator] = {}

    def register_validator(
        self, config_name: str, rules: Dict[str, ConfigValidationRule]
    ) -> None:
        """Register validation rules for a configuration."""
        self._validators[config_name] = ConfigValidator(rules)

    def load_config(
        self,
        config_name: str,
        sources: Optional[List[Union[str, Path, Dict[str, Any]]]] = None,
        use_cache: bool = True,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Load configuration from multiple sources with validation.

        Args:
            config_name: Name of the configuration
            sources: List of sources to load from (files, dicts, etc.)
            use_cache: Whether to use cached config if available
            validate: Whether to validate the configuration

        Returns:
            Merged and validated configuration
        """
        # Return cached config if available
        if use_cache and config_name in self._cached_configs:
            return self._cached_configs[config_name].copy()

        config = {}

        # Default sources if none provided
        if sources is None:
            sources = [
                self.config_dir / f"{config_name}.json",
                self.config_dir / f"{config_name}.yaml",
                self.config_dir / f"{config_name}.yml",
                "env",  # Environment variables
            ]

        # Load from all sources and merge
        for source in sources:
            try:
                if source == "env":
                    env_config = self._loaders["env"].load()
                    config.update(env_config)
                elif isinstance(source, dict):
                    config.update(source)
                else:
                    source_path = Path(source)
                    if source_path.exists():
                        extension = source_path.suffix[1:].lower()
                        if extension in self._loaders:
                            loaded_config = self._loaders[extension].load(source_path)
                            config.update(loaded_config)
            except Exception as e:
                # Log warning but continue with other sources
                print(f"Warning: Failed to load config from {source}: {e}")

        # Validate configuration
        if validate and config_name in self._validators:
            is_valid, errors = self._validators[config_name].validate(config)
            if not is_valid:
                raise ConfigurationError(
                    f"Configuration validation failed for {config_name}: {errors}"
                )

        # Cache the configuration
        if use_cache:
            self._cached_configs[config_name] = config.copy()

        return config

    def save_config(
        self,
        config_name: str,
        config: Dict[str, Any],
        format: str = "json",
        validate: bool = True,
    ) -> bool:
        """
        Save configuration to file.

        Args:
            config_name: Name of the configuration
            config: Configuration data
            format: Output format (json, yaml)
            validate: Whether to validate before saving

        Returns:
            True if successful, False otherwise
        """
        # Validate before saving
        if validate and config_name in self._validators:
            is_valid, errors = self._validators[config_name].validate(config)
            if not is_valid:
                raise ConfigurationError(f"Configuration validation failed: {errors}")

        # Save configuration
        try:
            output_path = self.config_dir / f"{config_name}.{format}"
            success = self._loaders[format].save(config, output_path)

            # Update cache
            if success:
                self._cached_configs[config_name] = config.copy()

            return success
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration {config_name}: {e}")

    def get_config_value(
        self, config_name: str, key: str, default: Any = None, required: bool = False
    ) -> Any:
        """
        Get a specific configuration value.

        Args:
            config_name: Name of the configuration
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            required: Whether the key is required

        Returns:
            Configuration value
        """
        config = self.load_config(config_name)

        # Support dot notation for nested keys
        keys = key.split(".")
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            if required:
                raise ConfigurationError(f"Required configuration key not found: {key}")
            return default

    def set_config_value(
        self, config_name: str, key: str, value: Any, save: bool = True
    ) -> bool:
        """
        Set a specific configuration value.

        Args:
            config_name: Name of the configuration
            key: Configuration key (supports dot notation)
            value: Value to set
            save: Whether to save to file immediately

        Returns:
            True if successful
        """
        config = self.load_config(config_name)

        # Support dot notation for nested keys
        keys = key.split(".")
        current = config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

        # Update cache
        self._cached_configs[config_name] = config

        # Save if requested
        if save:
            return self.save_config(config_name, config)

        return True

    def clear_cache(self, config_name: Optional[str] = None) -> None:
        """Clear configuration cache."""
        if config_name:
            self._cached_configs.pop(config_name, None)
        else:
            self._cached_configs.clear()


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config(config_name: str, **kwargs) -> Dict[str, Any]:
    """
    Get configuration using global manager.

    This is the DRY replacement for scattered config loading patterns.
    """
    return _config_manager.load_config(config_name, **kwargs)


def get_config_value(
    config_name: str, key: str, default: Any = None, required: bool = False
) -> Any:
    """Get specific configuration value using global manager."""
    return _config_manager.get_config_value(config_name, key, default, required)


def register_config_schema(
    config_name: str, rules: Dict[str, ConfigValidationRule]
) -> None:
    """Register configuration validation schema."""
    _config_manager.register_validator(config_name, rules)


def save_config(config_name: str, config: Dict[str, Any], **kwargs) -> bool:
    """Save configuration using global manager."""
    return _config_manager.save_config(config_name, config, **kwargs)


# Common configuration schemas
PLUGIN_CONFIG_SCHEMA = {
    "enabled": ConfigValidationRule(required=True, type_check=bool, default=True),
    "timeout": ConfigValidationRule(
        type_check=int, min_value=1, max_value=300, default=30
    ),
    "retry_count": ConfigValidationRule(
        type_check=int, min_value=0, max_value=10, default=3
    ),
    "log_level": ConfigValidationRule(
        type_check=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    ),
}

DATABASE_CONFIG_SCHEMA = {
    "host": ConfigValidationRule(required=True, type_check=str),
    "database": ConfigValidationRule(required=True, type_check=str),
    "username": ConfigValidationRule(required=True, type_check=str),
    "password": ConfigValidationRule(required=True, type_check=str),
    "timeout": ConfigValidationRule(
        type_check=int, min_value=5, max_value=60, default=30
    ),
    "pool_size": ConfigValidationRule(
        type_check=int, min_value=1, max_value=100, default=10
    ),
}

API_CONFIG_SCHEMA = {
    "api_key": ConfigValidationRule(required=True, type_check=str),
    "base_url": ConfigValidationRule(type_check=str),
    "timeout": ConfigValidationRule(
        type_check=int, min_value=5, max_value=300, default=30
    ),
    "rate_limit": ConfigValidationRule(type_check=int, min_value=1, default=100),
    "retry_attempts": ConfigValidationRule(
        type_check=int, min_value=0, max_value=10, default=3
    ),
}
