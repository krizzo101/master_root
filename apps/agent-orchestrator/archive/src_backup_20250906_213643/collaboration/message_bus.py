#!/usr/bin/env python3
"""
Real-Time Collaboration Message Bus

Provides high-performance pub/sub messaging for agent-to-agent communication
with Redis backend and WebSocket real-time streaming.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of collaboration messages"""

    DIRECT = "direct"
    BROADCAST = "broadcast"
    COORDINATION = "coordination"
    RESOURCE_SHARE = "resource_share"
    STATUS_UPDATE = "status_update"
    HANDOFF_REQUEST = "handoff_request"
    HANDOFF_RESPONSE = "handoff_response"
    ERROR_NOTIFICATION = "error_notification"


class Priority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class CollaborationMessage:
    """Message structure for agent collaboration"""

    message_type: MessageType
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    payload: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    correlation_id: Optional[str] = None
    requires_response: bool = False
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: f"msg_{int(time.time()*1000)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message_type": self.message_type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "requires_response": self.requires_response,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollaborationMessage":
        """Create from dictionary"""
        return cls(
            message_type=MessageType(data["message_type"]),
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            payload=data["payload"],
            priority=Priority(data["priority"]),
            correlation_id=data.get("correlation_id"),
            requires_response=data.get("requires_response", False),
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("message_id", f"msg_{int(time.time()*1000)}"),
        )


@dataclass
class AgentConnection:
    """Agent connection information"""

    agent_id: str
    websocket: Any  # websockets.WebSocketServerProtocol
    capabilities: Set[str]
    last_heartbeat: float
    message_count: int = 0


