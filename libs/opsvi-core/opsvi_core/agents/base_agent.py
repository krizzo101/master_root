"""
Base agent implementation for OPSVI Core Library.

Provides the foundation for implementing agents with lifecycle management,
message handling, and plugin support.
"""

import logging
from typing import Any

from ..core.exceptions import InitializationError


class BaseAgent:
    """
    Base class for agents, managing lifecycle, message handling, and plugins.

    Provides a foundation for implementing agents with proper lifecycle management,
    async message processing, and plugin architecture.
    """

    def __init__(self, agent_id: str, plugins: list[Any] | None = None):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent
            plugins: Optional list of plugins to attach to this agent
        """
        self.agent_id = agent_id
        self.plugins = plugins or []
        self.active = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{agent_id}")

    async def activate(self) -> None:
        """
        Activate the agent, initialize resources.

        Raises:
            InitializationError: If activation fails
        """
        try:
            await self._initialize()
            self.active = True
            self.logger.info("Agent activated successfully")
        except Exception as e:
            self.logger.exception("Activation failed for agent: %s", e)
            raise InitializationError(
                f"Activation failed for agent {self.agent_id}: {e}"
            ) from e

    async def deactivate(self) -> None:
        """
        Deactivate the agent, clean up resources.

        Raises:
            InitializationError: If deactivation fails
        """
        try:
            await self._cleanup()
            self.active = False
            self.logger.info("Agent deactivated successfully")
        except Exception as e:
            self.logger.exception("Deactivation failed for agent: %s", e)
            raise InitializationError(
                f"Deactivation failed for agent {self.agent_id}: {e}"
            ) from e

    async def handle(self, message: dict[str, Any]) -> Any:
        """
        Handle incoming messages asynchronously.

        Args:
            message: Message to process

        Returns:
            Any: Processing result

        Raises:
            Exception: If message processing fails
        """
        if not self.active:
            raise RuntimeError(f"Agent {self.agent_id} is not active")

        try:
            response = await self.process(message)
            return response
        except Exception as e:
            self.logger.exception("Error handling message for agent: %s", e)
            raise

    async def _initialize(self) -> None:
        """
        Initialization hook; override as needed.

        Called during agent activation to perform custom initialization.
        """
        pass

    async def _cleanup(self) -> None:
        """
        Cleanup hook; override as needed.

        Called during agent deactivation to perform custom cleanup.
        """
        pass

    async def process(self, message: dict[str, Any]) -> Any:
        """
        Main message processing method; must be overridden.

        Args:
            message: Message to process

        Returns:
            Any: Processing result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            "The 'process' method must be implemented by subclasses."
        )

    def add_plugin(self, plugin: Any) -> None:
        """
        Add a plugin to this agent.

        Args:
            plugin: Plugin to add
        """
        self.plugins.append(plugin)
        self.logger.info("Plugin added to agent: %s", type(plugin).__name__)

    def remove_plugin(self, plugin: Any) -> None:
        """
        Remove a plugin from this agent.

        Args:
            plugin: Plugin to remove
        """
        if plugin in self.plugins:
            self.plugins.remove(plugin)
            self.logger.info("Plugin removed from agent: %s", type(plugin).__name__)

    def get_plugins(self) -> list[Any]:
        """
        Get all plugins attached to this agent.

        Returns:
            List[Any]: List of plugins
        """
        return self.plugins.copy()

    def is_active(self) -> bool:
        """
        Check if the agent is active.

        Returns:
            bool: True if agent is active, False otherwise
        """
        return self.active
