"""
Message Bus for Multi-Agent System

Provides asynchronous message passing, event distribution, and communication
coordination for the AI-Powered Development Workflow System agents.

Author: AI Agent System
Created: 2025-01-27
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from uuid import uuid4

from ..agents.base_agent import AgentMessage, MessageType


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SubscriptionType(Enum):
    """Message subscription types."""

    DIRECT = "direct"  # Messages to specific agent
    BROADCAST = "broadcast"  # Messages to all agents
    TOPIC = "topic"  # Messages on specific topic
    TYPE = "type"  # Messages of specific type


@dataclass
class MessageEnvelope:
    """Message envelope with routing and metadata."""

    message: AgentMessage
    priority: MessagePriority = MessagePriority.NORMAL
    topic: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    max_attempts: int = 3
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return (
            self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at
        )


@dataclass
class Subscription:
    """Message subscription information."""

    subscriber_id: str
    subscription_type: SubscriptionType
    handler: Callable[[AgentMessage], Any]
    filter_criteria: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0


class MessageBus:
    """
    Asynchronous message bus for inter-agent communication.

    Provides message routing, topic-based publishing, direct messaging,
    and subscription management for the multi-agent system.
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize message bus.

        Args:
            max_queue_size: Maximum number of messages in queue
        """
        self.logger = logging.getLogger(__name__)
        self.max_queue_size = max_queue_size

        # Message queues by priority
        self._priority_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in MessagePriority
        }

        # Subscriptions
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._topic_subscriptions: Dict[str, List[Subscription]] = {}
        self._type_subscriptions: Dict[MessageType, List[Subscription]] = {}
        self._broadcast_subscriptions: List[Subscription] = []

        # Processing state
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_expired": 0,
        }

        self.logger.info("Message bus initialized")

    async def start(self) -> None:
        """Start message bus processing."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        self.logger.info("Message bus started")

    async def stop(self) -> None:
        """Stop message bus processing."""
        if not self._running:
            return

        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Clear all queues
        for queue in self._priority_queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        self.logger.info("Message bus stopped")

    async def send_message(
        self,
        message: AgentMessage,
        priority: MessagePriority = MessagePriority.NORMAL,
        topic: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> bool:
        """
        Send a message through the bus.

        Args:
            message: Message to send
            priority: Message priority
            topic: Optional topic for topic-based routing
            expires_in: Optional expiration time in seconds

        Returns:
            True if message was queued, False otherwise
        """
        if not self._running:
            self.logger.warning("Message bus not running, dropping message")
            return False

        # Create envelope
        envelope = MessageEnvelope(message=message, priority=priority, topic=topic)

        if expires_in:
            envelope.expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in
            )

        # Queue message
        try:
            queue = self._priority_queues[priority]
            queue.put_nowait(envelope)
            self._stats["messages_sent"] += 1

            self.logger.debug(
                f"Message queued: {message.type.value} "
                f"from {message.sender_id} to {message.recipient_id}"
            )
            return True

        except asyncio.QueueFull:
            self.logger.warning(f"Message queue full for priority {priority.value}")
            self._stats["messages_failed"] += 1
            return False

    async def broadcast_message(
        self,
        message: AgentMessage,
        priority: MessagePriority = MessagePriority.NORMAL,
        topic: Optional[str] = None,
    ) -> int:
        """
        Broadcast a message to all subscribers.

        Args:
            message: Message to broadcast
            priority: Message priority
            topic: Optional topic filter

        Returns:
            Number of subscribers that received the message
        """
        # Send to broadcast subscribers
        delivered_count = 0

        for subscription in self._broadcast_subscriptions:
            if await self._deliver_to_subscription(message, subscription):
                delivered_count += 1

        # Send to topic subscribers if topic specified
        if topic and topic in self._topic_subscriptions:
            for subscription in self._topic_subscriptions[topic]:
                if await self._deliver_to_subscription(message, subscription):
                    delivered_count += 1

        self._stats["messages_delivered"] += delivered_count

        self.logger.debug(
            f"Broadcast message delivered to {delivered_count} subscribers"
        )
        return delivered_count

    def subscribe(
        self,
        subscriber_id: str,
        subscription_type: SubscriptionType,
        handler: Callable[[AgentMessage], Any],
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Subscribe to messages.

        Args:
            subscriber_id: ID of subscribing agent
            subscription_type: Type of subscription
            handler: Message handler function
            filter_criteria: Optional filter criteria

        Returns:
            Subscription ID
        """
        subscription = Subscription(
            subscriber_id=subscriber_id,
            subscription_type=subscription_type,
            handler=handler,
            filter_criteria=filter_criteria or {},
        )

        subscription_id = str(uuid4())

        # Store subscription by type
        if subscription_type == SubscriptionType.DIRECT:
            if subscriber_id not in self._subscriptions:
                self._subscriptions[subscriber_id] = []
            self._subscriptions[subscriber_id].append(subscription)

        elif subscription_type == SubscriptionType.BROADCAST:
            self._broadcast_subscriptions.append(subscription)

        elif subscription_type == SubscriptionType.TOPIC:
            topic = filter_criteria.get("topic")
            if topic:
                if topic not in self._topic_subscriptions:
                    self._topic_subscriptions[topic] = []
                self._topic_subscriptions[topic].append(subscription)

        elif subscription_type == SubscriptionType.TYPE:
            message_type = filter_criteria.get("message_type")
            if message_type:
                if message_type not in self._type_subscriptions:
                    self._type_subscriptions[message_type] = []
                self._type_subscriptions[message_type].append(subscription)

        self.logger.info(
            f"Subscription created: {subscription_type.value} for {subscriber_id}"
        )

        return subscription_id

    def unsubscribe(
        self, subscriber_id: str, subscription_type: SubscriptionType
    ) -> bool:
        """
        Unsubscribe from messages.

        Args:
            subscriber_id: ID of subscribing agent
            subscription_type: Type of subscription to remove

        Returns:
            True if subscription was removed, False otherwise
        """
        removed = False

        if subscription_type == SubscriptionType.DIRECT:
            if subscriber_id in self._subscriptions:
                del self._subscriptions[subscriber_id]
                removed = True

        elif subscription_type == SubscriptionType.BROADCAST:
            self._broadcast_subscriptions = [
                sub
                for sub in self._broadcast_subscriptions
                if sub.subscriber_id != subscriber_id
            ]
            removed = True

        elif subscription_type == SubscriptionType.TOPIC:
            for topic_subs in self._topic_subscriptions.values():
                topic_subs[:] = [
                    sub for sub in topic_subs if sub.subscriber_id != subscriber_id
                ]
            removed = True

        elif subscription_type == SubscriptionType.TYPE:
            for type_subs in self._type_subscriptions.values():
                type_subs[:] = [
                    sub for sub in type_subs if sub.subscriber_id != subscriber_id
                ]
            removed = True

        if removed:
            self.logger.info(
                f"Subscription removed: {subscription_type.value} for {subscriber_id}"
            )

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dictionary with statistics
        """
        queue_sizes = {
            priority.value: queue.qsize()
            for priority, queue in self._priority_queues.items()
        }

        return {
            **self._stats,
            "queue_sizes": queue_sizes,
            "total_subscriptions": (
                len(self._subscriptions)
                + len(self._broadcast_subscriptions)
                + sum(len(subs) for subs in self._topic_subscriptions.values())
                + sum(len(subs) for subs in self._type_subscriptions.values())
            ),
            "running": self._running,
        }

    async def _process_messages(self) -> None:
        """Process messages from priority queues."""
        while self._running:
            try:
                # Process messages by priority (highest first)
                envelope = None

                for priority in sorted(
                    MessagePriority, key=lambda p: p.value, reverse=True
                ):
                    queue = self._priority_queues[priority]
                    try:
                        envelope = queue.get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue

                if envelope is None:
                    # No messages available, wait briefly
                    await asyncio.sleep(0.1)
                    continue

                # Check if message has expired
                if envelope.is_expired:
                    self._stats["messages_expired"] += 1
                    self.logger.debug(
                        f"Message expired, dropping. Expires at: {envelope.expires_at}, Current time: {datetime.now(timezone.utc)}"
                    )
                    continue
                else:
                    self.logger.debug(
                        f"Message not expired. Expires at: {envelope.expires_at}, Current time: {datetime.now(timezone.utc)}"
                    )

                # Process message
                await self._route_message(envelope)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                await asyncio.sleep(1)

    async def _route_message(self, envelope: MessageEnvelope) -> None:
        """Route message to appropriate subscribers."""
        message = envelope.message
        delivered = False

        try:
            # Route to direct recipient
            if message.recipient_id and message.recipient_id in self._subscriptions:
                for subscription in self._subscriptions[message.recipient_id]:
                    if await self._deliver_to_subscription(message, subscription):
                        delivered = True

            # Route by message type
            if message.type in self._type_subscriptions:
                for subscription in self._type_subscriptions[message.type]:
                    if await self._deliver_to_subscription(message, subscription):
                        delivered = True

            # Route by topic
            if envelope.topic and envelope.topic in self._topic_subscriptions:
                for subscription in self._topic_subscriptions[envelope.topic]:
                    if await self._deliver_to_subscription(message, subscription):
                        delivered = True

            if delivered:
                self._stats["messages_delivered"] += 1
            else:
                self.logger.debug(f"No subscribers for message {message.type.value}")

        except Exception as e:
            self.logger.error(f"Message routing error: {e}")
            self._stats["messages_failed"] += 1

    async def _deliver_to_subscription(
        self, message: AgentMessage, subscription: Subscription
    ) -> bool:
        """
        Deliver message to a subscription.

        Args:
            message: Message to deliver
            subscription: Subscription to deliver to

        Returns:
            True if delivered successfully, False otherwise
        """
        try:
            # Check filter criteria
            if not self._message_matches_filter(message, subscription.filter_criteria):
                return False

            # Call handler
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(message)
            else:
                subscription.handler(message)

            subscription.message_count += 1
            return True

        except Exception as e:
            self.logger.error(
                f"Error delivering message to {subscription.subscriber_id}: {e}"
            )
            return False

    def _message_matches_filter(
        self, message: AgentMessage, filter_criteria: Dict[str, Any]
    ) -> bool:
        """
        Check if message matches filter criteria.

        Args:
            message: Message to check
            filter_criteria: Filter criteria

        Returns:
            True if message matches, False otherwise
        """
        for key, value in filter_criteria.items():
            if key == "sender_id" and message.sender_id != value:
                return False
            elif key == "message_type" and message.type != value:
                return False
            elif key == "topic" and message.metadata.get("topic") != value:
                return False
            elif key in message.metadata and message.metadata[key] != value:
                return False

        return True

    async def _cleanup_expired_messages(self) -> None:
        """Periodically clean up expired messages from queues."""
        while self._running:
            try:
                await asyncio.sleep(0.05)  # Check every 50ms

                for priority, queue in self._priority_queues.items():
                    # Create a temporary list to hold non-expired messages
                    temp_messages = []

                    # Check all messages in the queue
                    while not queue.empty():
                        try:
                            envelope = queue.get_nowait()
                            if envelope.is_expired:
                                self._stats["messages_expired"] += 1
                                self.logger.debug(
                                    f"Expired message removed from {priority.value} queue"
                                )
                            else:
                                temp_messages.append(envelope)
                        except asyncio.QueueEmpty:
                            break

                    # Put non-expired messages back in the queue
                    for envelope in temp_messages:
                        try:
                            queue.put_nowait(envelope)
                        except asyncio.QueueFull:
                            # If queue is full, drop the message
                            self._stats["messages_failed"] += 1
                            self.logger.warning(
                                f"Dropped message due to full queue: {priority.value}"
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message cleanup error: {e}")
                await asyncio.sleep(1)


# Global message bus instance
_message_bus_instance: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get the global message bus instance."""
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()
    return _message_bus_instance


async def initialize_message_bus() -> MessageBus:
    """Initialize and start the global message bus."""
    bus = get_message_bus()
    await bus.start()
    return bus


async def shutdown_message_bus() -> None:
    """Shutdown the global message bus."""
    global _message_bus_instance
    if _message_bus_instance:
        await _message_bus_instance.stop()
        _message_bus_instance = None