class CollaborationMessageBus:
    """
    High-performance message bus for real-time agent collaboration

    Features:
    - Redis pub/sub for scalable messaging
    - WebSocket connections for real-time delivery
    - File-based fallback for reliability
    - Message queuing and acknowledgments
    - Load balancing and failover
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        websocket_host: str = "localhost",
        websocket_port: int = 8767,
        fallback_dir: Optional[Path] = None,
        max_message_size: int = 1024 * 1024,  # 1MB
        message_ttl: int = 3600,  # 1 hour
    ):
        # Configuration
        self.redis_url = redis_url
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        self.fallback_dir = fallback_dir or Path("./collaboration_messages")
        self.max_message_size = max_message_size
        self.message_ttl = message_ttl

        # Initialize components
        self.redis_client: Optional[redis.Redis] = None
        self.websocket_server = None
        self.agent_connections: Dict[str, AgentConnection] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.running = False

        # Message queues for disconnected agents
        self.pending_messages: Dict[str, List[CollaborationMessage]] = {}

        # Stats tracking
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "broadcasts_sent": 0,
            "failed_deliveries": 0,
            "connected_agents": 0,
        }

        logger.info("CollaborationMessageBus initialized")

    async def start(self) -> None:
        """Start the message bus services"""
        if self.running:
            return

        logger.info("Starting CollaborationMessageBus...")

        # Initialize Redis connection
        if self.redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using file fallback")
                self.redis_client = None

        # Start WebSocket server
        if WEBSOCKETS_AVAILABLE:
            try:
                self.websocket_server = await websockets.serve(
                    self._handle_websocket_connection,
                    self.websocket_host,
                    self.websocket_port,
                    ping_interval=30,
                    ping_timeout=10,
                )
                logger.info(
                    f"WebSocket server started on {self.websocket_host}:{self.websocket_port}"
                )
            except Exception as e:
                logger.error(f"Failed to start WebSocket server: {e}")
                raise

        # Ensure fallback directory exists
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

        self.running = True
        logger.info("CollaborationMessageBus started successfully")

    async def stop(self) -> None:
        """Stop the message bus services"""
        if not self.running:
            return

        logger.info("Stopping CollaborationMessageBus...")
        self.running = False

        # Close WebSocket connections
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("CollaborationMessageBus stopped")

    async def register_agent(
        self, agent_id: str, websocket_connection, capabilities: List[str]
    ) -> bool:
        """Register an agent for collaboration"""
        try:
            connection = AgentConnection(
                agent_id=agent_id,
                websocket=websocket_connection,
                capabilities=set(capabilities),
                last_heartbeat=time.time(),
            )

            self.agent_connections[agent_id] = connection
            self.stats["connected_agents"] = len(self.agent_connections)

            # Deliver any pending messages
            await self._deliver_pending_messages(agent_id)

            logger.info(
                f"Agent {agent_id} registered with capabilities: {capabilities}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]
            self.stats["connected_agents"] = len(self.agent_connections)
            logger.info(f"Agent {agent_id} unregistered")

    async def send_message(self, message: CollaborationMessage) -> bool:
        """Send a message to specific agent or broadcast"""
        try:
            # Validate message size
            message_data = message.to_dict()
            message_json = json.dumps(message_data)
            if len(message_json.encode()) > self.max_message_size:
                logger.error(f"Message too large: {len(message_json)} bytes")
                return False

            # Route message based on type
            if message.to_agent:
                # Direct message
                success = await self._send_direct_message(message)
            else:
                # Broadcast message
                success = await self._send_broadcast_message(message)

            if success:
                self.stats["messages_sent"] += 1
            else:
                self.stats["failed_deliveries"] += 1

            return success

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.stats["failed_deliveries"] += 1
            return False

    async def _send_direct_message(self, message: CollaborationMessage) -> bool:
        """Send message to specific agent"""
        target_agent = message.to_agent

        # Try WebSocket delivery first
        if target_agent in self.agent_connections:
            try:
                connection = self.agent_connections[target_agent]
                await connection.websocket.send(json.dumps(message.to_dict()))
                connection.message_count += 1
                return True
            except Exception as e:
                logger.warning(f"WebSocket delivery failed for {target_agent}: {e}")
                # Remove broken connection
                await self.unregister_agent(target_agent)

        # Try Redis delivery
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    f"agent_queue:{target_agent}", json.dumps(message.to_dict())
                )
                await self.redis_client.expire(
                    f"agent_queue:{target_agent}", self.message_ttl
                )
                return True
            except Exception as e:
                logger.warning(f"Redis delivery failed for {target_agent}: {e}")

        # Fallback to pending messages queue
        if target_agent not in self.pending_messages:
            self.pending_messages[target_agent] = []
        self.pending_messages[target_agent].append(message)

        # Also save to file for persistence
        await self._save_message_to_file(message)

        logger.info(f"Message queued for {target_agent} (agent offline)")
        return True

    async def _send_broadcast_message(self, message: CollaborationMessage) -> bool:
        """Send message to all agents or filtered by capability"""
        successful_deliveries = 0

        # Get target agents
        target_agents = self.agent_connections.keys()

        # Filter by capabilities if specified in payload
        required_capabilities = message.payload.get("required_capabilities")
        if required_capabilities:
            target_agents = [
                agent_id
                for agent_id, conn in self.agent_connections.items()
                if any(cap in conn.capabilities for cap in required_capabilities)
            ]

        # Send to all targets via WebSocket
        for agent_id in target_agents:
            if agent_id == message.from_agent:
                continue  # Don't send to sender

            try:
                connection = self.agent_connections[agent_id]
                await connection.websocket.send(json.dumps(message.to_dict()))
                connection.message_count += 1
                successful_deliveries += 1
            except Exception as e:
                logger.warning(f"Broadcast delivery failed for {agent_id}: {e}")
                await self.unregister_agent(agent_id)

        # Also publish to Redis for agents not currently connected
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "agent_broadcast", json.dumps(message.to_dict())
                )
            except Exception as e:
                logger.warning(f"Redis broadcast failed: {e}")

        self.stats["broadcasts_sent"] += 1
        logger.info(f"Broadcast sent to {successful_deliveries} agents")
        return successful_deliveries > 0

    async def _handle_websocket_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        logger.info(f"New WebSocket connection from {websocket.remote_address}")

        try:
            # Wait for agent registration
            registration_data = await websocket.recv()
            registration = json.loads(registration_data)

            agent_id = registration.get("agent_id")
            capabilities = registration.get("capabilities", [])

            if not agent_id:
                await websocket.send(json.dumps({"error": "agent_id required"}))
                return

            # Register agent
            success = await self.register_agent(agent_id, websocket, capabilities)
            if not success:
                await websocket.send(json.dumps({"error": "registration failed"}))
                return

            # Send confirmation
            await websocket.send(
                json.dumps(
                    {
                        "type": "registration_confirmed",
                        "agent_id": agent_id,
                        "server_info": {
                            "message_bus_version": "1.0.0",
                            "max_message_size": self.max_message_size,
                            "connected_agents": len(self.agent_connections),
                        },
                    }
                )
            )

            # Handle incoming messages
            async for message in websocket:
                try:
                    await self._handle_agent_message(agent_id, message)
                except Exception as e:
                    logger.error(f"Error handling message from {agent_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for agent {agent_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Cleanup
            if "agent_id" in locals():
                await self.unregister_agent(agent_id)

    async def _handle_agent_message(self, sender_agent: str, message_data: str) -> None:
        """Handle message from agent"""
        try:
            data = json.loads(message_data)

            # Handle heartbeat
            if data.get("type") == "heartbeat":
                if sender_agent in self.agent_connections:
                    self.agent_connections[sender_agent].last_heartbeat = time.time()
                return

            # Handle collaboration message
            if data.get("type") == "collaboration_message":
                message = CollaborationMessage.from_dict(data["message"])
                message.from_agent = sender_agent  # Ensure sender is set correctly
                await self.send_message(message)
                self.stats["messages_received"] += 1

        except Exception as e:
            logger.error(f"Error processing message from {sender_agent}: {e}")

    async def _deliver_pending_messages(self, agent_id: str) -> None:
        """Deliver pending messages to newly connected agent"""
        if agent_id not in self.pending_messages:
            return

        messages = self.pending_messages[agent_id]
        connection = self.agent_connections[agent_id]

        delivered = 0
        for message in messages:
            try:
                await connection.websocket.send(json.dumps(message.to_dict()))
                delivered += 1
            except Exception as e:
                logger.warning(f"Failed to deliver pending message to {agent_id}: {e}")
                break

        # Remove delivered messages
        if delivered > 0:
            self.pending_messages[agent_id] = messages[delivered:]
            if not self.pending_messages[agent_id]:
                del self.pending_messages[agent_id]

        logger.info(f"Delivered {delivered} pending messages to {agent_id}")

    async def _save_message_to_file(self, message: CollaborationMessage) -> None:
        """Save message to file for persistence"""
        try:
            message_file = (
                self.fallback_dir / f"{message.to_agent}_{message.message_id}.json"
            )
            message_file.write_text(json.dumps(message.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Failed to save message to file: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            **self.stats,
            "running": self.running,
            "redis_connected": self.redis_client is not None,
            "websocket_server_running": self.websocket_server is not None,
            "pending_message_queues": len(self.pending_messages),
            "total_pending_messages": sum(
                len(msgs) for msgs in self.pending_messages.values()
            ),
        }

    def get_connected_agents(self) -> List[Dict[str, Any]]:
        """Get list of connected agents"""
        return [
            {
                "agent_id": conn.agent_id,
                "capabilities": list(conn.capabilities),
                "last_heartbeat": conn.last_heartbeat,
                "message_count": conn.message_count,
            }
            for conn in self.agent_connections.values()
        ]


# Factory function for easy instantiation
async def create_collaboration_message_bus(
    redis_url: Optional[str] = None, websocket_port: int = 8767, **kwargs
) -> CollaborationMessageBus:
    """Create and start a collaboration message bus"""
    bus = CollaborationMessageBus(
        redis_url=redis_url, websocket_port=websocket_port, **kwargs
    )
    await bus.start()
    return bus
