"""
Core Message Bus implementation using Redis Streams and Pub/Sub.

Provides high-performance, reliable message passing between agents with:
- Redis Streams for persistent queues and message replay
- Redis Pub/Sub for real-time notifications
- Connection pooling for scalability
- Message compression for efficiency
- Delivery confirmation and retry logic
"""

import asyncio
import gzip
import json
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import redis.asyncio as redis
except ImportError:
    redis = None
    logging.warning("redis package not available - install with: pip install redis")

from .message_types import (
    Message,
    MessageAck,
    MessagePriority,
    MessageStats,
    MessageType,
)

logger = logging.getLogger(__name__)


class MessageBus:
    """High-performance Redis-based message bus for agent communication"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 20,
        enable_compression: bool = True,
        compression_threshold: int = 1024,  # bytes
        default_ttl: int = 3600,  # seconds
        enable_persistence: bool = True,
    ):
        if redis is None:
            raise ImportError(
                "redis package required - install with: pip install redis"
            )

        self.redis_url = redis_url
        self.max_connections = max_connections
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.default_ttl = default_ttl
        self.enable_persistence = enable_persistence

        # Connection pools
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.Redis] = None

        # Subscriber management
        self.message_handlers: Dict[str, Callable[[Message], Any]] = {}
        self.group_subscriptions: Dict[str, Set[str]] = {}  # group_id -> {agent_ids}
        self.topic_subscriptions: Dict[str, Set[str]] = {}  # topic -> {agent_ids}
        self.agent_connections: Dict[str, float] = {}  # agent_id -> last_heartbeat

        # Statistics and monitoring
        self.stats = MessageStats()
        self.running = False

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []

        logger.info("MessageBus initialized with Redis: %s", redis_url)

    async def start(self) -> None:
        """Start the message bus system"""
        if self.running:
            logger.warning("MessageBus already running")
            return

        try:
            # Initialize Redis connections
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            self.pubsub_client = redis.Redis(connection_pool=self.redis_pool)

            # Test connection
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")

            # Start background tasks
            self._background_tasks = [
                asyncio.create_task(self._heartbeat_monitor()),
                asyncio.create_task(self._message_cleanup()),
                asyncio.create_task(self._stats_updater()),
            ]

            self.running = True
            logger.info("MessageBus started successfully")

        except Exception as e:
            logger.error("Failed to start MessageBus: %s", e)
            raise

    async def stop(self) -> None:
        """Stop the message bus system"""
        if not self.running:
            return

        logger.info("Stopping MessageBus...")
        self.running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close Redis connections
        if self.redis_client:
            await self.redis_client.close()
        if self.pubsub_client:
            await self.pubsub_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()

        logger.info("MessageBus stopped")

    async def send_message(self, message: Message) -> bool:
        """Send a message through the message bus"""
        if not self.running:
            raise RuntimeError("MessageBus not running")

        try:
            # Set default TTL if not specified
            if message.ttl_seconds is None:
                message.ttl_seconds = self.default_ttl

            # Mark as received by message bus
            message.mark_received()

            # Serialize message
            serialized_msg = await self._serialize_message(message)

            # Route message based on type
            success = await self._route_message(message, serialized_msg)

            if success:
                self.stats.total_sent += 1
                logger.debug("Message sent: %s", message.message_id)
            else:
                self.stats.total_failed += 1
                logger.error("Failed to send message: %s", message.message_id)

            return success

        except Exception as e:
            logger.error("Error sending message %s: %s", message.message_id, e)
            self.stats.total_failed += 1
            return False

    async def _route_message(self, message: Message, serialized_msg: bytes) -> bool:
        """Route message based on its type"""
        try:
            if message.message_type == MessageType.POINT_TO_POINT:
                return await self._send_point_to_point(message, serialized_msg)
            elif message.message_type == MessageType.BROADCAST:
                return await self._send_broadcast(message, serialized_msg)
            elif message.message_type == MessageType.GROUP:
                return await self._send_group(message, serialized_msg)
            elif message.message_type == MessageType.TOPIC:
                return await self._send_topic(message, serialized_msg)
            elif message.message_type == MessageType.SYSTEM:
                return await self._send_system(message, serialized_msg)
            else:
                logger.error("Unknown message type: %s", message.message_type)
                return False
        except Exception as e:
            logger.error("Error routing message: %s", e)
            return False

    async def _send_point_to_point(
        self, message: Message, serialized_msg: bytes
    ) -> bool:
        """Send point-to-point message to specific agent"""
        if not message.recipient_id:
            logger.error("Point-to-point message missing recipient_id")
            return False

        # Use Redis Stream for reliable delivery
        stream_key = f"agent:{message.recipient_id}:messages"

        try:
            # Add to recipient's stream
            message_id = await self.redis_client.xadd(
                stream_key,
                {"data": serialized_msg},
                maxlen=10000,  # Keep last 10k messages
                approximate=True,
            )

            # Add to persistent store if required
            if message.persistent and self.enable_persistence:
                await self._store_persistent_message(message, serialized_msg)

            # Send real-time notification via pub/sub
            notification_channel = f"notify:{message.recipient_id}"
            await self.redis_client.publish(
                notification_channel,
                json.dumps(
                    {
                        "type": "new_message",
                        "message_id": message.message_id,
                        "sender_id": message.sender_id,
                        "stream_key": stream_key,
                        "redis_message_id": message_id.decode(),
                    }
                ),
            )

            logger.debug("Point-to-point message sent to %s", message.recipient_id)
            return True

        except Exception as e:
            logger.error("Error sending point-to-point message: %s", e)
            return False

    async def _send_broadcast(self, message: Message, serialized_msg: bytes) -> bool:
        """Send broadcast message to all connected agents"""
        try:
            # Get all connected agents
            connected_agents = list(self.agent_connections.keys())

            if not connected_agents:
                logger.warning("No connected agents for broadcast")
                return True

            # Send to all agents via their streams
            pipeline = self.redis_client.pipeline()

            for agent_id in connected_agents:
                stream_key = f"agent:{agent_id}:messages"
                pipeline.xadd(
                    stream_key, {"data": serialized_msg}, maxlen=10000, approximate=True
                )

            # Execute pipeline
            await pipeline.execute()

            # Send pub/sub notifications
            for agent_id in connected_agents:
                notification_channel = f"notify:{agent_id}"
                await self.redis_client.publish(
                    notification_channel,
                    json.dumps(
                        {
                            "type": "broadcast_message",
                            "message_id": message.message_id,
                            "sender_id": message.sender_id,
                        }
                    ),
                )

            logger.debug("Broadcast message sent to %d agents", len(connected_agents))
            return True

        except Exception as e:
            logger.error("Error sending broadcast message: %s", e)
            return False

    async def _send_group(self, message: Message, serialized_msg: bytes) -> bool:
        """Send message to group members"""
        if not message.group_id:
            logger.error("Group message missing group_id")
            return False

        try:
            # Get group members
            group_members = self.group_subscriptions.get(message.group_id, set())

            if not group_members:
                logger.warning("No members in group: %s", message.group_id)
                return True

            # Send to group members
            pipeline = self.redis_client.pipeline()

            for agent_id in group_members:
                if agent_id in self.agent_connections:  # Only send to connected agents
                    stream_key = f"agent:{agent_id}:messages"
                    pipeline.xadd(
                        stream_key,
                        {"data": serialized_msg},
                        maxlen=10000,
                        approximate=True,
                    )

            await pipeline.execute()

            # Send notifications
            for agent_id in group_members:
                if agent_id in self.agent_connections:
                    notification_channel = f"notify:{agent_id}"
                    await self.redis_client.publish(
                        notification_channel,
                        json.dumps(
                            {
                                "type": "group_message",
                                "message_id": message.message_id,
                                "sender_id": message.sender_id,
                                "group_id": message.group_id,
                            }
                        ),
                    )

            logger.debug(
                "Group message sent to %d members of group %s",
                len(group_members),
                message.group_id,
            )
            return True

        except Exception as e:
            logger.error("Error sending group message: %s", e)
            return False

    async def _send_topic(self, message: Message, serialized_msg: bytes) -> bool:
        """Send message to topic subscribers"""
        if not message.topic:
            logger.error("Topic message missing topic")
            return False

        try:
            # Get topic subscribers
            subscribers = self.topic_subscriptions.get(message.topic, set())

            if not subscribers:
                logger.warning("No subscribers for topic: %s", message.topic)
                return True

            # Send to subscribers
            pipeline = self.redis_client.pipeline()

            for agent_id in subscribers:
                if agent_id in self.agent_connections:
                    stream_key = f"agent:{agent_id}:messages"
                    pipeline.xadd(
                        stream_key,
                        {"data": serialized_msg},
                        maxlen=10000,
                        approximate=True,
                    )

            await pipeline.execute()

            # Send notifications
            for agent_id in subscribers:
                if agent_id in self.agent_connections:
                    notification_channel = f"notify:{agent_id}"
                    await self.redis_client.publish(
                        notification_channel,
                        json.dumps(
                            {
                                "type": "topic_message",
                                "message_id": message.message_id,
                                "sender_id": message.sender_id,
                                "topic": message.topic,
                            }
                        ),
                    )

            logger.debug(
                "Topic message sent to %d subscribers of topic %s",
                len(subscribers),
                message.topic,
            )
            return True

        except Exception as e:
            logger.error("Error sending topic message: %s", e)
            return False

    async def _send_system(self, message: Message, serialized_msg: bytes) -> bool:
        """Send system message (admin/control messages)"""
        try:
            # System messages go to all agents
            return await self._send_broadcast(message, serialized_msg)
        except Exception as e:
            logger.error("Error sending system message: %s", e)
            return False

    async def _serialize_message(self, message: Message) -> bytes:
        """Serialize message with optional compression"""
        try:
            # Convert to JSON
            json_data = message.to_json().encode("utf-8")

            # Apply compression if enabled and data is large enough
            if self.enable_compression and len(json_data) > self.compression_threshold:
                compressed_data = gzip.compress(json_data)
                # Only use compression if it actually saves space
                if len(compressed_data) < len(json_data):
                    return b"compressed:" + compressed_data

            return json_data

        except Exception as e:
            logger.error("Error serializing message: %s", e)
            raise

    async def _deserialize_message(self, data: bytes) -> Message:
        """Deserialize message with decompression support"""
        try:
            # Check if compressed
            if data.startswith(b"compressed:"):
                compressed_data = data[11:]  # Remove "compressed:" prefix
                json_data = gzip.decompress(compressed_data).decode("utf-8")
            else:
                json_data = data.decode("utf-8")

            return Message.from_json(json_data)

        except Exception as e:
            logger.error("Error deserializing message: %s", e)
            raise

    async def _store_persistent_message(
        self, message: Message, serialized_msg: bytes
    ) -> None:
        """Store message in persistent storage"""
        try:
            # Store in Redis hash for persistence across restarts
            key = f"persistent:message:{message.message_id}"
            await self.redis_client.hset(
                key,
                mapping={
                    "data": serialized_msg,
                    "timestamp": message.timestamp,
                    "ttl": message.ttl_seconds or 0,
                },
            )

            # Set TTL on the key itself
            if message.ttl_seconds:
                await self.redis_client.expire(key, message.ttl_seconds)

        except Exception as e:
            logger.error("Error storing persistent message: %s", e)

    async def register_agent(self, agent_id: str) -> bool:
        """Register an agent with the message bus"""
        try:
            # Add to active agents
            self.agent_connections[agent_id] = time.time()

            # Create agent's message stream if it doesn't exist
            stream_key = f"agent:{agent_id}:messages"
            try:
                # Try to get stream info, create if doesn't exist
                await self.redis_client.xinfo_stream(stream_key)
            except redis.ResponseError:
                # Stream doesn't exist, create it with a dummy message
                await self.redis_client.xadd(stream_key, {"init": "true"})
                # Remove the dummy message
                messages = await self.redis_client.xrange(stream_key, count=1)
                if messages:
                    await self.redis_client.xdel(stream_key, messages[0][0])

            logger.info("Agent registered: %s", agent_id)
            return True

        except Exception as e:
            logger.error("Error registering agent %s: %s", agent_id, e)
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the message bus"""
        try:
            # Remove from active agents
            self.agent_connections.pop(agent_id, None)

            # Remove from group subscriptions
            for group_id, members in self.group_subscriptions.items():
                members.discard(agent_id)

            # Remove from topic subscriptions
            for topic, subscribers in self.topic_subscriptions.items():
                subscribers.discard(agent_id)

            logger.info("Agent unregistered: %s", agent_id)
            return True

        except Exception as e:
            logger.error("Error unregistering agent %s: %s", agent_id, e)
            return False

    async def join_group(self, agent_id: str, group_id: str) -> bool:
        """Add agent to a group"""
        try:
            if group_id not in self.group_subscriptions:
                self.group_subscriptions[group_id] = set()

            self.group_subscriptions[group_id].add(agent_id)
            logger.debug("Agent %s joined group %s", agent_id, group_id)
            return True

        except Exception as e:
            logger.error("Error joining group: %s", e)
            return False

    async def leave_group(self, agent_id: str, group_id: str) -> bool:
        """Remove agent from a group"""
        try:
            if group_id in self.group_subscriptions:
                self.group_subscriptions[group_id].discard(agent_id)
                # Clean up empty groups
                if not self.group_subscriptions[group_id]:
                    del self.group_subscriptions[group_id]

            logger.debug("Agent %s left group %s", agent_id, group_id)
            return True

        except Exception as e:
            logger.error("Error leaving group: %s", e)
            return False

    async def subscribe_topic(self, agent_id: str, topic: str) -> bool:
        """Subscribe agent to a topic"""
        try:
            if topic not in self.topic_subscriptions:
                self.topic_subscriptions[topic] = set()

            self.topic_subscriptions[topic].add(agent_id)
            logger.debug("Agent %s subscribed to topic %s", agent_id, topic)
            return True

        except Exception as e:
            logger.error("Error subscribing to topic: %s", e)
            return False

    async def unsubscribe_topic(self, agent_id: str, topic: str) -> bool:
        """Unsubscribe agent from a topic"""
        try:
            if topic in self.topic_subscriptions:
                self.topic_subscriptions[topic].discard(agent_id)
                # Clean up empty topics
                if not self.topic_subscriptions[topic]:
                    del self.topic_subscriptions[topic]

            logger.debug("Agent %s unsubscribed from topic %s", agent_id, topic)
            return True

        except Exception as e:
            logger.error("Error unsubscribing from topic: %s", e)
            return False

    async def _heartbeat_monitor(self) -> None:
        """Monitor agent heartbeats and cleanup stale connections"""
        heartbeat_timeout = 300  # 5 minutes

        while self.running:
            try:
                current_time = time.time()
                stale_agents = []

                for agent_id, last_heartbeat in self.agent_connections.items():
                    if current_time - last_heartbeat > heartbeat_timeout:
                        stale_agents.append(agent_id)

                # Clean up stale agents
                for agent_id in stale_agents:
                    await self.unregister_agent(agent_id)
                    logger.info("Removed stale agent: %s", agent_id)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat monitor: %s", e)
                await asyncio.sleep(60)

    async def _message_cleanup(self) -> None:
        """Clean up expired messages and old streams"""
        while self.running:
            try:
                # Clean up expired persistent messages
                current_time = time.time()

                # Get all persistent message keys
                pattern = "persistent:message:*"
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)

                # Check each message for expiration
                pipeline = self.redis_client.pipeline()
                for key in keys:
                    message_data = await self.redis_client.hgetall(key)
                    if message_data:
                        timestamp = float(message_data.get(b"timestamp", 0))
                        ttl = int(message_data.get(b"ttl", 0))

                        if ttl > 0 and current_time > (timestamp + ttl):
                            pipeline.delete(key)
                            self.stats.total_expired += 1

                if keys:
                    await pipeline.execute()

                await asyncio.sleep(300)  # Clean up every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in message cleanup: %s", e)
                await asyncio.sleep(300)

    async def _stats_updater(self) -> None:
        """Update statistics periodically"""
        while self.running:
            try:
                # Update connection stats
                info = await self.redis_client.info()

                # Update delivery time stats if we have processed messages
                # This would typically be calculated from actual delivery timestamps

                await asyncio.sleep(30)  # Update every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error updating stats: %s", e)
                await asyncio.sleep(30)

    async def get_stats(self) -> MessageStats:
        """Get current message bus statistics"""
        return self.stats

    async def get_agent_count(self) -> int:
        """Get number of connected agents"""
        return len(self.agent_connections)

    async def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs"""
        return list(self.agent_connections.keys())

    async def get_groups(self) -> Dict[str, List[str]]:
        """Get all groups and their members"""
        return {
            group_id: list(members)
            for group_id, members in self.group_subscriptions.items()
        }

    async def get_topics(self) -> Dict[str, List[str]]:
        """Get all topics and their subscribers"""
        return {
            topic: list(subscribers)
            for topic, subscribers in self.topic_subscriptions.items()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Get health status of the message bus"""
        try:
            # Test Redis connectivity
            ping_result = await self.redis_client.ping()
            redis_info = await self.redis_client.info()

            return {
                "status": "healthy" if ping_result else "unhealthy",
                "running": self.running,
                "connected_agents": len(self.agent_connections),
                "total_groups": len(self.group_subscriptions),
                "total_topics": len(self.topic_subscriptions),
                "redis_connected": ping_result,
                "redis_memory_used": redis_info.get("used_memory_human", "unknown"),
                "stats": self.stats.to_dict(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "running": self.running,
            }
