"""
Message broker for inter-agent communication.

Provides reliable message passing, broadcasting, and subscription
mechanisms for agents to communicate and coordinate.
"""

import asyncio
import logging
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from ..common.types import CommunicationError, Message, MessageType

logger = logging.getLogger(__name__)


class MessageBroker:
    """
    Centralized message broker for inter-agent communication.

    Supports point-to-point messaging, broadcasting, and subscription-based
    message routing with delivery guarantees and error handling.
    """

    def __init__(self, max_queue_size: int = 1000, message_ttl: int = 3600):
        """
        Initialize the message broker.

        Args:
            max_queue_size: Maximum messages per agent queue
            message_ttl: Message time-to-live in seconds
        """
        self._agent_queues: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_queue_size)
        )
        self._subscribers: dict[MessageType, set[str]] = defaultdict(set)
        self._message_handlers: dict[str, Callable] = {}
        self._message_history: deque = deque(maxlen=10000)
        self._max_queue_size = max_queue_size
        self._message_ttl = message_ttl
        self._running = False
        self._cleanup_task: asyncio.Task | None = None

        logger.info("MessageBroker initialized")

    async def start(self) -> None:
        """Start the message broker and cleanup task."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        logger.info("MessageBroker started")

    async def stop(self) -> None:
        """Stop the message broker and cleanup task."""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("MessageBroker stopped")

    def register_agent(
        self, agent_id: str, message_handler: Callable | None = None
    ) -> None:
        """
        Register an agent with the message broker.

        Args:
            agent_id: Unique agent identifier
            message_handler: Optional async function to handle messages
        """
        if agent_id not in self._agent_queues:
            self._agent_queues[agent_id] = deque(maxlen=self._max_queue_size)

        if message_handler:
            self._message_handlers[agent_id] = message_handler

        logger.info(f"Agent {agent_id} registered with MessageBroker")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the message broker.

        Args:
            agent_id: Agent identifier to unregister
        """
        if agent_id in self._agent_queues:
            del self._agent_queues[agent_id]

        if agent_id in self._message_handlers:
            del self._message_handlers[agent_id]

        # Remove from all subscriptions
        for subscribers in self._subscribers.values():
            subscribers.discard(agent_id)

        logger.info(f"Agent {agent_id} unregistered from MessageBroker")

    async def send_message(self, message: Message) -> bool:
        """
        Send a message to a specific agent.

        Args:
            message: Message to send

        Returns:
            True if message was queued successfully, False otherwise
        """
        try:
            if not message.recipient_id:
                raise CommunicationError("Recipient ID required for direct messages")

            if message.recipient_id not in self._agent_queues:
                logger.warning(f"Recipient {message.recipient_id} not registered")
                return False

            # Add to recipient's queue
            self._agent_queues[message.recipient_id].append(message)

            # Add to message history
            self._message_history.append(message)

            # Try to deliver immediately if handler exists
            if message.recipient_id in self._message_handlers:
                handler = self._message_handlers[message.recipient_id]
                asyncio.create_task(self._safe_deliver_message(handler, message))

            logger.debug(
                f"Message {message.id} sent from {message.sender_id} "
                f"to {message.recipient_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send message {message.id}: {e}")
            raise CommunicationError(f"Failed to send message: {e}")

    async def broadcast_message(
        self, message: Message, exclude_sender: bool = True
    ) -> int:
        """
        Broadcast a message to all registered agents.

        Args:
            message: Message to broadcast
            exclude_sender: Whether to exclude the sender from broadcast

        Returns:
            Number of agents the message was sent to
        """
        try:
            recipients = set(self._agent_queues.keys())

            if exclude_sender and message.sender_id in recipients:
                recipients.remove(message.sender_id)

            sent_count = 0
            for recipient_id in recipients:
                # Create a copy of the message with specific recipient
                msg_copy = Message(
                    id=message.id,
                    sender_id=message.sender_id,
                    recipient_id=recipient_id,
                    message_type=message.message_type,
                    content=message.content.copy(),
                    timestamp=message.timestamp,
                    correlation_id=message.correlation_id,
                )

                self._agent_queues[recipient_id].append(msg_copy)

                # Try immediate delivery
                if recipient_id in self._message_handlers:
                    handler = self._message_handlers[recipient_id]
                    asyncio.create_task(self._safe_deliver_message(handler, msg_copy))

                sent_count += 1

            # Add to message history
            self._message_history.append(message)

            logger.debug(f"Message {message.id} broadcast to {sent_count} agents")
            return sent_count

        except Exception as e:
            logger.error(f"Failed to broadcast message {message.id}: {e}")
            raise CommunicationError(f"Failed to broadcast message: {e}")

    def subscribe_to_message_type(
        self, agent_id: str, message_type: MessageType
    ) -> None:
        """
        Subscribe an agent to a specific message type.

        Args:
            agent_id: Agent identifier
            message_type: Type of messages to subscribe to
        """
        self._subscribers[message_type].add(agent_id)
        logger.debug(f"Agent {agent_id} subscribed to {message_type.value}")

    def unsubscribe_from_message_type(
        self, agent_id: str, message_type: MessageType
    ) -> None:
        """
        Unsubscribe an agent from a specific message type.

        Args:
            agent_id: Agent identifier
            message_type: Type of messages to unsubscribe from
        """
        self._subscribers[message_type].discard(agent_id)
        logger.debug(f"Agent {agent_id} unsubscribed from {message_type.value}")

    async def receive_messages(
        self, agent_id: str, max_messages: int = 10
    ) -> list[Message]:
        """
        Retrieve messages for a specific agent.

        Args:
            agent_id: Agent identifier
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of messages for the agent
        """
        if agent_id not in self._agent_queues:
            return []

        messages = []
        queue = self._agent_queues[agent_id]

        for _ in range(min(max_messages, len(queue))):
            if queue:
                messages.append(queue.popleft())

        logger.debug(f"Retrieved {len(messages)} messages for agent {agent_id}")
        return messages

    def get_queue_size(self, agent_id: str) -> int:
        """
        Get the number of queued messages for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Number of queued messages
        """
        return len(self._agent_queues.get(agent_id, []))

    def get_registered_agents(self) -> list[str]:
        """
        Get list of all registered agents.

        Returns:
            List of agent IDs
        """
        return list(self._agent_queues.keys())

    def get_message_history(self, limit: int = 100) -> list[Message]:
        """
        Get recent message history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return list(self._message_history)[-limit:]

    async def _safe_deliver_message(self, handler: Callable, message: Message) -> None:
        """
        Safely deliver a message to a handler with error handling.

        Args:
            handler: Message handler function
            message: Message to deliver
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
        except Exception as e:
            logger.error(f"Error delivering message {message.id} to handler: {e}")

    async def _cleanup_expired_messages(self) -> None:
        """Background task to clean up expired messages."""
        while self._running:
            try:
                cutoff_time = datetime.now() - timedelta(seconds=self._message_ttl)

                # Clean up message history
                while (
                    self._message_history
                    and self._message_history[0].timestamp < cutoff_time
                ):
                    self._message_history.popleft()

                # Clean up agent queues
                for agent_id, queue in self._agent_queues.items():
                    expired_count = 0
                    while queue and queue[0].timestamp < cutoff_time:
                        queue.popleft()
                        expired_count += 1

                    if expired_count > 0:
                        logger.debug(
                            f"Cleaned up {expired_count} expired messages "
                            f"for agent {agent_id}"
                        )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in message cleanup: {e}")
                await asyncio.sleep(60)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get message broker statistics.

        Returns:
            Dictionary containing broker statistics
        """
        total_queued = sum(len(queue) for queue in self._agent_queues.values())

        return {
            "registered_agents": len(self._agent_queues),
            "total_queued_messages": total_queued,
            "message_history_size": len(self._message_history),
            "subscription_count": sum(len(subs) for subs in self._subscribers.values()),
            "running": self._running,
            "max_queue_size": self._max_queue_size,
            "message_ttl": self._message_ttl,
        }
