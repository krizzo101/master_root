"""Configuration management for the Autonomous Coder system."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class Config:
    """System configuration manager."""
    
    DEFAULT_CONFIG = {
        "research": {
            "cache_ttl": 86400,  # 24 hours
            "max_retries": 3,
            "timeout": 30,
            "use_cache": True,
            "web_search_count": 5
        },
        "generation": {
            "default_language": "typescript",
            "style_guide": "standard",
            "documentation": True,
            "tests": True,
            "use_templates": True
        },
        "validation": {
            "strict_mode": True,
            "security_scan": True,
            "performance_check": False,
            "max_file_size": 1048576  # 1MB
        },
        "orchestration": {
            "parallel_tasks": 4,
            "checkpoint_interval": 300,  # 5 minutes
            "progress_reporting": True,
            "auto_fix_errors": True
        },
        "paths": {
            "templates": "templates",
            "knowledge": "knowledge",
            "cache": ".cache",
            "output": "output"
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration from file or defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and config_path.exists():
            self.load_from_file(config_path)
    
    def load_from_file(self, path: Path):
        """Load configuration from a file."""
        if path.suffix == '.json':
            with open(path, 'r') as f:
                custom_config = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            if not HAS_YAML:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
            with open(path, 'r') as f:
                custom_config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        self._merge_config(custom_config)
    
    def _merge_config(self, custom: Dict[str, Any]):
        """Merge custom configuration with defaults."""
        def merge_dict(base: dict, custom: dict):
            for key, value in custom.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self.config, custom)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value by dot-notation key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Path):
        """Save configuration to a file."""
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            if not HAS_YAML:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
            with open(path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-style setting."""
        self.set(key, value)