"""
WebSocket Gateway for real-time agent connections.

Provides WebSocket endpoint for agents to connect and receive real-time
message notifications while using Redis Streams for reliable message delivery.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None
    logging.warning(
        "websockets package not available - install with: pip install websockets"
    )

from ..core.message_bus import MessageBus
from ..core.message_types import Message, MessageType

logger = logging.getLogger(__name__)


class WebSocketGateway:
    """WebSocket gateway for real-time agent communication"""

    def __init__(
        self,
        message_bus: MessageBus,
        host: str = "localhost",
        port: int = 8767,
        max_connections: int = 1000,
    ):
        if websockets is None:
            raise ImportError(
                "websockets package required - install with: pip install websockets"
            )

        self.message_bus = message_bus
        self.host = host
        self.port = port
        self.max_connections = max_connections

        # Connection management
        self.connections: Dict[
            str, WebSocketServerProtocol
        ] = {}  # agent_id -> websocket
        self.agent_sessions: Dict[
            WebSocketServerProtocol, str
        ] = {}  # websocket -> agent_id
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}  # agent_id -> metadata

        # Server state
        self.server = None
        self.running = False

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []

        logger.info("WebSocketGateway initialized on %s:%d", host, port)

    async def start(self) -> None:
        """Start the WebSocket gateway"""
        if self.running:
            logger.warning("WebSocketGateway already running")
            return

        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
                max_size=1024 * 1024,  # 1MB max message size
                max_queue=100,  # Max queued messages per connection
            )

            # Start background tasks
            self._background_tasks = [
                asyncio.create_task(self._connection_monitor()),
                asyncio.create_task(self._redis_notification_listener()),
            ]

            self.running = True
            logger.info("WebSocketGateway started on %s:%d", self.host, self.port)

        except Exception as e:
            logger.error("Failed to start WebSocketGateway: %s", e)
            raise

    async def stop(self) -> None:
        """Stop the WebSocket gateway"""
        if not self.running:
            return

        logger.info("Stopping WebSocketGateway...")
        self.running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close all connections
        if self.connections:
            close_tasks = []
            for websocket in self.connections.values():
                close_tasks.append(self._close_connection(websocket))
            await asyncio.gather(*close_tasks, return_exceptions=True)

        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("WebSocketGateway stopped")

    async def _handle_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handle new WebSocket connection"""
        client_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info("New WebSocket connection from: %s", client_address)

        agent_id = None

        try:
            # Wait for authentication message
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            auth_data = json.loads(auth_message)

            if auth_data.get("type") != "authenticate":
                await self._send_error(
                    websocket, "First message must be authentication"
                )
                return

            agent_id = auth_data.get("agent_id")
            if not agent_id:
                await self._send_error(
                    websocket, "agent_id required for authentication"
                )
                return

            # Check connection limits
            if len(self.connections) >= self.max_connections:
                await self._send_error(websocket, "Maximum connections exceeded")
                return

            # Register the connection
            await self._register_connection(websocket, agent_id, auth_data)

            # Send authentication success
            await self._send_response(
                websocket,
                "authenticated",
                {
                    "agent_id": agent_id,
                    "session_id": str(uuid.uuid4()),
                    "server_time": time.time(),
                },
            )

            # Handle messages from this connection
            async for message in websocket:
                try:
                    await self._handle_message(websocket, agent_id, message)
                except Exception as e:
                    logger.error("Error handling message from %s: %s", agent_id, e)
                    await self._send_error(websocket, f"Message processing error: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed: %s", client_address)
        except asyncio.TimeoutError:
            logger.warning("Authentication timeout for: %s", client_address)
            await self._send_error(websocket, "Authentication timeout")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from: %s", client_address)
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error("Error handling connection from %s: %s", client_address, e)
        finally:
            # Clean up connection
            if agent_id:
                await self._unregister_connection(agent_id, websocket)

    async def _register_connection(
        self,
        websocket: WebSocketServerProtocol,
        agent_id: str,
        auth_data: Dict[str, Any],
    ) -> None:
        """Register a new agent connection"""
        # Close existing connection for this agent if any
        if agent_id in self.connections:
            old_websocket = self.connections[agent_id]
            await self._close_connection(old_websocket, "New connection established")

        # Register new connection
        self.connections[agent_id] = websocket
        self.agent_sessions[websocket] = agent_id
        self.connection_metadata[agent_id] = {
            "connected_at": time.time(),
            "client_info": auth_data.get("client_info", {}),
            "capabilities": auth_data.get("capabilities", []),
        }

        # Register with message bus
        await self.message_bus.register_agent(agent_id)

        # Send any pending messages
        await self._send_pending_messages(agent_id)

        logger.info("Agent connected via WebSocket: %s", agent_id)

    async def _unregister_connection(
        self, agent_id: str, websocket: WebSocketServerProtocol
    ) -> None:
        """Unregister an agent connection"""
        # Remove from tracking
        self.connections.pop(agent_id, None)
        self.agent_sessions.pop(websocket, None)
        self.connection_metadata.pop(agent_id, None)

        # Unregister from message bus
        await self.message_bus.unregister_agent(agent_id)

        logger.info("Agent disconnected from WebSocket: %s", agent_id)

    async def _handle_message(
        self, websocket: WebSocketServerProtocol, agent_id: str, raw_message: str
    ) -> None:
        """Handle incoming message from agent"""
        try:
            data = json.loads(raw_message)
            message_type = data.get("type")

            if message_type == "send_message":
                # Agent wants to send a message
                await self._handle_send_message(websocket, agent_id, data)

            elif message_type == "join_group":
                # Agent wants to join a group
                group_id = data.get("group_id")
                if group_id:
                    success = await self.message_bus.join_group(agent_id, group_id)
                    await self._send_response(
                        websocket,
                        "group_joined",
                        {"group_id": group_id, "success": success},
                    )

            elif message_type == "leave_group":
                # Agent wants to leave a group
                group_id = data.get("group_id")
                if group_id:
                    success = await self.message_bus.leave_group(agent_id, group_id)
                    await self._send_response(
                        websocket,
                        "group_left",
                        {"group_id": group_id, "success": success},
                    )

            elif message_type == "subscribe_topic":
                # Agent wants to subscribe to a topic
                topic = data.get("topic")
                if topic:
                    success = await self.message_bus.subscribe_topic(agent_id, topic)
                    await self._send_response(
                        websocket,
                        "topic_subscribed",
                        {"topic": topic, "success": success},
                    )

            elif message_type == "unsubscribe_topic":
                # Agent wants to unsubscribe from a topic
                topic = data.get("topic")
                if topic:
                    success = await self.message_bus.unsubscribe_topic(agent_id, topic)
                    await self._send_response(
                        websocket,
                        "topic_unsubscribed",
                        {"topic": topic, "success": success},
                    )

            elif message_type == "get_messages":
                # Agent wants to retrieve messages from its stream
                await self._handle_get_messages(websocket, agent_id, data)

            elif message_type == "heartbeat":
                # Heartbeat from agent
                await self._handle_heartbeat(websocket, agent_id, data)

            elif message_type == "get_status":
                # Agent wants status information
                await self._handle_get_status(websocket, agent_id)

            else:
                await self._send_error(
                    websocket, f"Unknown message type: {message_type}"
                )

        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error("Error handling message from %s: %s", agent_id, e)
            await self._send_error(websocket, f"Processing error: {e}")

    async def _handle_send_message(
        self, websocket: WebSocketServerProtocol, sender_id: str, data: Dict[str, Any]
    ) -> None:
        """Handle message sending request from agent"""
        try:
            # Extract message data
            message_data = data.get("message", {})
            message_data["sender_id"] = sender_id  # Ensure sender is correct

            # Create message object
            message = Message.from_dict(message_data)

            # Send via message bus
            success = await self.message_bus.send_message(message)

            # Send confirmation
            await self._send_response(
                websocket,
                "message_sent",
                {"message_id": message.message_id, "success": success},
            )

        except Exception as e:
            logger.error("Error sending message for %s: %s", sender_id, e)
            await self._send_error(websocket, f"Failed to send message: {e}")

    async def _handle_get_messages(
        self, websocket: WebSocketServerProtocol, agent_id: str, data: Dict[str, Any]
    ) -> None:
        """Handle request to get messages from agent's stream"""
        try:
            # Get parameters
            count = min(data.get("count", 10), 100)  # Max 100 messages
            start_id = data.get(
                "start_id", "-"
            )  # Start from beginning if not specified

            # Read from agent's stream
            stream_key = f"agent:{agent_id}:messages"

            # Use Redis client from message bus
            redis_client = self.message_bus.redis_client
            messages = await redis_client.xread({stream_key: start_id}, count=count)

            # Process messages
            message_list = []
            if messages:
                stream_messages = messages[0][
                    1
                ]  # messages[0] = (stream_name, [(id, data), ...])
                for msg_id, msg_data in stream_messages:
                    try:
                        # Deserialize message
                        message = await self.message_bus._deserialize_message(
                            msg_data[b"data"]
                        )
                        message_dict = message.to_dict()
                        message_dict["redis_message_id"] = msg_id.decode()
                        message_list.append(message_dict)
                    except Exception as e:
                        logger.error("Error deserializing message %s: %s", msg_id, e)

            # Send messages to agent
            await self._send_response(
                websocket,
                "messages",
                {"count": len(message_list), "messages": message_list},
            )

        except Exception as e:
            logger.error("Error getting messages for %s: %s", agent_id, e)
            await self._send_error(websocket, f"Failed to get messages: {e}")

    async def _handle_heartbeat(
        self, websocket: WebSocketServerProtocol, agent_id: str, data: Dict[str, Any]
    ) -> None:
        """Handle heartbeat from agent"""
        # Update heartbeat timestamp in message bus
        self.message_bus.agent_connections[agent_id] = time.time()

        # Send heartbeat response
        await self._send_response(
            websocket,
            "heartbeat_ack",
            {
                "server_time": time.time(),
                "client_timestamp": data.get("timestamp"),
            },
        )

    async def _handle_get_status(
        self, websocket: WebSocketServerProtocol, agent_id: str
    ) -> None:
        """Handle status request from agent"""
        try:
            # Get message bus stats
            stats = await self.message_bus.get_stats()
            health = await self.message_bus.health_check()

            # Get gateway stats
            gateway_stats = {
                "connected_agents": len(self.connections),
                "total_connections": len(self.agent_sessions),
                "uptime_seconds": time.time()
                - self.connection_metadata.get(agent_id, {}).get(
                    "connected_at", time.time()
                ),
            }

            await self._send_response(
                websocket,
                "status",
                {
                    "agent_id": agent_id,
                    "message_bus_stats": stats.to_dict(),
                    "message_bus_health": health,
                    "gateway_stats": gateway_stats,
                },
            )

        except Exception as e:
            logger.error("Error getting status for %s: %s", agent_id, e)
            await self._send_error(websocket, f"Failed to get status: {e}")

    async def _send_pending_messages(self, agent_id: str) -> None:
        """Send any pending messages to newly connected agent"""
        try:
            # Get recent messages from agent's stream
            stream_key = f"agent:{agent_id}:messages"
            redis_client = self.message_bus.redis_client

            # Get unread messages (this is a simplified version)
            # In a production system, you'd track read positions per agent
            messages = await redis_client.xrevrange(stream_key, count=10)

            if messages and agent_id in self.connections:
                websocket = self.connections[agent_id]

                for msg_id, msg_data in reversed(
                    messages
                ):  # Send in chronological order
                    try:
                        message = await self.message_bus._deserialize_message(
                            msg_data[b"data"]
                        )
                        await self._send_notification(
                            websocket,
                            "pending_message",
                            {
                                "message": message.to_dict(),
                                "redis_message_id": msg_id.decode(),
                            },
                        )
                    except Exception as e:
                        logger.error("Error sending pending message: %s", e)

        except Exception as e:
            logger.error("Error sending pending messages to %s: %s", agent_id, e)

    async def _send_response(
        self,
        websocket: WebSocketServerProtocol,
        response_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Send response message to agent"""
        response = {
            "type": response_type,
            "timestamp": time.time(),
            "data": data,
        }

        try:
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error("Error sending response: %s", e)

    async def _send_notification(
        self,
        websocket: WebSocketServerProtocol,
        notification_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Send notification to agent"""
        notification = {
            "type": "notification",
            "notification_type": notification_type,
            "timestamp": time.time(),
            "data": data,
        }

        try:
            await websocket.send(json.dumps(notification))
        except Exception as e:
            logger.error("Error sending notification: %s", e)

    async def _send_error(
        self, websocket: WebSocketServerProtocol, error_message: str
    ) -> None:
        """Send error message to agent"""
        error_response = {
            "type": "error",
            "timestamp": time.time(),
            "error": error_message,
        }

        try:
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error("Error sending error message: %s", e)

    async def _close_connection(
        self, websocket: WebSocketServerProtocol, reason: str = "Connection closed"
    ) -> None:
        """Close WebSocket connection gracefully"""
        try:
            await websocket.close(reason=reason)
        except Exception as e:
            logger.error("Error closing connection: %s", e)

    async def _connection_monitor(self) -> None:
        """Monitor WebSocket connections and clean up stale ones"""
        while self.running:
            try:
                current_time = time.time()
                stale_connections = []

                # Check for stale connections
                for agent_id, metadata in self.connection_metadata.items():
                    connected_at = metadata.get("connected_at", current_time)
                    if agent_id not in self.connections:  # Connection was closed
                        stale_connections.append(agent_id)
                    elif current_time - connected_at > 3600:  # 1 hour without heartbeat
                        # This should be handled by heartbeat mechanism
                        pass

                # Clean up stale connection metadata
                for agent_id in stale_connections:
                    self.connection_metadata.pop(agent_id, None)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in connection monitor: %s", e)
                await asyncio.sleep(60)

    async def _redis_notification_listener(self) -> None:
        """Listen for Redis pub/sub notifications and forward to WebSocket clients"""
        try:
            # Create separate Redis client for pub/sub
            pubsub = self.message_bus.redis_client.pubsub()

            # Subscribe to all agent notification channels
            # We'll dynamically subscribe/unsubscribe as agents connect/disconnect
            pattern = "notify:*"
            await pubsub.psubscribe(pattern)

            while self.running:
                try:
                    message = await pubsub.get_message(timeout=1.0)

                    if message and message["type"] == "pmessage":
                        # Extract agent ID from channel name
                        channel = message["channel"].decode()
                        if channel.startswith("notify:"):
                            agent_id = channel[7:]  # Remove 'notify:' prefix

                            # Forward notification if agent is connected
                            if agent_id in self.connections:
                                websocket = self.connections[agent_id]
                                notification_data = json.loads(message["data"].decode())

                                await self._send_notification(
                                    websocket,
                                    notification_data.get("type", "redis_notification"),
                                    notification_data,
                                )

                except asyncio.TimeoutError:
                    # No message received, continue
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Error in Redis notification listener: %s", e)
                    await asyncio.sleep(5)

            # Cleanup
            await pubsub.close()

        except Exception as e:
            logger.error("Fatal error in Redis notification listener: %s", e)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket gateway statistics"""
        return {
            "host": self.host,
            "port": self.port,
            "running": self.running,
            "connected_agents": len(self.connections),
            "total_sessions": len(self.agent_sessions),
            "max_connections": self.max_connections,
            "connection_details": {
                agent_id: {
                    "connected_at": metadata.get("connected_at"),
                    "uptime_seconds": time.time()
                    - metadata.get("connected_at", time.time()),
                    "capabilities": metadata.get("capabilities", []),
                }
                for agent_id, metadata in self.connection_metadata.items()
            },
        }

    async def broadcast_to_all(
        self, notification_type: str, data: Dict[str, Any]
    ) -> int:
        """Broadcast notification to all connected agents"""
        sent_count = 0

        for agent_id, websocket in self.connections.items():
            try:
                await self._send_notification(websocket, notification_type, data)
                sent_count += 1
            except Exception as e:
                logger.error("Error broadcasting to %s: %s", agent_id, e)

        return sent_count

    async def send_to_agent(
        self, agent_id: str, notification_type: str, data: Dict[str, Any]
    ) -> bool:
        """Send notification to specific agent if connected"""
        if agent_id in self.connections:
            try:
                websocket = self.connections[agent_id]
                await self._send_notification(websocket, notification_type, data)
                return True
            except Exception as e:
                logger.error("Error sending to %s: %s", agent_id, e)

        return False
