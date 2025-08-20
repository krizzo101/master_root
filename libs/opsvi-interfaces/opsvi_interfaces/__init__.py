"""
OpsVi Interfaces Library
Provides common interfaces for CLI, web, and configuration management
"""

from .cli import BaseCLI, Command, command
from .config import ConfigManager, Configuration

__version__ = "0.1.0"

__all__ = ["BaseCLI", "Command", "command", "ConfigManager", "Configuration"]
