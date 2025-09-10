"""
Configuration management system with environment variable support and validation.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List, Type
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
from functools import lru_cache

from pydantic import BaseModel, Field, validator, ValidationError


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    ENV = "env"


@dataclass
class ConfigSource:
    """Configuration source metadata."""

    path: Optional[Path] = None
    format: ConfigFormat = ConfigFormat.JSON
    priority: int = 0  # Higher priority overrides lower
    is_required: bool = False
    prefix: Optional[str] = None  # For environment variables


class BaseConfig(BaseModel):
    """Base configuration model with validation."""

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Prevent unknown fields
        validate_assignment = True
        use_enum_values = True


class MonitoringConfig(BaseConfig):
    """Monitoring configuration."""

    enabled: bool = True
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    dashboard_port: int = Field(default=8080, ge=1024, le=65535)
    alert_webhook: Optional[str] = None
    health_check_interval: int = Field(default=30, ge=10)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @validator("alert_webhook")
    def validate_webhook_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class ClaudeConfig(BaseConfig):
    """Claude API configuration."""

    api_key: str = Field(..., min_length=1)
    model: str = Field(default="claude-3-sonnet-20240229")
    max_tokens: int = Field(default=4096, ge=1, le=100000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    timeout: int = Field(default=300, ge=10)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1)


class GovernanceConfig(BaseConfig):
    """Governance configuration."""

    require_approval: bool = True
    auto_approve_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    max_resource_usage: Dict[str, Any] = Field(
        default_factory=lambda: {"cpu_percent": 80, "memory_percent": 70, "disk_gb": 10}
    )
    audit_enabled: bool = True
    audit_retention_days: int = Field(default=30, ge=1)


class LearningConfig(BaseConfig):
    """Learning system configuration."""

    enabled: bool = True
    experience_buffer_size: int = Field(default=10000, ge=100)
    learning_rate: float = Field(default=0.01, ge=0.0001, le=1.0)
    update_frequency: int = Field(default=100, ge=10)
    knowledge_base_path: Path = Field(default=Path("./knowledge"))
    pattern_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class AppConfig(BaseConfig):
    """Complete application configuration."""

    app_name: str = Field(default="autonomous-claude-agent")
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = Field(default=False)

    # Sub-configurations
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    claude: ClaudeConfig
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)

    # Paths
    data_dir: Path = Field(default=Path("./data"))
    cache_dir: Path = Field(default=Path("./cache"))
    log_dir: Path = Field(default=Path("./logs"))

    @validator("environment")
    def validate_environment(cls, v, values):
        if v == "production" and values.get("debug"):
            raise ValueError("Debug mode cannot be enabled in production")
        return v


class ConfigLoader:
    """Configuration loader with multiple source support."""

    def __init__(self, config_dir: Path = Path("./config")):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config: Optional[AppConfig] = None
        self._sources: List[ConfigSource] = []
        self._raw_config: Dict[str, Any] = {}

    def add_source(self, source: ConfigSource):
        """Add a configuration source."""
        self._sources.append(source)
        self._sources.sort(key=lambda x: x.priority)

    def load_file(self, path: Path, format: ConfigFormat) -> Dict[str, Any]:
        """Load configuration from a file."""
        if not path.exists():
            return {}

        with open(path, "r") as f:
            if format == ConfigFormat.JSON:
                return json.load(f)
            elif format == ConfigFormat.YAML:
                return yaml.safe_load(f) or {}
            else:
                raise ValueError(f"Unsupported format: {format}")

    def load_env_vars(self, prefix: str = "ACA_") -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        prefix = prefix.upper()

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert ACA_CLAUDE_API_KEY to claude.api_key
                config_key = key[len(prefix) :].lower()
                config_key = config_key.replace("_", ".")

                # Convert value types
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                elif re.match(r"^\d+\.\d+$", value):
                    value = float(value)

                # Set nested value
                self._set_nested_value(config, config_key, value)

        return config

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """Set a nested value in config dictionary."""
        parts = key.split(".")
        current = config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def load(self, validate: bool = True) -> AppConfig:
        """Load configuration from all sources."""
        config = {}

        # Load from sources in priority order
        for source in self._sources:
            source_config = {}

            if source.format == ConfigFormat.ENV:
                source_config = self.load_env_vars(source.prefix or "ACA_")
            elif source.path:
                source_config = self.load_file(source.path, source.format)
                if source.is_required and not source_config:
                    raise FileNotFoundError(f"Required config file not found: {source.path}")

            config = self._merge_configs(config, source_config)

        # Store raw config
        self._raw_config = config

        # Validate and create config object
        if validate:
            try:
                self._config = AppConfig(**config)
            except ValidationError as e:
                raise ValueError(f"Invalid configuration: {e}")
        else:
            self._config = AppConfig.construct(**config)

        # Create required directories
        self._create_directories()

        return self._config

    def _create_directories(self):
        """Create required directories."""
        if self._config:
            for dir_path in [self._config.data_dir, self._config.cache_dir, self._config.log_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)

    def save(self, path: Optional[Path] = None, format: ConfigFormat = ConfigFormat.JSON):
        """Save current configuration to file."""
        if not self._config:
            raise ValueError("No configuration loaded")

        path = path or self.config_dir / f"config.{format.value}"
        config_dict = self._config.dict()

        # Convert Path objects to strings
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            return obj

        config_dict = convert_paths(config_dict)

        with open(path, "w") as f:
            if format == ConfigFormat.JSON:
                json.dump(config_dict, f, indent=2)
            elif format == ConfigFormat.YAML:
                yaml.safe_dump(config_dict, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key."""
        if not self._config:
            return default

        value = self._config
        for part in key.split("."):
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return default

        return value

    def reload(self) -> AppConfig:
        """Reload configuration from sources."""
        return self.load()

    @property
    def config(self) -> Optional[AppConfig]:
        """Get current configuration."""
        return self._config


# Global configuration instance
_config_loader = ConfigLoader()


def get_config() -> AppConfig:
    """Get global configuration."""
    if not _config_loader.config:
        # Set up default sources
        _config_loader.add_source(
            ConfigSource(path=Path("./config/default.json"), format=ConfigFormat.JSON, priority=0)
        )
        _config_loader.add_source(
            ConfigSource(path=Path("./config/config.yaml"), format=ConfigFormat.YAML, priority=1)
        )
        _config_loader.add_source(ConfigSource(format=ConfigFormat.ENV, priority=2, prefix="ACA_"))

        # Load configuration
        _config_loader.load(validate=False)  # Don't validate if Claude API key not set

    return _config_loader.config


@lru_cache(maxsize=128)
def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value with caching."""
    return _config_loader.get(key, default)


# Example usage
if __name__ == "__main__":
    # Create example configuration
    config = AppConfig(
        claude=ClaudeConfig(api_key="test-key"), environment="development", debug=True
    )

    print(json.dumps(config.dict(), indent=2, default=str))
