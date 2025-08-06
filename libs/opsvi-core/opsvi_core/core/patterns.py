"""
Base patterns for OPSVI Core Library.

Provides abstract base classes and patterns for actors, agents, and components.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from .exceptions import InitializationError


class BaseActor(ABC):
    """
    Abstract base class for actors with lifecycle and message handling.

    Provides a foundation for implementing actor-based components with
    proper lifecycle management and async message processing.
    """

    def __init__(self, name: str):
        """
        Initialize the actor.

        Args:
            name: Unique name for this actor
        """
        self.name = name
        self.active: bool = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")

    async def start(self) -> None:
        """
        Start the actor, initialize resources.

        Raises:
            InitializationError: If startup fails
        """
        try:
            await self.on_start()
            self.active = True
            self.logger.info("Actor started successfully")
        except Exception as e:
            self.logger.exception("Failed to start actor: %s", e)
            raise InitializationError(f"Failed to start actor {self.name}: {e}") from e

    async def stop(self) -> None:
        """
        Stop the actor, release resources.

        Raises:
            InitializationError: If shutdown fails
        """
        try:
            await self.on_stop()
            self.active = False
            self.logger.info("Actor stopped successfully")
        except Exception as e:
            self.logger.exception("Failed to stop actor: %s", e)
            raise InitializationError(f"Failed to stop actor {self.name}: {e}") from e

    @abstractmethod
    async def on_start(self) -> None:
        """
        Hook for custom startup logic.

        Override this method to implement custom initialization.
        """
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """
        Hook for custom shutdown logic.

        Override this method to implement custom cleanup.
        """
        pass

    async def handle_message(self, message: dict[str, Any]) -> Any:
        """
        Process incoming messages asynchronously.

        Args:
            message: Message to process

        Returns:
            Any: Processing result

        Raises:
            Exception: If message processing fails
        """
        if not self.active:
            raise RuntimeError(f"Actor {self.name} is not active")

        try:
            result = await self.process_message(message)
            return result
        except Exception as e:
            self.logger.exception("Error handling message: %s", e)
            raise

    @abstractmethod
    async def process_message(self, message: dict[str, Any]) -> Any:
        """
        To be implemented by subclasses for message processing.

        Args:
            message: Message to process

        Returns:
            Any: Processing result
        """
        pass

    def is_active(self) -> bool:
        """
        Check if the actor is active.

        Returns:
            bool: True if actor is active, False otherwise
        """
        return self.active


class LifecycleComponent(ABC):
    """
    Abstract base class for components with lifecycle management.

    Provides a simpler interface for components that don't need
    full actor message handling capabilities.
    """

    def __init__(self, name: str):
        """
        Initialize the component.

        Args:
            name: Unique name for this component
        """
        self.name = name
        self.active: bool = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")

    async def initialize(self) -> None:
        """
        Initialize the component.

        Raises:
            InitializationError: If initialization fails
        """
        try:
            await self.on_initialize()
            self.active = True
            self.logger.info("Component initialized successfully")
        except Exception as e:
            self.logger.exception("Failed to initialize component: %s", e)
            raise InitializationError(
                f"Failed to initialize component {self.name}: {e}"
            ) from e

    async def shutdown(self) -> None:
        """
        Shutdown the component.

        Raises:
            InitializationError: If shutdown fails
        """
        try:
            await self.on_shutdown()
            self.active = False
            self.logger.info("Component shutdown successfully")
        except Exception as e:
            self.logger.exception("Failed to shutdown component: %s", e)
            raise InitializationError(
                f"Failed to shutdown component {self.name}: {e}"
            ) from e

    @abstractmethod
    async def on_initialize(self) -> None:
        """
        Hook for custom initialization logic.
        """
        pass

    @abstractmethod
    async def on_shutdown(self) -> None:
        """
        Hook for custom shutdown logic.
        """
        pass

    def is_active(self) -> bool:
        """
        Check if the component is active.

        Returns:
            bool: True if component is active, False otherwise
        """
        return self.active
