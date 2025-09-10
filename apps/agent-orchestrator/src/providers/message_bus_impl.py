"""
Concrete MessageBus implementation wrapping existing CollaborationMessageBus
"""

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

from ..collaboration.message_bus import CollaborationMessage, CollaborationMessageBus
from ..collaboration.message_bus import MessageType as CollabMessageType
from ..collaboration.message_bus import Priority as CollabPriority
from ..interfaces.message_bus import IMessageBus, Message, MessageType, Priority

logger = logging.getLogger(__name__)


class MessageBusImpl(IMessageBus):
    """
    Concrete implementation of IMessageBus interface.
    Wraps the existing CollaborationMessageBus to provide dependency injection.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        websocket_host: str = "localhost",
        websocket_port: int = 8767,
        enable_fallback: bool = True,
    ):
        """
        Initialize the message bus.

        Args:
            redis_url: Optional Redis URL for pub/sub
            websocket_host: WebSocket server host
            websocket_port: WebSocket server port
            enable_fallback: Enable file-based fallback
        """
        self._bus = CollaborationMessageBus(
            redis_url=redis_url,
            websocket_host=websocket_host,
            websocket_port=websocket_port,
        )
        self._connected = False
        self._subscriptions: Dict[str, Callable] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._subscriber_id = f"subscriber_{uuid.uuid4().hex[:8]}"

    def _convert_message_type(self, msg_type: MessageType) -> CollabMessageType:
        """Convert interface MessageType to CollaborationMessageType"""
        mapping = {
            MessageType.DIRECT: CollabMessageType.DIRECT,
            MessageType.BROADCAST: CollabMessageType.BROADCAST,
            MessageType.COORDINATION: CollabMessageType.COORDINATION,
            MessageType.STATUS_UPDATE: CollabMessageType.STATUS_UPDATE,
            MessageType.ERROR: CollabMessageType.ERROR_NOTIFICATION,
            MessageType.HANDOFF: CollabMessageType.HANDOFF_REQUEST,
        }
        return mapping.get(msg_type, CollabMessageType.BROADCAST)

    def _convert_priority(self, priority: Priority) -> CollabPriority:
        """Convert interface Priority to CollaborationPriority"""
        mapping = {
            Priority.LOW: CollabPriority.LOW,
            Priority.NORMAL: CollabPriority.NORMAL,
            Priority.HIGH: CollabPriority.HIGH,
            Priority.URGENT: CollabPriority.URGENT,
        }
        return mapping.get(priority, CollabPriority.NORMAL)

    def _convert_to_collab_message(self, message: Message) -> CollaborationMessage:
        """Convert interface Message to CollaborationMessage"""
        return CollaborationMessage(
            message_type=self._convert_message_type(message.message_type),
            from_agent=message.sender,
            to_agent=message.recipient,
            payload=message.payload,
            priority=self._convert_priority(message.priority),
            correlation_id=message.correlation_id,
            requires_response=message.requires_response,
        )

    def _convert_from_collab_message(self, collab_msg: CollaborationMessage) -> Message:
        """Convert CollaborationMessage to interface Message"""
        # Reverse mapping for message types
        type_mapping = {
            CollabMessageType.DIRECT: MessageType.DIRECT,
            CollabMessageType.BROADCAST: MessageType.BROADCAST,
            CollabMessageType.COORDINATION: MessageType.COORDINATION,
            CollabMessageType.STATUS_UPDATE: MessageType.STATUS_UPDATE,
            CollabMessageType.ERROR_NOTIFICATION: MessageType.ERROR,
            CollabMessageType.HANDOFF_REQUEST: MessageType.HANDOFF,
            CollabMessageType.HANDOFF_RESPONSE: MessageType.HANDOFF,
        }

        # Reverse mapping for priorities
        priority_mapping = {
            CollabPriority.LOW: Priority.LOW,
            CollabPriority.NORMAL: Priority.NORMAL,
            CollabPriority.HIGH: Priority.HIGH,
            CollabPriority.URGENT: Priority.URGENT,
        }

        return Message(
            message_type=type_mapping.get(
                collab_msg.message_type, MessageType.BROADCAST
            ),
            sender=collab_msg.from_agent,
            recipient=collab_msg.to_agent,
            payload=collab_msg.payload,
            priority=priority_mapping.get(collab_msg.priority, Priority.NORMAL),
            correlation_id=collab_msg.correlation_id,
            requires_response=collab_msg.requires_response,
        )

    async def connect(self) -> None:
        """
        Connect to the message bus.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            await self._bus.start()
            self._connected = True
            logger.info("Connected to message bus")
        except Exception as e:
            logger.error(f"Failed to connect to message bus: {e}")
            raise ConnectionError(f"Message bus connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the message bus."""
        try:
            if self._connected:
                await self._bus.stop()
                self._connected = False
                logger.info("Disconnected from message bus")
        except Exception as e:
            logger.error(f"Error disconnecting from message bus: {e}")

    async def publish(self, message: Message) -> str:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
            ValueError: If message is invalid
        """
        if not self._connected:
            raise RuntimeError("Not connected to message bus")

        try:
            collab_msg = self._convert_to_collab_message(message)

            if message.recipient:
                # Direct message
                await self._bus.send_message(
                    collab_msg.to_agent,
                    collab_msg.payload,
                    message_type=collab_msg.message_type,
                    priority=collab_msg.priority,
                )
            else:
                # Broadcast message
                await self._bus.broadcast(
                    collab_msg.payload,
                    message_type=collab_msg.message_type,
                    priority=collab_msg.priority,
                )

            message_id = collab_msg.message_id
            logger.debug(f"Published message {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise ValueError(f"Failed to publish message: {e}")

    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None],
        subscriber_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to message topics.

        Args:
            topics: List of topics to subscribe to
            handler: Callback function for messages
            subscriber_id: Optional subscriber identifier

        Returns:
            Subscription ID

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected to message bus")

        subscription_id = subscriber_id or f"sub_{uuid.uuid4().hex[:8]}"

        # Wrap handler to convert message types
        async def wrapped_handler(collab_msg: CollaborationMessage):
            message = self._convert_from_collab_message(collab_msg)
            await handler(message)

        # Register handler with the collaboration bus
        for topic in topics:
            # Map topics to message types
            if topic == "direct":
                msg_type = CollabMessageType.DIRECT
            elif topic == "broadcast":
                msg_type = CollabMessageType.BROADCAST
            elif topic == "coordination":
                msg_type = CollabMessageType.COORDINATION
            elif topic == "status":
                msg_type = CollabMessageType.STATUS_UPDATE
            else:
                msg_type = CollabMessageType.BROADCAST

            self._bus.register_handler(msg_type, wrapped_handler)

        self._subscriptions[subscription_id] = handler
        logger.debug(f"Created subscription {subscription_id} for topics {topics}")

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from messages.

        Args:
            subscription_id: Subscription to cancel
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            logger.debug(f"Cancelled subscription {subscription_id}")

    async def send_direct(
        self,
        recipient: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
    ) -> str:
        """
        Send a direct message to a specific recipient.

        Args:
            recipient: Target recipient ID
            payload: Message payload
            priority: Message priority

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
            ValueError: If recipient not found
        """
        message = Message(
            message_type=MessageType.DIRECT,
            sender=self._subscriber_id,
            recipient=recipient,
            payload=payload,
            priority=priority,
        )

        return await self.publish(message)

    async def broadcast(
        self, payload: Dict[str, Any], priority: Priority = Priority.NORMAL
    ) -> str:
        """
        Broadcast a message to all subscribers.

        Args:
            payload: Message payload
            priority: Message priority

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
        """
        message = Message(
            message_type=MessageType.BROADCAST,
            sender=self._subscriber_id,
            recipient=None,
            payload=payload,
            priority=priority,
        )

        return await self.publish(message)

    async def request_response(
        self,
        recipient: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """
        Send a request and wait for response.

        Args:
            recipient: Target recipient ID
            payload: Request payload
            timeout: Response timeout in seconds

        Returns:
            Response message or None if timeout

        Raises:
            RuntimeError: If not connected
            TimeoutError: If no response within timeout
        """
        if not self._connected:
            raise RuntimeError("Not connected to message bus")

        correlation_id = f"req_{uuid.uuid4().hex[:8]}"
        response_future = asyncio.Future()
        self._pending_responses[correlation_id] = response_future

        # Send request
        message = Message(
            message_type=MessageType.DIRECT,
            sender=self._subscriber_id,
            recipient=recipient,
            payload=payload,
            priority=Priority.NORMAL,
            correlation_id=correlation_id,
            requires_response=True,
        )

        await self.publish(message)

        try:
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            del self._pending_responses[correlation_id]
            raise TimeoutError(f"No response received within {timeout} seconds")
        finally:
            if correlation_id in self._pending_responses:
                del self._pending_responses[correlation_id]

    async def get_subscribers(self) -> Set[str]:
        """
        Get list of active subscribers.

        Returns:
            Set of subscriber IDs
        """
        if hasattr(self._bus, "get_active_agents"):
            agents = await self._bus.get_active_agents()
            return set(agents)
        return set(self._subscriptions.keys())

    async def get_metrics(self) -> Dict:
        """
        Get message bus metrics.

        Returns:
            Dictionary containing messaging metrics
        """
        metrics = {
            "connected": self._connected,
            "active_subscriptions": len(self._subscriptions),
            "pending_responses": len(self._pending_responses),
        }

        if hasattr(self._bus, "get_metrics"):
            bus_metrics = await self._bus.get_metrics()
            metrics.update(bus_metrics)

        return metrics

    async def health_check(self) -> bool:
        """
        Check health status of message bus.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._connected:
                return False

            # Try to get metrics as a health check
            metrics = await self.get_metrics()
            return metrics is not None

        except Exception as e:
            logger.error(f"Message bus health check failed: {e}")
            return False
