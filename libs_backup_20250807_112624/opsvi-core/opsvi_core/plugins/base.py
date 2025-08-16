"""
Base plugin infrastructure for OPSVI Core.

Provides plugin architecture and management capabilities.
"""

from __future__ import annotations

import importlib
import importlib.util
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger

logger = get_logger(__name__)


class PluginError(ComponentError):
    """Raised when plugin operations fail."""

    pass


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata and information."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = "main"
    config_schema: dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """Abstract base class for plugins."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.state = PluginState.UNLOADED
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the plugin."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the plugin."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)


class PluginRegistry(BaseComponent):
    """Plugin registry and lifecycle management."""

    def __init__(self):
        super().__init__()
        self._plugins: dict[str, BasePlugin] = {}
        self._plugin_states: dict[str, PluginState] = {}
        self._plugin_hooks: dict[str, list[Callable]] = {}

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Register a plugin."""
        metadata = plugin.metadata
        if metadata.name in self._plugins:
            raise PluginError(f"Plugin '{metadata.name}' already registered")

        self._plugins[metadata.name] = plugin
        self._plugin_states[metadata.name] = PluginState.LOADED
        logger.info("Registered plugin: %s v%s", metadata.name, metadata.version)

    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not found")

        if self._plugin_states[name] == PluginState.ACTIVE:
            # Stop plugin before unregistering
            import asyncio

            asyncio.create_task(self.stop_plugin(name))

        del self._plugins[name]
        del self._plugin_states[name]
        logger.info("Unregistered plugin: %s", name)

    async def initialize_plugin(self, name: str) -> None:
        """Initialize a plugin."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not found")

        plugin = self._plugins[name]
        try:
            await plugin.initialize()
            plugin.state = PluginState.INACTIVE
            self._plugin_states[name] = PluginState.INACTIVE
            logger.info("Initialized plugin: %s", name)
        except Exception as e:
            plugin.state = PluginState.ERROR
            self._plugin_states[name] = PluginState.ERROR
            logger.error("Failed to initialize plugin %s: %s", name, e)
            raise PluginError(f"Plugin initialization failed: {e}") from e

    async def start_plugin(self, name: str) -> None:
        """Start a plugin."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not found")

        plugin = self._plugins[name]
        if plugin.state not in [PluginState.INACTIVE, PluginState.LOADED]:
            raise PluginError(
                f"Plugin '{name}' cannot be started from state {plugin.state}"
            )

        try:
            if plugin.state == PluginState.LOADED:
                await plugin.initialize()

            await plugin.start()
            plugin.state = PluginState.ACTIVE
            self._plugin_states[name] = PluginState.ACTIVE
            logger.info("Started plugin: %s", name)
        except Exception as e:
            plugin.state = PluginState.ERROR
            self._plugin_states[name] = PluginState.ERROR
            logger.error("Failed to start plugin %s: %s", name, e)
            raise PluginError(f"Plugin start failed: {e}") from e

    async def stop_plugin(self, name: str) -> None:
        """Stop a plugin."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not found")

        plugin = self._plugins[name]
        if plugin.state != PluginState.ACTIVE:
            return  # Already stopped

        try:
            await plugin.stop()
            plugin.state = PluginState.INACTIVE
            self._plugin_states[name] = PluginState.INACTIVE
            logger.info("Stopped plugin: %s", name)
        except Exception as e:
            plugin.state = PluginState.ERROR
            self._plugin_states[name] = PluginState.ERROR
            logger.error("Failed to stop plugin %s: %s", name, e)
            raise PluginError(f"Plugin stop failed: {e}") from e

    def get_plugin(self, name: str) -> BasePlugin:
        """Get a plugin by name."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not found")
        return self._plugins[name]

    def list_plugins(self) -> dict[str, dict[str, Any]]:
        """List all plugins with their status."""
        return {
            name: {
                "metadata": plugin.metadata.__dict__,
                "state": self._plugin_states[name].value,
            }
            for name, plugin in self._plugins.items()
        }

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        if hook_name not in self._plugin_hooks:
            self._plugin_hooks[hook_name] = []
        self._plugin_hooks[hook_name].append(callback)
        logger.debug("Registered hook callback for: %s", hook_name)

    async def execute_hooks(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """Execute all callbacks for a hook."""
        if hook_name not in self._plugin_hooks:
            return []

        results = []
        for callback in self._plugin_hooks[hook_name]:
            try:
                import asyncio

                if asyncio.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error("Hook callback failed for %s: %s", hook_name, e)

        return results


class PluginLoader(BaseComponent):
    """Plugin loader from files and modules."""

    def __init__(self, registry: PluginRegistry):
        super().__init__()
        self.registry = registry

    async def load_from_file(
        self, file_path: str | Path, config: dict[str, Any] | None = None
    ) -> str:
        """Load plugin from Python file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise PluginError(f"Plugin file not found: {file_path}")

        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("plugin_module", file_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"Cannot load plugin from {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr != BasePlugin
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                raise PluginError(f"No plugin class found in {file_path}")

            # Create plugin instance
            plugin = plugin_class(config)
            self.registry.register_plugin(plugin)

            return plugin.metadata.name

        except Exception as e:
            logger.error("Failed to load plugin from %s: %s", file_path, e)
            raise PluginError(f"Plugin loading failed: {e}") from e

    async def load_from_module(
        self, module_name: str, config: dict[str, Any] | None = None
    ) -> str:
        """Load plugin from Python module."""
        try:
            module = importlib.import_module(module_name)

            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr != BasePlugin
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                raise PluginError(f"No plugin class found in module {module_name}")

            # Create plugin instance
            plugin = plugin_class(config)
            self.registry.register_plugin(plugin)

            return plugin.metadata.name

        except ImportError as e:
            raise PluginError(f"Cannot import module {module_name}: {e}") from e
        except Exception as e:
            logger.error("Failed to load plugin from module %s: %s", module_name, e)
            raise PluginError(f"Plugin loading failed: {e}") from e


class PluginManager(BaseComponent):
    """Main plugin management system."""

    def __init__(self):
        super().__init__()
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)

    async def _start(self) -> None:
        """Start plugin manager."""
        await self.registry.start()
        await self.loader.start()
        logger.info("Plugin manager started")

    async def _stop(self) -> None:
        """Stop plugin manager."""
        # Stop all active plugins
        for name in list(self.registry._plugins.keys()):
            try:
                await self.registry.stop_plugin(name)
            except Exception as e:
                logger.error("Error stopping plugin %s: %s", name, e)

        await self.loader.stop()
        await self.registry.stop()
        logger.info("Plugin manager stopped")

    async def load_plugin(
        self, source: str | Path, config: dict[str, Any] | None = None
    ) -> str:
        """Load plugin from file or module."""
        if isinstance(source, str | Path) and Path(source).exists():
            return await self.loader.load_from_file(source, config)
        else:
            return await self.loader.load_from_module(str(source), config)

    async def start_plugin(self, name: str) -> None:
        """Start a plugin."""
        await self.registry.start_plugin(name)

    async def stop_plugin(self, name: str) -> None:
        """Stop a plugin."""
        await self.registry.stop_plugin(name)

    def get_plugin_status(self) -> dict[str, Any]:
        """Get status of all plugins."""
        return self.registry.list_plugins()
