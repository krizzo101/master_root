"""Configuration handling for Project Mapper.

This module provides functionality for loading, validating, and managing
configuration settings from various sources.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration settings."""

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """Validate the configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Check for required fields
        required_fields = []
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate include/exclude patterns
        if "include_patterns" in config and not isinstance(config["include_patterns"], list):
            errors.append("include_patterns must be a list")
            
        if "exclude_patterns" in config and not isinstance(config["exclude_patterns"], list):
            errors.append("exclude_patterns must be a list")
        
        return errors


class ConfigManager:
    """Manages configuration settings from various sources."""
    
    DEFAULT_CONFIG_PATHS = [
        "project_mapper.yaml",
        "project_mapper.yml",
        "project_mapper.json",
        ".project_mapper/config.yaml",
        ".project_mapper/config.yml",
        ".project_mapper/config.json",
    ]
    
    ENV_PREFIX = "PROJECT_MAPPER_"
    
    def __init__(self, 
                 base_config: Optional[Dict[str, Any]] = None,
                 config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            base_config: Base configuration to start with
            config_file: Path to configuration file
        """
        self.config = base_config or {}
        self.config_file = config_file
        self.validator = ConfigValidator()
    
    def load_config(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from all sources.
        
        Args:
            project_path: Project path to use for relative paths
            
        Returns:
            The merged configuration
            
        Raises:
            ValueError: If the configuration is invalid
        """
        # Start with default configuration
        config = self._get_default_config()
        
        # Load from configuration file if specified
        if self.config_file:
            file_config = self._load_config_file(self.config_file)
            config.update(file_config)
        else:
            # Try to find a configuration file in default locations
            config_path = self._find_config_file(project_path)
            if config_path:
                file_config = self._load_config_file(config_path)
                config.update(file_config)
        
        # Load from environment variables
        env_config = self._load_from_env()
        config.update(env_config)
        
        # Apply base config (highest priority)
        config.update(self.config)
        
        # Validate configuration
        errors = self.validator.validate_config(config)
        if errors:
            error_msg = "\n".join(errors)
            logger.error(f"Invalid configuration:\n{error_msg}")
            raise ValueError(f"Invalid configuration:\n{error_msg}")
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration.
        
        Returns:
            Default configuration
        """
        return {
            "include_patterns": ["**/*.py", "**/*.md"],
            "exclude_patterns": ["**/venv/**", "**/.git/**", "**/__pycache__/**"],
            "analysis": {
                "python": {
                    "enabled": True,
                    "analyze_docstrings": True,
                    "analyze_imports": True,
                },
                "markdown": {
                    "enabled": True,
                    "analyze_links": True,
                    "analyze_code_blocks": True,
                }
            },
            "output": {
                "json": {
                    "indent": 2,
                    "sort_keys": True,
                },
                "chunking": {
                    "enabled": True,
                    "max_size": 10000,
                }
            },
            "verbosity": "info"
        }
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration from file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "r") as f:
                    return yaml.safe_load(f) or {}
            elif path.suffix.lower() == ".json":
                with open(path, "r") as f:
                    return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {e}")
    
    def _find_config_file(self, project_path: Optional[str] = None) -> Optional[Path]:
        """Find a configuration file in default locations.
        
        Args:
            project_path: Project path to use for relative paths
            
        Returns:
            Path to configuration file, or None if not found
        """
        search_paths = []
        
        # Add project path locations if provided
        if project_path:
            base_path = Path(project_path)
            for config_name in self.DEFAULT_CONFIG_PATHS:
                search_paths.append(base_path / config_name)
        
        # Add home directory locations
        home_path = Path.home()
        for config_name in self.DEFAULT_CONFIG_PATHS:
            search_paths.append(home_path / config_name)
        
        # Check each path
        for path in search_paths:
            if path.exists() and path.is_file():
                logger.debug(f"Found configuration file: {path}")
                return path
        
        return None
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Returns:
            Configuration from environment
        """
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                config_key = key[len(self.ENV_PREFIX):].lower()
                
                # Handle nested keys
                if "__" in config_key:
                    parts = config_key.split("__")
                    current = config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = self._parse_env_value(value)
                else:
                    config[config_key] = self._parse_env_value(value)
        
        return config
    
    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse an environment variable value.
        
        Args:
            value: Value to parse
            
        Returns:
            Parsed value
        """
        if value.lower() in ["true", "yes"]:
            return True
        elif value.lower() in ["false", "no"]:
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            return float(value)
        elif value.startswith("[") and value.endswith("]"):
            # Handle list values
            items = value[1:-1].split(",")
            return [item.strip() for item in items]
        else:
            return value
    
    def save_config(self, config_path: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Save the configuration to a file.
        
        Args:
            config_path: Path to save the configuration to
            config: Configuration to save, or None to use current
            
        Raises:
            ValueError: If the file format is unsupported
        """
        config_to_save = config if config is not None else self.config
        path = Path(config_path)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "w") as f:
                    yaml.dump(config_to_save, f, default_flow_style=False)
            elif path.suffix.lower() == ".json":
                with open(path, "w") as f:
                    json.dump(config_to_save, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
            
            logger.debug(f"Configuration saved to: {path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise 