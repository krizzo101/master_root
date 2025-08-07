"""
Base agent implementation.

Provides foundational agent lifecycle, state management, and communication.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from opsvi_foundation import (
    BaseComponent,
    RetryConfig,
    get_logger,
    retry,
)
from pydantic import BaseModel, Field

from ..core.exceptions import AgentError

logger = get_logger(__name__)


class AgentState(str, Enum):
    """Agent lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AgentCapability(BaseModel):
    """Agent capability definition."""

    name: str = Field(..., description="Capability name")
    version: str = Field(default="1.0.0", description="Capability version")
    description: str = Field(default="", description="Capability description")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Capability parameters"
    )


class AgentMetadata(BaseModel):
    """Agent metadata and configuration."""

    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Agent name")
    version: str = Field(default="1.0.0", description="Agent version")
    description: str = Field(default="", description="Agent description")
    capabilities: list[AgentCapability] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message structure for agent communication."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = Field(..., description="Sender agent ID")
    recipient_id: str | None = Field(default=None, description="Recipient agent ID")
    message_type: str = Field(..., description="Message type")
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=lambda: asyncio.get_event_loop().time())


class BaseAgent(BaseComponent, ABC):
    """Base agent with lifecycle management and communication.

    Provides:
    - Async lifecycle management (initialize, start, stop, cleanup)
    - State tracking and transitions
    - Message handling and communication
    - Capability registration and discovery
    - Error handling and recovery
    """

    def __init__(self, metadata: AgentMetadata):
        super().__init__()
        self.metadata = metadata
        self.state = AgentState.CREATED
        self._message_handlers: dict[str, callable] = {}
        self._plugins: dict[str, Any] = {}
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "uptime": 0.0,
        }

        logger.info(
            "Agent created", agent_id=self.metadata.agent_id, name=self.metadata.name
        )

    async def _initialize(self) -> None:
        """Initialize the agent."""
        self.state = AgentState.INITIALIZING

        try:
            await self.setup()
            self.state = AgentState.READY

            logger.info(
                "Agent initialized",
                agent_id=self.metadata.agent_id,
                capabilities=len(self.metadata.capabilities),
            )

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(
                "Agent initialization failed",
                agent_id=self.metadata.agent_id,
                error=str(e),
            )
            raise AgentError(f"Agent initialization failed: {e}")

    async def _start(self) -> None:
        """Start the agent."""
        if self.state != AgentState.READY:
            raise AgentError(f"Cannot start agent in state {self.state}")

        self.state = AgentState.RUNNING

        try:
            await self.run()

            logger.info("Agent started", agent_id=self.metadata.agent_id)

        except Exception as e:
            self.state = AgentState.ERROR
            self._stats["errors"] += 1
            logger.error(
                "Agent start failed", agent_id=self.metadata.agent_id, error=str(e)
            )
            raise AgentError(f"Agent start failed: {e}")

    async def _stop(self) -> None:
        """Stop the agent."""
        if self.state not in [AgentState.RUNNING, AgentState.PAUSED]:
            logger.warning(
                "Attempting to stop agent not in running state",
                agent_id=self.metadata.agent_id,
                state=self.state,
            )
            return

        self.state = AgentState.STOPPING

        try:
            await self.teardown()
            self.state = AgentState.STOPPED

            logger.info("Agent stopped", agent_id=self.metadata.agent_id)

        except Exception as e:
            self.state = AgentState.ERROR
            self._stats["errors"] += 1
            logger.error(
                "Agent stop failed", agent_id=self.metadata.agent_id, error=str(e)
            )
            raise AgentError(f"Agent stop failed: {e}")

    async def _cleanup(self) -> None:
        """Cleanup agent resources."""
        try:
            await self.cleanup_resources()
            logger.info("Agent cleanup completed", agent_id=self.metadata.agent_id)

        except Exception as e:
            logger.error(
                "Agent cleanup failed", agent_id=self.metadata.agent_id, error=str(e)
            )
            raise AgentError(f"Agent cleanup failed: {e}")

    @abstractmethod
    async def setup(self) -> None:
        """Agent-specific setup logic.

        Override this method to implement custom initialization.
        """
        pass

    @abstractmethod
    async def run(self) -> None:
        """Agent-specific run logic.

        Override this method to implement the main agent loop.
        """
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Agent-specific teardown logic.

        Override this method to implement custom cleanup.
        """
        pass

    async def cleanup_resources(self) -> None:
        """Cleanup agent resources.

        Override this method to implement custom resource cleanup.
        """
        pass

    async def pause(self) -> None:
        """Pause the agent."""
        if self.state != AgentState.RUNNING:
            raise AgentError(f"Cannot pause agent in state {self.state}")

        self.state = AgentState.PAUSED
        logger.info("Agent paused", agent_id=self.metadata.agent_id)

    async def resume(self) -> None:
        """Resume the agent."""
        if self.state != AgentState.PAUSED:
            raise AgentError(f"Cannot resume agent in state {self.state}")

        self.state = AgentState.RUNNING
        logger.info("Agent resumed", agent_id=self.metadata.agent_id)

    @retry(RetryConfig(max_attempts=3))
    async def send_message(self, message: AgentMessage) -> None:
        """Send message to another agent.

        Args:
            message: Message to send

        Raises:
            AgentError: If message sending fails
        """
        try:
            await self.deliver_message(message)
            self._stats["messages_sent"] += 1

            logger.debug(
                "Message sent",
                agent_id=self.metadata.agent_id,
                message_id=message.message_id,
                recipient=message.recipient_id,
            )

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(
                "Failed to send message",
                agent_id=self.metadata.agent_id,
                message_id=message.message_id,
                error=str(e),
            )
            raise AgentError(f"Failed to send message: {e}")

    async def receive_message(self, message: AgentMessage) -> None:
        """Receive and process a message.

        Args:
            message: Received message
        """
        self._stats["messages_received"] += 1

        logger.debug(
            "Message received",
            agent_id=self.metadata.agent_id,
            message_id=message.message_id,
            sender=message.sender_id,
            message_type=message.message_type,
        )

        try:
            handler = self._message_handlers.get(message.message_type)

            if handler:
                await handler(message)
            else:
                await self.handle_unknown_message(message)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(
                "Message processing failed",
                agent_id=self.metadata.agent_id,
                message_id=message.message_id,
                error=str(e),
            )

    def register_message_handler(self, message_type: str, handler: callable) -> None:
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self._message_handlers[message_type] = handler
        logger.debug(
            "Message handler registered",
            agent_id=self.metadata.agent_id,
            message_type=message_type,
        )

    def add_capability(self, capability: AgentCapability) -> None:
        """Add a capability to the agent.

        Args:
            capability: Capability to add
        """
        self.metadata.capabilities.append(capability)
        logger.info(
            "Capability added",
            agent_id=self.metadata.agent_id,
            capability=capability.name,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get agent statistics.

        Returns:
            Dictionary of agent statistics
        """
        return {
            **self._stats,
            "state": self.state.value,
            "capabilities": len(self.metadata.capabilities),
            "plugins": len(self._plugins),
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform agent health check.

        Returns:
            Health status information
        """
        return {
            "agent_id": self.metadata.agent_id,
            "name": self.metadata.name,
            "state": self.state.value,
            "healthy": self.state in [AgentState.READY, AgentState.RUNNING],
            "stats": self.get_stats(),
        }

    async def deliver_message(self, message: AgentMessage) -> None:
        """Deliver message to recipient.

        Override this method to implement custom message delivery.

        Args:
            message: Message to deliver
        """
        # Default implementation - override in subclasses
        logger.debug(
            "Message delivery not implemented", agent_id=self.metadata.agent_id
        )

    async def handle_unknown_message(self, message: AgentMessage) -> None:
        """Handle unknown message types.

        Override this method to implement custom unknown message handling.

        Args:
            message: Unknown message
        """
        logger.warning(
            "Unknown message type",
            agent_id=self.metadata.agent_id,
            message_type=message.message_type,
            message_id=message.message_id,
        )
