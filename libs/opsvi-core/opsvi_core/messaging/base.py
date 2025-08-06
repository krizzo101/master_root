"""
Base messaging infrastructure for OPSVI Core.

Provides abstract message broker interface, message types, and routing mechanisms.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger

logger = get_logger(__name__)


class MessagingError(ComponentError):
    """Raised when messaging operations fail."""

    pass


class QoSLevel(str, Enum):
    """Quality of Service levels for message delivery."""

    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class MessageRoute:
    """Message routing information."""

    source: str
    destination: str | None = None
    topic: str | None = None
    exchange: str | None = None
    routing_key: str | None = None


@dataclass
class Message:
    """Message structure for inter-agent communication."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any] = field(default_factory=dict)
    route: MessageRoute = field(default_factory=lambda: MessageRoute(source="unknown"))
    qos: QoSLevel = QoSLevel.AT_LEAST_ONCE
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str | None = None
    reply_to: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    encrypted: bool = False


class MessageBroker(BaseComponent, ABC):
    """Abstract message broker interface.

    Provides pub/sub messaging capabilities with support for:
    - Topic-based publishing and subscription
    - Quality of Service levels
    - Message encryption and authentication
    - Retry and dead letter handling
    """

    RETRY_DELAY = 1.0  # seconds

    def __init__(self, *, encryption_key: bytes | None = None):
        super().__init__()
        self.encryption_key = encryption_key
        self._subscribers: dict[str, list[Callable]] = {}

    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message to a topic."""
        pass

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        *,
        callback: Callable[[Message], Any],
        group: str | None = None,
    ) -> None:
        """Subscribe to messages on a topic."""
        pass

    def _encrypt_if_needed(self, message: Message) -> None:
        """Encrypt message payload if encryption is enabled."""
        if self.encryption_key and not message.encrypted:
            # TODO: Implement encryption
            message.encrypted = True

    def _decrypt_if_needed(self, message: Message) -> None:
        """Decrypt message payload if encrypted."""
        if self.encryption_key and message.encrypted:
            # TODO: Implement decryption
            message.encrypted = False


class MessageRouter(BaseComponent):
    """Message routing and delivery management."""

    def __init__(self):
        super().__init__()
        self._routes: dict[str, str] = {}
        self._broker: MessageBroker | None = None

    def set_broker(self, broker: MessageBroker) -> None:
        """Set the message broker for routing."""
        self._broker = broker

    def add_route(self, pattern: str, destination: str) -> None:
        """Add a routing pattern."""
        self._routes[pattern] = destination
        logger.info("Added route: %s -> %s", pattern, destination)

    async def route_message(self, message: Message) -> None:
        """Route a message based on its destination."""
        if not self._broker:
            raise MessagingError("No broker configured")

        destination = self._routes.get(
            message.route.destination, message.route.destination
        )
        if destination:
            message.route.destination = destination
            await self._broker.publish(message)
        else:
            logger.warning(
                "No route found for destination: %s", message.route.destination
            )


class MessageQueue(BaseComponent):
    """Message queue with persistence and retry logic."""

    def __init__(self, broker: MessageBroker, max_retries: int = 3):
        super().__init__()
        self.broker = broker
        self.max_retries = max_retries
        self._pending: dict[str, Message] = {}
        self._retry_counts: dict[str, int] = {}

    async def enqueue(self, message: Message) -> None:
        """Add message to queue."""
        self._pending[message.message_id] = message
        self._retry_counts[message.message_id] = 0
        await self._process_message(message)

    async def _process_message(self, message: Message) -> None:
        """Process a message with retry logic."""
        try:
            await self.broker.publish(message)
            self._pending.pop(message.message_id, None)
            self._retry_counts.pop(message.message_id, None)
        except Exception as e:
            retry_count = self._retry_counts.get(message.message_id, 0)
            if retry_count < self.max_retries:
                self._retry_counts[message.message_id] = retry_count + 1
                logger.warning(
                    "Message %s failed, retrying (%d/%d): %s",
                    message.message_id,
                    retry_count + 1,
                    self.max_retries,
                    str(e),
                )
                await asyncio.sleep(self.broker.RETRY_DELAY * (retry_count + 1))
                await self._process_message(message)
            else:
                logger.error(
                    "Message %s failed after %d retries, moving to dead letter",
                    message.message_id,
                    self.max_retries,
                )
                await self._move_to_dead_letter(message)

    async def _move_to_dead_letter(self, message: Message) -> None:
        """Move failed message to dead letter queue."""
        # TODO: Implement dead letter queue
        self._pending.pop(message.message_id, None)
        self._retry_counts.pop(message.message_id, None)
