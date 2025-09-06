#!/usr/bin/env python3
"""
Simplified Agent Message Client SDK

High-level, easy-to-use client for agents to connect and communicate via the message bus.
Provides simple methods for common messaging patterns while abstracting away complexity.

Usage:
    from src.message_bus.simple_client import SimpleMessageClient

    async def main():
        client = SimpleMessageClient("my_agent_id")
        await client.connect()

        # Send direct message
        await client.send_to_agent("other_agent", {"action": "process_data", "data": [1,2,3]})

        # Broadcast to all agents
        await client.broadcast({"announcement": "Hello everyone!"})

        # Subscribe to topics
        await client.subscribe_topic("alerts", handle_alert)

        await client.disconnect()
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .client.agent_client import AgentClientConfig, AgentMessageClient
from .core.message_types import Message, MessagePriority, MessageType

logger = logging.getLogger(__name__)


@dataclass
class MessageResponse:
    """Response wrapper for sent messages"""

    success: bool
    message_id: str
    error: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class SimpleMessageClient:
    """Simplified client interface for agent communication"""

    def __init__(
        self,
        agent_id: str,
        websocket_url: str = "ws://localhost:8767",
        capabilities: Optional[List[str]] = None,
        auto_reconnect: bool = True,
    ):
        """
        Initialize simple message client

        Args:
            agent_id: Unique identifier for this agent
            websocket_url: WebSocket URL for message bus server
            capabilities: List of agent capabilities for routing
            auto_reconnect: Whether to automatically reconnect on disconnect
        """
        self.agent_id = agent_id
        self.capabilities = capabilities or []

        # Configure underlying client
        config = AgentClientConfig(
            agent_id=agent_id,
            websocket_url=websocket_url,
            capabilities=self.capabilities,
            auto_reconnect=auto_reconnect,
            reconnect_delay_seconds=2,
            max_reconnect_attempts=10,
            heartbeat_interval_seconds=30,
        )

        self._client = AgentMessageClient(config)
        self._connected = False

        # Message handling
        self._message_handlers: Dict[str, Callable] = {}
        self._topic_handlers: Dict[str, Callable] = {}
        self._group_handlers: Dict[str, Callable] = {}

        # Setup default message router
        self._client.register_default_handler(self._route_incoming_message)

        logger.info(f"SimpleMessageClient initialized for agent: {agent_id}")

    async def connect(self) -> bool:
        """Connect to the message bus server"""
        try:
            success = await self._client.connect()
            if success:
                self._connected = True
                logger.info(f"Agent {self.agent_id} connected successfully")
                return True
            else:
                logger.error(f"Failed to connect agent {self.agent_id}")
                return False
        except Exception as e:
            logger.error(f"Connection error for agent {self.agent_id}: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the message bus server"""
        try:
            await self._client.disconnect()
            self._connected = False
            logger.info(f"Agent {self.agent_id} disconnected")
        except Exception as e:
            logger.error(f"Disconnect error for agent {self.agent_id}: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client.is_connected

    # === SENDING MESSAGES ===

    async def send_to_agent(
        self,
        recipient_id: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_ack: bool = False,
        timeout_seconds: int = 30,
    ) -> MessageResponse:
        """
        Send direct message to specific agent

        Args:
            recipient_id: ID of target agent
            data: Message payload
            priority: Message priority level
            requires_ack: Whether delivery confirmation is required
            timeout_seconds: Timeout for response

        Returns:
            MessageResponse indicating success/failure
        """
        if not self.is_connected:
            return MessageResponse(False, "", "Not connected to message bus")

        try:
            message = Message(
                message_type=MessageType.POINT_TO_POINT,
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                payload=data,
                priority=priority,
                requires_ack=requires_ack,
            )

            success = await self._client.send_message(message)

            if success:
                return MessageResponse(True, message.message_id)
            else:
                return MessageResponse(
                    False, message.message_id, "Failed to send message"
                )

        except Exception as e:
            logger.error(f"Error sending message to {recipient_id}: {e}")
            return MessageResponse(False, "", str(e))

    async def broadcast(
        self,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        required_capabilities: Optional[List[str]] = None,
    ) -> MessageResponse:
        """
        Broadcast message to all connected agents

        Args:
            data: Message payload
            priority: Message priority level
            required_capabilities: Filter by agent capabilities

        Returns:
            MessageResponse indicating success/failure
        """
        if not self.is_connected:
            return MessageResponse(False, "", "Not connected to message bus")

        try:
            payload = data.copy()
            if required_capabilities:
                payload["required_capabilities"] = required_capabilities

            message = Message(
                message_type=MessageType.BROADCAST,
                sender_id=self.agent_id,
                payload=payload,
                priority=priority,
            )

            success = await self._client.send_message(message)

            if success:
                return MessageResponse(True, message.message_id)
            else:
                return MessageResponse(
                    False, message.message_id, "Failed to broadcast message"
                )

        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return MessageResponse(False, "", str(e))

    async def send_to_topic(
        self,
        topic: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> MessageResponse:
        """
        Send message to topic subscribers

        Args:
            topic: Topic name
            data: Message payload
            priority: Message priority level

        Returns:
            MessageResponse indicating success/failure
        """
        if not self.is_connected:
            return MessageResponse(False, "", "Not connected to message bus")

        try:
            message = Message(
                message_type=MessageType.TOPIC,
                sender_id=self.agent_id,
                topic=topic,
                payload=data,
                priority=priority,
            )

            success = await self._client.send_message(message)

            if success:
                return MessageResponse(True, message.message_id)
            else:
                return MessageResponse(
                    False, message.message_id, "Failed to send to topic"
                )

        except Exception as e:
            logger.error(f"Error sending to topic {topic}: {e}")
            return MessageResponse(False, "", str(e))

    async def send_to_group(
        self,
        group_id: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> MessageResponse:
        """
        Send message to group members

        Args:
            group_id: Group identifier
            data: Message payload
            priority: Message priority level

        Returns:
            MessageResponse indicating success/failure
        """
        if not self.is_connected:
            return MessageResponse(False, "", "Not connected to message bus")

        try:
            message = Message(
                message_type=MessageType.GROUP,
                sender_id=self.agent_id,
                group_id=group_id,
                payload=data,
                priority=priority,
            )

            success = await self._client.send_message(message)

            if success:
                return MessageResponse(True, message.message_id)
            else:
                return MessageResponse(
                    False, message.message_id, "Failed to send to group"
                )

        except Exception as e:
            logger.error(f"Error sending to group {group_id}: {e}")
            return MessageResponse(False, "", str(e))

    # === MESSAGE SUBSCRIPTIONS ===

    async def subscribe_topic(
        self, topic: str, handler: Callable[[Dict[str, Any]], None]
    ) -> bool:
        """
        Subscribe to topic messages

        Args:
            topic: Topic name to subscribe to
            handler: Function to call when topic message received

        Returns:
            True if subscription successful
        """
        try:
            success = await self._client.subscribe_to_topic(topic)
            if success:
                self._topic_handlers[topic] = handler
                logger.info(f"Agent {self.agent_id} subscribed to topic: {topic}")
            return success
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
            return False

    async def unsubscribe_topic(self, topic: str) -> bool:
        """
        Unsubscribe from topic messages

        Args:
            topic: Topic name to unsubscribe from

        Returns:
            True if unsubscription successful
        """
        try:
            success = await self._client.unsubscribe_from_topic(topic)
            if success and topic in self._topic_handlers:
                del self._topic_handlers[topic]
                logger.info(f"Agent {self.agent_id} unsubscribed from topic: {topic}")
            return success
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
            return False

    async def join_group(
        self, group_id: str, handler: Callable[[Dict[str, Any]], None]
    ) -> bool:
        """
        Join a message group

        Args:
            group_id: Group to join
            handler: Function to call when group message received

        Returns:
            True if join successful
        """
        try:
            success = await self._client.join_group(group_id)
            if success:
                self._group_handlers[group_id] = handler
                logger.info(f"Agent {self.agent_id} joined group: {group_id}")
            return success
        except Exception as e:
            logger.error(f"Error joining group {group_id}: {e}")
            return False

    async def leave_group(self, group_id: str) -> bool:
        """
        Leave a message group

        Args:
            group_id: Group to leave

        Returns:
            True if leave successful
        """
        try:
            success = await self._client.leave_group(group_id)
            if success and group_id in self._group_handlers:
                del self._group_handlers[group_id]
                logger.info(f"Agent {self.agent_id} left group: {group_id}")
            return success
        except Exception as e:
            logger.error(f"Error leaving group {group_id}: {e}")
            return False

    def register_direct_handler(
        self, handler: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Register handler for direct messages

        Args:
            handler: Function(sender_id, data) to call for direct messages
        """
        self._message_handlers["direct"] = handler

    def register_broadcast_handler(
        self, handler: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Register handler for broadcast messages

        Args:
            handler: Function(sender_id, data) to call for broadcast messages
        """
        self._message_handlers["broadcast"] = handler

    # === UTILITY METHODS ===

    def _route_incoming_message(self, message: Message) -> None:
        """Route incoming messages to appropriate handlers"""
        try:
            sender_id = message.sender_id
            data = message.payload

            if message.message_type == MessageType.POINT_TO_POINT:
                # Direct message
                if "direct" in self._message_handlers:
                    self._message_handlers["direct"](sender_id, data)

            elif message.message_type == MessageType.BROADCAST:
                # Broadcast message
                if "broadcast" in self._message_handlers:
                    self._message_handlers["broadcast"](sender_id, data)

            elif message.message_type == MessageType.TOPIC and message.topic:
                # Topic message
                if message.topic in self._topic_handlers:
                    self._topic_handlers[message.topic](data)

            elif message.message_type == MessageType.GROUP and message.group_id:
                # Group message
                if message.group_id in self._group_handlers:
                    self._group_handlers[message.group_id](data)

        except Exception as e:
            logger.error(f"Error routing message: {e}")

    async def get_connected_agents(self) -> List[str]:
        """Get list of currently connected agent IDs"""
        try:
            return await self._client.get_connected_agents()
        except Exception as e:
            logger.error(f"Error getting connected agents: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        try:
            return await self._client.get_stats()
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"SimpleMessageClient(agent_id={self.agent_id}, status={status})"


# Convenience factory function
def create_agent_client(agent_id: str, **kwargs) -> SimpleMessageClient:
    """
    Create a simple message client for an agent

    Args:
        agent_id: Unique agent identifier
        **kwargs: Additional configuration options

    Returns:
        Configured SimpleMessageClient
    """
    return SimpleMessageClient(agent_id, **kwargs)
