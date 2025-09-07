"""
Agent Message Client - Python SDK for agents to use the message bus.

Provides a simple, high-level interface for agents to:
- Connect to the message bus via WebSocket
- Send and receive messages
- Subscribe to topics and join groups
- Handle delivery confirmations
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    websockets = None
    logging.warning(
        "websockets package not available - install with: pip install websockets"
    )

from ..core.message_types import Message, MessagePriority, MessageType

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class AgentClientConfig:
    """Configuration for agent message client"""

    agent_id: str
    websocket_url: str = "ws://localhost:8767"
    auto_reconnect: bool = True
    reconnect_delay_seconds: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval_seconds: int = 30
    message_timeout_seconds: int = 30
    max_pending_messages: int = 1000
    capabilities: List[str] = None
    client_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.client_info is None:
            self.client_info = {}


class AgentMessageClient:
    """High-level client for agents to use the message bus"""

    def __init__(self, config: AgentClientConfig):
        if websockets is None:
            raise ImportError(
                "websockets package required - install with: pip install websockets"
            )

        self.config = config
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        self.session_id: Optional[str] = None

        # Message handling
        self.message_handlers: Dict[MessageType, Callable[[Message], Any]] = {}
        self.response_handlers: Dict[
            str, Callable[[Dict[str, Any]], Any]
        ] = {}  # correlation_id -> handler
        self.pending_responses: Dict[
            str, asyncio.Future
        ] = {}  # correlation_id -> future

        # Subscriptions
        self.group_memberships: Set[str] = set()
        self.topic_subscriptions: Set[str] = set()

        # Connection management
        self.reconnect_attempts = 0
        self.last_heartbeat = 0
        self.running = False

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []

        logger.info("AgentMessageClient initialized for agent: %s", config.agent_id)

    async def connect(self) -> bool:
        """Connect to the message bus"""
        if self.running:
            logger.warning("Client already running")
            return self.state == ConnectionState.AUTHENTICATED

        self.running = True

        try:
            await self._connect_and_authenticate()

            # Start background tasks
            self._background_tasks = [
                asyncio.create_task(self._message_handler_loop()),
                asyncio.create_task(self._heartbeat_loop()),
                asyncio.create_task(self._reconnection_loop()),
            ]

            return self.state == ConnectionState.AUTHENTICATED

        except Exception as e:
            logger.error("Failed to connect: %s", e)
            self.state = ConnectionState.FAILED
            return False

    async def disconnect(self) -> None:
        """Disconnect from the message bus"""
        logger.info("Disconnecting agent: %s", self.config.agent_id)

        self.running = False
        self.state = ConnectionState.DISCONNECTED

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        logger.info("Disconnected agent: %s", self.config.agent_id)

    async def send_message(
        self,
        recipient_id: Optional[str] = None,
        group_id: Optional[str] = None,
        topic: Optional[str] = None,
        payload: Dict[str, Any] = None,
        message_type: MessageType = MessageType.POINT_TO_POINT,
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_ack: bool = False,
        ttl_seconds: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Send a message through the message bus"""

        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot send message - not authenticated")
            return None

        if payload is None:
            payload = {}

        # Create message
        message = Message(
            message_type=message_type,
            priority=priority,
            sender_id=self.config.agent_id,
            recipient_id=recipient_id,
            group_id=group_id,
            topic=topic,
            payload=payload,
            requires_ack=requires_ack,
            ttl_seconds=ttl_seconds,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

        # Send via WebSocket
        try:
            await self._send_websocket_message(
                "send_message", {"message": message.to_dict()}
            )

            logger.debug("Sent message: %s", message.message_id)
            return message.message_id

        except Exception as e:
            logger.error("Error sending message: %s", e)
            return None

    async def send_point_to_point(
        self,
        recipient_id: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_ack: bool = False,
        ttl_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """Send a point-to-point message to another agent"""
        return await self.send_message(
            recipient_id=recipient_id,
            payload=payload,
            message_type=MessageType.POINT_TO_POINT,
            priority=priority,
            requires_ack=requires_ack,
            ttl_seconds=ttl_seconds,
        )

    async def broadcast(
        self,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """Broadcast a message to all connected agents"""
        return await self.send_message(
            payload=payload,
            message_type=MessageType.BROADCAST,
            priority=priority,
            ttl_seconds=ttl_seconds,
        )

    async def send_to_group(
        self,
        group_id: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """Send a message to all members of a group"""
        return await self.send_message(
            group_id=group_id,
            payload=payload,
            message_type=MessageType.GROUP,
            priority=priority,
            ttl_seconds=ttl_seconds,
        )

    async def send_to_topic(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """Send a message to all subscribers of a topic"""
        return await self.send_message(
            topic=topic,
            payload=payload,
            message_type=MessageType.TOPIC,
            priority=priority,
            ttl_seconds=ttl_seconds,
        )

    async def send_request(
        self,
        recipient_id: str,
        payload: Dict[str, Any],
        timeout_seconds: float = 30.0,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response"""

        correlation_id = str(uuid.uuid4())

        # Create future for response
        response_future = asyncio.Future()
        self.pending_responses[correlation_id] = response_future

        try:
            # Send request
            message_id = await self.send_point_to_point(
                recipient_id=recipient_id,
                payload=payload,
                priority=priority,
                requires_ack=True,
            )

            if not message_id:
                return None

            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout_seconds)
            return response

        except asyncio.TimeoutError:
            logger.error("Request timeout for correlation_id: %s", correlation_id)
            return None
        except Exception as e:
            logger.error("Error in request/response: %s", e)
            return None
        finally:
            # Clean up
            self.pending_responses.pop(correlation_id, None)

    async def join_group(self, group_id: str) -> bool:
        """Join a group"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot join group - not authenticated")
            return False

        try:
            response = await self._send_request("join_group", {"group_id": group_id})
            success = (
                response.get("data", {}).get("success", False) if response else False
            )

            if success:
                self.group_memberships.add(group_id)
                logger.info("Joined group: %s", group_id)
            else:
                logger.error("Failed to join group: %s", group_id)

            return success

        except Exception as e:
            logger.error("Error joining group %s: %s", group_id, e)
            return False

    async def leave_group(self, group_id: str) -> bool:
        """Leave a group"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot leave group - not authenticated")
            return False

        try:
            response = await self._send_request("leave_group", {"group_id": group_id})
            success = (
                response.get("data", {}).get("success", False) if response else False
            )

            if success:
                self.group_memberships.discard(group_id)
                logger.info("Left group: %s", group_id)
            else:
                logger.error("Failed to leave group: %s", group_id)

            return success

        except Exception as e:
            logger.error("Error leaving group %s: %s", group_id, e)
            return False

    async def subscribe_topic(self, topic: str) -> bool:
        """Subscribe to a topic"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot subscribe to topic - not authenticated")
            return False

        try:
            response = await self._send_request("subscribe_topic", {"topic": topic})
            success = (
                response.get("data", {}).get("success", False) if response else False
            )

            if success:
                self.topic_subscriptions.add(topic)
                logger.info("Subscribed to topic: %s", topic)
            else:
                logger.error("Failed to subscribe to topic: %s", topic)

            return success

        except Exception as e:
            logger.error("Error subscribing to topic %s: %s", topic, e)
            return False

    async def unsubscribe_topic(self, topic: str) -> bool:
        """Unsubscribe from a topic"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot unsubscribe from topic - not authenticated")
            return False

        try:
            response = await self._send_request("unsubscribe_topic", {"topic": topic})
            success = (
                response.get("data", {}).get("success", False) if response else False
            )

            if success:
                self.topic_subscriptions.discard(topic)
                logger.info("Unsubscribed from topic: %s", topic)
            else:
                logger.error("Failed to unsubscribe from topic: %s", topic)

            return success

        except Exception as e:
            logger.error("Error unsubscribing from topic %s: %s", topic, e)
            return False

    def register_message_handler(
        self, message_type: MessageType, handler: Callable[[Message], Any]
    ) -> None:
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.debug("Registered handler for message type: %s", message_type.value)

    def register_default_handler(self, handler: Callable[[Message], Any]) -> None:
        """Register a default handler for all message types"""
        # Use a special key for default handler
        self.message_handlers["_default"] = handler
        logger.debug("Registered default message handler")

    async def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from the message bus"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot get messages - not authenticated")
            return []

        try:
            response = await self._send_request("get_messages", {"count": count})
            if response and "data" in response:
                return response["data"].get("messages", [])
            return []

        except Exception as e:
            logger.error("Error getting messages: %s", e)
            return []

    async def get_status(self) -> Optional[Dict[str, Any]]:
        """Get status information from the message bus"""
        if self.state != ConnectionState.AUTHENTICATED:
            logger.error("Cannot get status - not authenticated")
            return None

        try:
            response = await self._send_request("get_status", {})
            return response.get("data") if response else None

        except Exception as e:
            logger.error("Error getting status: %s", e)
            return None

    # Internal methods

    async def _connect_and_authenticate(self) -> None:
        """Connect to WebSocket and authenticate"""
        try:
            self.state = ConnectionState.CONNECTING
            logger.info("Connecting to WebSocket: %s", self.config.websocket_url)

            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.config.websocket_url,
                ping_interval=30,
                ping_timeout=10,
                max_size=1024 * 1024,  # 1MB
                max_queue=self.config.max_pending_messages,
            )

            self.state = ConnectionState.CONNECTED

            # Authenticate
            auth_message = {
                "type": "authenticate",
                "agent_id": self.config.agent_id,
                "capabilities": self.config.capabilities,
                "client_info": self.config.client_info,
            }

            await self.websocket.send(json.dumps(auth_message))

            # Wait for authentication response
            response = await asyncio.wait_for(
                self.websocket.recv(), timeout=self.config.message_timeout_seconds
            )

            auth_response = json.loads(response)

            if auth_response.get("type") == "authenticated":
                self.state = ConnectionState.AUTHENTICATED
                self.session_id = auth_response.get("data", {}).get("session_id")
                self.reconnect_attempts = 0
                logger.info(
                    "Successfully authenticated agent: %s", self.config.agent_id
                )
            else:
                raise Exception(f"Authentication failed: {auth_response}")

        except Exception as e:
            logger.error("Connection/authentication failed: %s", e)
            self.state = ConnectionState.FAILED
            raise

    async def _send_websocket_message(
        self, message_type: str, data: Dict[str, Any]
    ) -> None:
        """Send a message via WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")

        message = {
            "type": message_type,
            "timestamp": time.time(),
            "data": data,
        }

        await self.websocket.send(json.dumps(message))

    async def _send_request(
        self, request_type: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response"""
        if self.state != ConnectionState.AUTHENTICATED:
            return None

        correlation_id = str(uuid.uuid4())

        # Create future for response
        response_future = asyncio.Future()
        self.response_handlers[
            correlation_id
        ] = lambda resp: response_future.set_result(resp)

        try:
            # Add correlation ID to data
            request_data = {**data, "correlation_id": correlation_id}

            # Send request
            await self._send_websocket_message(request_type, request_data)

            # Wait for response
            return await asyncio.wait_for(
                response_future, timeout=self.config.message_timeout_seconds
            )

        except asyncio.TimeoutError:
            logger.error("Request timeout for type: %s", request_type)
            return None
        except Exception as e:
            logger.error("Error in request: %s", e)
            return None
        finally:
            # Clean up
            self.response_handlers.pop(correlation_id, None)

    async def _message_handler_loop(self) -> None:
        """Handle incoming WebSocket messages"""
        while self.running and self.websocket:
            try:
                # Wait for message
                raw_message = await self.websocket.recv()
                message_data = json.loads(raw_message)

                await self._process_websocket_message(message_data)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.state = ConnectionState.DISCONNECTED
                break
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON received: %s", e)
            except Exception as e:
                logger.error("Error in message handler loop: %s", e)
                await asyncio.sleep(1)

    async def _process_websocket_message(self, message_data: Dict[str, Any]) -> None:
        """Process incoming WebSocket message"""
        try:
            message_type = message_data.get("type")

            if message_type == "notification":
                # Handle notifications (incoming messages)
                await self._handle_notification(message_data)

            elif message_type in [
                "authenticated",
                "message_sent",
                "group_joined",
                "group_left",
                "topic_subscribed",
                "topic_unsubscribed",
                "messages",
                "status",
                "heartbeat_ack",
            ]:
                # Handle responses
                await self._handle_response(message_data)

            elif message_type == "error":
                logger.error("Server error: %s", message_data.get("error"))

            else:
                logger.warning("Unknown message type: %s", message_type)

        except Exception as e:
            logger.error("Error processing WebSocket message: %s", e)

    async def _handle_notification(self, message_data: Dict[str, Any]) -> None:
        """Handle incoming message notifications"""
        try:
            notification_type = message_data.get("notification_type")
            data = message_data.get("data", {})

            if "message" in data:
                # Incoming message
                message = Message.from_dict(data["message"])

                # Find appropriate handler
                handler = self.message_handlers.get(message.message_type)
                if not handler:
                    handler = self.message_handlers.get("_default")

                if handler:
                    try:
                        # Call handler (could be sync or async)
                        result = handler(message)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error("Error in message handler: %s", e)
                else:
                    logger.warning(
                        "No handler for message type: %s", message.message_type
                    )

        except Exception as e:
            logger.error("Error handling notification: %s", e)

    async def _handle_response(self, message_data: Dict[str, Any]) -> None:
        """Handle response messages"""
        try:
            # Check if this is a response to a pending request
            data = message_data.get("data", {})
            correlation_id = data.get("correlation_id")

            if correlation_id and correlation_id in self.response_handlers:
                handler = self.response_handlers[correlation_id]
                handler(message_data)

            # Handle specific response types
            message_type = message_data.get("type")

            if message_type == "heartbeat_ack":
                self.last_heartbeat = time.time()

        except Exception as e:
            logger.error("Error handling response: %s", e)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats"""
        while self.running:
            try:
                if self.state == ConnectionState.AUTHENTICATED:
                    await self._send_websocket_message(
                        "heartbeat", {"timestamp": time.time()}
                    )

                await asyncio.sleep(self.config.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop: %s", e)
                await asyncio.sleep(self.config.heartbeat_interval_seconds)

    async def _reconnection_loop(self) -> None:
        """Handle automatic reconnection"""
        while self.running and self.config.auto_reconnect:
            try:
                if self.state == ConnectionState.DISCONNECTED:
                    if self.reconnect_attempts < self.config.max_reconnect_attempts:
                        logger.info(
                            "Attempting to reconnect... (attempt %d/%d)",
                            self.reconnect_attempts + 1,
                            self.config.max_reconnect_attempts,
                        )

                        self.state = ConnectionState.RECONNECTING
                        self.reconnect_attempts += 1

                        try:
                            await self._connect_and_authenticate()

                            # Re-subscribe to groups and topics
                            for group_id in list(self.group_memberships):
                                await self.join_group(group_id)

                            for topic in list(self.topic_subscriptions):
                                await self.subscribe_topic(topic)

                        except Exception as e:
                            logger.error("Reconnection attempt failed: %s", e)
                            await asyncio.sleep(self.config.reconnect_delay_seconds)
                    else:
                        logger.error("Max reconnection attempts exceeded")
                        self.state = ConnectionState.FAILED
                        break

                await asyncio.sleep(5)  # Check reconnection status every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in reconnection loop: %s", e)
                await asyncio.sleep(10)

    @property
    def is_connected(self) -> bool:
        """Check if client is connected and authenticated"""
        return self.state == ConnectionState.AUTHENTICATED

    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "agent_id": self.config.agent_id,
            "state": self.state.value,
            "session_id": self.session_id,
            "reconnect_attempts": self.reconnect_attempts,
            "group_memberships": list(self.group_memberships),
            "topic_subscriptions": list(self.topic_subscriptions),
            "last_heartbeat": self.last_heartbeat,
            "websocket_url": self.config.websocket_url,
        }
