"""
Configuration package for O3 Code Generator.

This package contains all configuration management functionality including:
- Configuration file loading and validation
- Default value management
- Environment-specific settings
- Configuration manager class
"""

from .config_manager import ConfigManager
from .defaults import DEFAULT_CONFIG

__all__ = ["ConfigManager", "DEFAULT_CONFIG"]
