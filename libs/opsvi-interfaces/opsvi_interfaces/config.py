"""
Configuration Management Interface
Provides configuration loading, validation, and management
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Union

import yaml


class Configuration:
    """Configuration object that holds settings"""

    def __init__(self, data: Dict[str, Any] = None):
        """Initialize configuration"""
        self._data = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def update(self, data: Dict[str, Any]):
        """Update configuration with dictionary"""
        self._merge_dict(self._data, data)

    def _merge_dict(self, dest: Dict, source: Dict):
        """Recursively merge dictionaries"""
        for key, value in source.items():
            if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                self._merge_dict(dest[key], value)
            else:
                dest[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return self._data.copy()

    def to_json(self) -> str:
        """Export configuration as JSON"""
        return json.dumps(self._data, indent=2)

    def to_yaml(self) -> str:
        """Export configuration as YAML"""
        return yaml.dump(self._data, default_flow_style=False)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, app_name: str = None, config_dir: str = None):
        """Initialize configuration manager"""
        self.app_name = app_name or "app"
        self.config_dir = (
            Path(config_dir) if config_dir else Path.home() / f".{app_name}"
        )
        self.config_file = self.config_dir / "config.yaml"
        self.configuration = Configuration()

        # Load default configuration
        self._load_defaults()

        # Load user configuration if exists
        if self.config_file.exists():
            self.load_config(self.config_file)

    def _load_defaults(self):
        """Load default configuration"""
        defaults = {
            "app": {"name": self.app_name, "version": "0.1.0"},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "paths": {
                "config": str(self.config_dir),
                "data": str(self.config_dir / "data"),
                "logs": str(self.config_dir / "logs"),
            },
        }
        self.configuration.update(defaults)

    def load_config(self, path: Union[str, Path]) -> Configuration:
        """Load configuration from file"""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Determine format from extension
        if path.suffix in [".yaml", ".yml"]:
            with open(path) as f:
                data = yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration format: {path.suffix}")

        self.configuration.update(data)
        return self.configuration

    def save_config(self, path: Union[str, Path] = None):
        """Save configuration to file"""
        path = Path(path) if path else self.config_file

        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save based on extension
        if path.suffix in [".yaml", ".yml"]:
            with open(path, "w") as f:
                f.write(self.configuration.to_yaml())
        elif path.suffix == ".json":
            with open(path, "w") as f:
                f.write(self.configuration.to_json())
        else:
            # Default to YAML
            with open(path, "w") as f:
                f.write(self.configuration.to_yaml())

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.configuration.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.configuration.set(key, value)

    def get_config(self) -> Configuration:
        """Get configuration object"""
        return self.configuration

    def reset(self):
        """Reset to default configuration"""
        self.configuration = Configuration()
        self._load_defaults()

    def load_env(self, prefix: str = None):
        """Load configuration from environment variables"""
        prefix = prefix or self.app_name.upper()

        for key, value in os.environ.items():
            if key.startswith(f"{prefix}_"):
                # Convert env var to config key
                config_key = key[len(prefix) + 1 :].lower().replace("_", ".")
                self.configuration.set(config_key, value)
