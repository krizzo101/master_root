"""
Plugins module for opsvi-core.

Provides plugin system, loader, registry, and sandboxing capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base plugin infrastructure
from .base import (
    BasePlugin,
    PluginError,
    PluginLoader,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    PluginState,
)

__all__ = [
    # Base classes
    "BasePlugin",
    "PluginError",
    "PluginLoader",
    "PluginManager",
    "PluginMetadata",
    "PluginRegistry",
    "PluginState",
]

__version__ = "1.0.0"
