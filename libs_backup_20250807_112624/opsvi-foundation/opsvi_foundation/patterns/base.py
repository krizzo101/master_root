"""
Base patterns and components.

Provides abstract base classes and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Any


class ComponentError(Exception):
    """Base exception for all foundation components."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class BaseComponent(ABC):
    """Abstract base class for all components."""

    def __init__(self):
        self._initialized = False
        self._active = False

    async def initialize(self) -> None:
        """Initialize the component."""
        if self._initialized:
            return

        await self._initialize()
        self._initialized = True

    async def start(self) -> None:
        """Start the component."""
        if not self._initialized:
            await self.initialize()

        if self._active:
            return

        await self._start()
        self._active = True

    async def stop(self) -> None:
        """Stop the component."""
        if not self._active:
            return

        await self._stop()
        self._active = False

    async def cleanup(self) -> None:
        """Cleanup component resources."""
        if self._active:
            await self.stop()

        await self._cleanup()
        self._initialized = False

    def is_active(self) -> bool:
        """Check if component is active."""
        return self._active

    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized

    @abstractmethod
    async def _initialize(self) -> None:
        """Component-specific initialization logic."""

    async def _start(self) -> None:
        """Component-specific start logic."""

    async def _stop(self) -> None:
        """Component-specific stop logic."""

    async def _cleanup(self) -> None:
        """Component-specific cleanup logic."""


class LifecycleComponent(BaseComponent):
    """Simple lifecycle component with minimal interface."""

    async def _initialize(self) -> None:
        """Default initialization - override if needed."""
