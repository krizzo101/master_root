"""Configuration management for Hello CLI."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from hello_cli.errors import ConfigurationError


class Config:
    """Configuration manager for Hello CLI."""

    DEFAULT_CONFIG = {
        "greeting": "Hello",
        "styles": {
            "plain": "{greeting}, {name}!",
            "emoji": "👋 {greeting}, {name}! 🎉",
            "banner": "\n{'=' * 40}\n{greeting}, {name}!\n{'=' * 40}",
        },
        "default_style": "plain",
        "uppercase": False,
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_path: Optional path to config file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get default config path."""
        config_dir = Path.home() / ".config" / "hello-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except (json.JSONDecodeError, IOError) as e:
                raise ConfigurationError(f"Failed to load config: {e}")
        return self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            raise ConfigurationError(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
