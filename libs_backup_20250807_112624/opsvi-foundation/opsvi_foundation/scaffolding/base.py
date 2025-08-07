"""
Centralized base framework for OPSVI libraries.

Provides generic base classes and patterns to eliminate repetition across all libraries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from opsvi_foundation.patterns.base import BaseComponent, ComponentError

T = TypeVar('T')


class LibraryBase(BaseComponent, ABC):
    """Generic base class for all OPSVI library components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the component."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check."""
        pass


class ConfigurableLibrary(LibraryBase, ABC):
    """Base class for libraries that need configuration management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize with configuration validation."""
        if self._initialized:
            return

        await self._validate_config()
        await self._do_initialize()
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown the component."""
        if not self._initialized:
            return

        await self._do_shutdown()
        self._initialized = False

    async def health_check(self) -> bool:
        """Perform health check."""
        if not self._initialized:
            return False
        return await self._do_health_check()

    @abstractmethod
    async def _validate_config(self) -> None:
        """Validate configuration."""
        pass

    @abstractmethod
    async def _do_initialize(self) -> None:
        """Perform actual initialization."""
        pass

    @abstractmethod
    async def _do_shutdown(self) -> None:
        """Perform actual shutdown."""
        pass

    @abstractmethod
    async def _do_health_check(self) -> bool:
        """Perform actual health check."""
        pass


class ServiceLibrary(ConfigurableLibrary, ABC):
    """Base class for service-oriented libraries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._running = False

    async def start(self) -> None:
        """Start the service."""
        await self.initialize()
        await self._do_start()
        self._running = True

    async def stop(self) -> None:
        """Stop the service."""
        if not self._running:
            return

        await self._do_stop()
        self._running = False
        await self.shutdown()

    async def _do_health_check(self) -> bool:
        """Health check includes running status."""
        return self._running and await self._do_service_health_check()

    @abstractmethod
    async def _do_start(self) -> None:
        """Start the service."""
        pass

    @abstractmethod
    async def _do_stop(self) -> None:
        """Stop the service."""
        pass

    @abstractmethod
    async def _do_service_health_check(self) -> bool:
        """Perform service-specific health check."""
        pass


class ManagerLibrary(ConfigurableLibrary, ABC):
    """Base class for manager libraries that coordinate other components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._components: Dict[str, Any] = {}

    async def register_component(self, name: str, component: Any) -> None:
        """Register a component."""
        self._components[name] = component

    async def get_component(self, name: str) -> Optional[Any]:
        """Get a component by name."""
        return self._components.get(name)

    async def remove_component(self, name: str) -> None:
        """Remove a component."""
        if name in self._components:
            del self._components[name]

    async def _do_health_check(self) -> bool:
        """Health check includes all components."""
        if not self._components:
            return True

        for name, component in self._components.items():
            if hasattr(component, 'health_check'):
                if not await component.health_check():
                    return False
        return True


def create_library_base(library_name: str, base_class: Type[LibraryBase] = LibraryBase) -> Type[LibraryBase]:
    """Factory function to create library-specific base classes."""

    class_name = f"OPSVI{library_name.title().replace('-', '')}Base"

    class LibrarySpecificBase(base_class):
        """Base class for {library_name} library components."""

        def __init__(self, config: Optional[Dict[str, Any]] = None):
            super().__init__(config)

    LibrarySpecificBase.__name__ = class_name
    LibrarySpecificBase.__qualname__ = class_name
    LibrarySpecificBase.__doc__ = f"Base class for {library_name} library components."

    return LibrarySpecificBase
