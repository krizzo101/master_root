"""Enhanced message bus with retry logic, load balancing, and advanced routing.

This module extends the basic message bus with:
- Intelligent message retry mechanisms with exponential backoff
- Load balancing for multi-agent routing
- Message acknowledgments and delivery guarantees
- Event streaming and aggregation capabilities
- Dead letter queue for failed messages
- Message compression and optimization
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from statistics import mean
from typing import Any, Callable, Dict, List, Optional, Set

from src.agents.base_agent import AgentMessage, MessageType

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class DeliveryMode(Enum):
    """Message delivery modes."""

    FIRE_AND_FORGET = "fire_and_forget"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class RoutingStrategy(Enum):
    """Strategies for routing messages to multiple agents."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    RANDOM = "random"
    CAPABILITY_MATCH = "capability_match"


@dataclass
class MessageEnvelope:
    """Enhanced message envelope with delivery tracking."""

    message: AgentMessage
    priority: MessagePriority = MessagePriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    max_retries: int = 3
    retry_delay: float = 1.0
    ttl_seconds: int = 300

    # Tracking fields
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if message has expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry_time

    @property
    def next_retry_at(self) -> datetime:
        """Calculate next retry time."""
        if not self.last_attempt_at:
            return datetime.now(timezone.utc)

        delay = self.retry_delay * (2 ** (self.attempts - 1))  # Exponential backoff
        return self.last_attempt_at + timedelta(seconds=delay)


@dataclass
class AgentInfo:
    """Information about registered agents."""

    agent_id: str
    capabilities: List[str]
    load_factor: float = 0.0  # Current load (0.0 = idle, 1.0 = fully loaded)
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_handler: Optional[Callable] = None
    is_active: bool = True

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new messages."""
        return (
            self.is_active
            and self.message_handler is not None
            and self.load_factor < 0.9  # Don't send to overloaded agents
        )


class MessageAcknowledgment:
    """Message acknowledgment system."""

    def __init__(self):
        """Initialize acknowledgment tracker."""
        self.pending_acks: Dict[str, MessageEnvelope] = {}
        self.ack_timeout = 30.0  # seconds

    def register_message(self, envelope: MessageEnvelope) -> None:
        """Register message for acknowledgment tracking."""
        if envelope.delivery_mode in [
            DeliveryMode.AT_LEAST_ONCE,
            DeliveryMode.EXACTLY_ONCE,
        ]:
            self.pending_acks[envelope.envelope_id] = envelope

    def acknowledge_message(self, envelope_id: str) -> bool:
        """Acknowledge message delivery."""
        if envelope_id in self.pending_acks:
            envelope = self.pending_acks.pop(envelope_id)
            envelope.delivered_at = datetime.now(timezone.utc)
            return True
        return False

    def get_timed_out_messages(self) -> List[MessageEnvelope]:
        """Get messages that have timed out waiting for acknowledgment."""
        timeout_threshold = datetime.now(timezone.utc) - timedelta(
            seconds=self.ack_timeout
        )

        timed_out = []
        for envelope_id, envelope in list(self.pending_acks.items()):
            if (
                envelope.last_attempt_at
                and envelope.last_attempt_at < timeout_threshold
            ):
                timed_out.append(envelope)

        return timed_out


class LoadBalancer:
    """Load balancer for distributing messages across agents."""

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.LEAST_BUSY):
        """Initialize load balancer with routing strategy."""
        self.strategy = strategy
        self.round_robin_counters: Dict[str, int] = defaultdict(int)

    def select_agent(
        self, agents: List[AgentInfo], required_capabilities: Optional[List[str]] = None
    ) -> Optional[AgentInfo]:
        """Select best agent based on routing strategy."""
        # Filter available agents
        available_agents = [agent for agent in agents if agent.is_available]

        # Filter by capabilities if specified
        if required_capabilities:
            available_agents = [
                agent
                for agent in available_agents
                if all(cap in agent.capabilities for cap in required_capabilities)
            ]

        if not available_agents:
            return None

        # Apply routing strategy
        if self.strategy == RoutingStrategy.LEAST_BUSY:
            return min(available_agents, key=lambda a: a.load_factor)

        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            capability_key = ":".join(sorted(required_capabilities or []))
            counter = self.round_robin_counters[capability_key]
            selected_agent = available_agents[counter % len(available_agents)]
            self.round_robin_counters[capability_key] += 1
            return selected_agent

        elif self.strategy == RoutingStrategy.RANDOM:
            import random

            return random.choice(available_agents)

        elif self.strategy == RoutingStrategy.CAPABILITY_MATCH:
            # Score agents by capability match
            def capability_score(agent: AgentInfo) -> float:
                if not required_capabilities:
                    return 1.0
                matches = sum(
                    1 for cap in required_capabilities if cap in agent.capabilities
                )
                return matches / len(required_capabilities)

            return max(available_agents, key=capability_score)

        return available_agents[0]  # Fallback to first available


class DeadLetterQueue:
    """Queue for messages that failed to deliver."""

    def __init__(self, max_size: int = 1000):
        """Initialize dead letter queue."""
        self.max_size = max_size
        self.messages: deque = deque(maxlen=max_size)
        self.logger = logging.getLogger(f"{__name__}.DeadLetterQueue")

    def add_message(self, envelope: MessageEnvelope, error: str) -> None:
        """Add failed message to dead letter queue."""
        envelope.failed_at = datetime.now(timezone.utc)
        envelope.error_message = error

        self.messages.append(envelope)
        self.logger.warning(
            f"Message {envelope.envelope_id} added to dead letter queue: {error}"
        )

    def get_messages(self, limit: Optional[int] = None) -> List[MessageEnvelope]:
        """Get messages from dead letter queue."""
        if limit:
            return list(self.messages)[-limit:]
        return list(self.messages)

    def replay_message(self, envelope_id: str) -> Optional[MessageEnvelope]:
        """Remove and return message for replay."""
        for i, envelope in enumerate(self.messages):
            if envelope.envelope_id == envelope_id:
                # Reset for replay
                envelope.attempts = 0
                envelope.last_attempt_at = None
                envelope.failed_at = None
                envelope.error_message = None

                # Remove from dead letter queue
                del self.messages[i]
                return envelope

        return None


class MessageCompression:
    """Message compression utilities using secure JSON serialization."""

    @staticmethod
    def should_compress(data: bytes, threshold: int = 1024) -> bool:
        """Check if data should be compressed."""
        return len(data) > threshold

    @staticmethod
    def compress_message(message: AgentMessage) -> bytes:
        """Compress message data using secure JSON serialization."""
        # Use JSON instead of pickle for security
        message_dict = {
            "id": message.id,
            "type": message.type.value,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "content": message.content,
            "created_at": message.created_at.isoformat()
            if message.created_at
            else None,
            "correlation_id": message.correlation_id,
            "metadata": message.metadata,
        }

        serialized = json.dumps(message_dict).encode("utf-8")

        if MessageCompression.should_compress(serialized):
            return gzip.compress(serialized)

        return serialized

    @staticmethod
    def decompress_message(data: bytes) -> AgentMessage:
        """Decompress message data using secure JSON deserialization."""
        try:
            # Try to decompress first
            decompressed = gzip.decompress(data)
            message_dict = json.loads(decompressed.decode("utf-8"))
        except (gzip.BadGzipFile, OSError):
            # Not compressed, load directly
            message_dict = json.loads(data.decode("utf-8"))

        # Reconstruct AgentMessage object

        return AgentMessage(
            type=MessageType(message_dict["type"]),
            content=message_dict["content"],
            sender_id=message_dict["sender_id"],
            recipient_id=message_dict["recipient_id"],
            correlation_id=message_dict["correlation_id"],
            metadata=message_dict["metadata"],
        )


class EnhancedMessageBus:
    """Enhanced message bus with retry logic and advanced features."""

    def __init__(
        self,
        routing_strategy: RoutingStrategy = RoutingStrategy.LEAST_BUSY,
        enable_compression: bool = True,
        max_queue_size: int = 10000,
    ):
        """Initialize enhanced message bus.

        Args:
            routing_strategy: Strategy for load balancing
            enable_compression: Whether to compress large messages
            max_queue_size: Maximum size of message queues
        """
        self.routing_strategy = routing_strategy
        self.enable_compression = enable_compression
        self.max_queue_size = max_queue_size

        # Core components
        self.agents: Dict[str, AgentInfo] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> agent_ids

        # Enhanced features
        self.load_balancer = LoadBalancer(routing_strategy)
        self.acknowledgments = MessageAcknowledgment()
        self.dead_letter_queue = DeadLetterQueue()

        # Background tasks
        self.running = False
        self.background_tasks: List[asyncio.Task] = []

        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "retries_attempted": 0,
            "compression_savings": 0,
        }

        self.logger = logging.getLogger(f"{__name__}.EnhancedMessageBus")

    async def start(self) -> None:
        """Start the message bus background tasks."""
        if self.running:
            return

        self.running = True

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._retry_loop()),
            asyncio.create_task(self._acknowledgment_timeout_loop()),
            asyncio.create_task(self._load_monitoring_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]

        self.logger.info("Enhanced message bus started")

    async def stop(self) -> None:
        """Stop the message bus and cleanup."""
        if not self.running:
            return

        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.background_tasks.clear()
        self.logger.info("Enhanced message bus stopped")

    async def register_agent(
        self,
        agent_id: str,
        handler: Callable[[AgentMessage], None],
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """Register an agent with the message bus."""
        agent_info = AgentInfo(
            agent_id=agent_id, capabilities=capabilities or [], message_handler=handler
        )

        self.agents[agent_id] = agent_info
        self.message_queues[agent_id] = asyncio.Queue(maxsize=self.max_queue_size)

        # Start message processing for this agent
        task = asyncio.create_task(self._process_agent_messages(agent_id))
        self.background_tasks.append(task)

        self.logger.info(
            f"Agent {agent_id} registered with capabilities: {capabilities}"
        )

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the message bus."""
        if agent_id in self.agents:
            self.agents[agent_id].is_active = False
            # Queue and tasks will be cleaned up by cleanup loop

            self.logger.info(f"Agent {agent_id} unregistered")

    async def send_message(
        self,
        message: AgentMessage,
        priority: MessagePriority = MessagePriority.NORMAL,
        delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET,
        max_retries: int = 3,
        required_capabilities: Optional[List[str]] = None,
    ) -> bool:
        """Send a message through the bus with enhanced delivery options."""
        envelope = MessageEnvelope(
            message=message,
            priority=priority,
            delivery_mode=delivery_mode,
            max_retries=max_retries,
        )

        self.stats["messages_sent"] += 1

        try:
            success = await self._deliver_message(envelope, required_capabilities)

            if success:
                self.stats["messages_delivered"] += 1
            else:
                self.stats["messages_failed"] += 1

            return success

        except Exception as e:
            self.logger.error(f"Failed to send message {envelope.envelope_id}: {e}")
            self.stats["messages_failed"] += 1
            return False

    async def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic."""
        self.subscriptions[topic].add(agent_id)
        self.logger.debug(f"Agent {agent_id} subscribed to topic {topic}")

    async def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic."""
        self.subscriptions[topic].discard(agent_id)
        self.logger.debug(f"Agent {agent_id} unsubscribed from topic {topic}")

    async def publish_event(
        self,
        topic: str,
        event_data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """Publish an event to all subscribers of a topic."""
        subscribers = self.subscriptions.get(topic, set())

        if not subscribers:
            return 0

        # Create event message
        event_message = AgentMessage(
            type=MessageType.NOTIFICATION,
            content={
                "topic": topic,
                "event_data": event_data,
                "published_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Send to all subscribers
        success_count = 0
        for agent_id in subscribers:
            event_message.recipient_id = agent_id

            envelope = MessageEnvelope(
                message=event_message,
                priority=priority,
                delivery_mode=DeliveryMode.AT_LEAST_ONCE,
            )

            if await self._deliver_message_to_agent(envelope, agent_id):
                success_count += 1

        return success_count

    def get_agent_load(self, agent_id: str) -> float:
        """Get current load factor for an agent."""
        if agent_id in self.agents:
            return self.agents[agent_id].load_factor
        return 0.0

    def update_agent_capabilities(self, agent_id: str, capabilities: List[str]) -> None:
        """Update agent capabilities."""
        if agent_id in self.agents:
            self.agents[agent_id].capabilities = capabilities
            self.logger.debug(
                f"Updated capabilities for agent {agent_id}: {capabilities}"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        active_agents = sum(1 for agent in self.agents.values() if agent.is_active)
        total_queue_size = sum(queue.qsize() for queue in self.message_queues.values())

        return {
            **self.stats,
            "active_agents": active_agents,
            "total_agents": len(self.agents),
            "queue_depth": total_queue_size,
            "dead_letter_count": len(self.dead_letter_queue.messages),
            "pending_acks": len(self.acknowledgments.pending_acks),
            "average_load": mean([agent.load_factor for agent in self.agents.values()])
            if self.agents
            else 0.0,
        }

    def get_dead_letter_messages(self) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue for inspection."""
        return [
            {
                "envelope_id": envelope.envelope_id,
                "message_id": envelope.message.id,
                "message_type": envelope.message.type.value,
                "attempts": envelope.attempts,
                "failed_at": envelope.failed_at.isoformat()
                if envelope.failed_at
                else None,
                "error": envelope.error_message,
            }
            for envelope in self.dead_letter_queue.get_messages()
        ]

    async def replay_dead_letter_message(self, envelope_id: str) -> bool:
        """Replay a message from the dead letter queue."""
        envelope = self.dead_letter_queue.replay_message(envelope_id)

        if envelope:
            success = await self._deliver_message(envelope)
            if success:
                self.logger.info(f"Successfully replayed message {envelope_id}")
            return success

        return False

    # Internal methods

    async def _deliver_message(
        self,
        envelope: MessageEnvelope,
        required_capabilities: Optional[List[str]] = None,
    ) -> bool:
        """Deliver message to appropriate agent(s)."""
        message = envelope.message

        # Direct delivery to specific recipient
        if message.recipient_id:
            return await self._deliver_message_to_agent(envelope, message.recipient_id)

        # Load balanced delivery
        available_agents = [
            agent for agent in self.agents.values() if agent.is_available
        ]

        selected_agent = self.load_balancer.select_agent(
            available_agents, required_capabilities
        )

        if not selected_agent:
            self.logger.warning(
                f"No available agents for message {envelope.envelope_id}"
            )
            self.dead_letter_queue.add_message(envelope, "No available agents")
            return False

        return await self._deliver_message_to_agent(envelope, selected_agent.agent_id)

    async def _deliver_message_to_agent(
        self, envelope: MessageEnvelope, agent_id: str
    ) -> bool:
        """Deliver message to a specific agent."""
        if agent_id not in self.agents or not self.agents[agent_id].is_available:
            return False

        try:
            envelope.attempts += 1
            envelope.last_attempt_at = datetime.now(timezone.utc)

            # Add to agent's message queue
            queue = self.message_queues[agent_id]

            # Check queue capacity
            if queue.full():
                self.logger.warning(f"Queue full for agent {agent_id}")
                return False

            # Register for acknowledgment if needed
            self.acknowledgments.register_message(envelope)

            # Add message to queue
            await queue.put(envelope)

            return True

        except Exception as e:
            self.logger.error(f"Failed to deliver message to agent {agent_id}: {e}")
            return False

    async def _process_agent_messages(self, agent_id: str) -> None:
        """Process messages for a specific agent."""
        queue = self.message_queues[agent_id]

        while self.running:
            try:
                # Get message from queue
                envelope = await asyncio.wait_for(queue.get(), timeout=1.0)

                # Check if agent is still active
                if agent_id not in self.agents or not self.agents[agent_id].is_active:
                    # Requeue message for retry
                    if envelope.attempts < envelope.max_retries:
                        await asyncio.sleep(envelope.retry_delay)
                        await self._deliver_message(envelope)
                    else:
                        self.dead_letter_queue.add_message(
                            envelope, "Agent became inactive"
                        )
                    continue

                # Get message handler
                agent_info = self.agents[agent_id]
                handler = agent_info.message_handler

                if not handler:
                    self.dead_letter_queue.add_message(envelope, "No message handler")
                    continue

                # Update agent load
                start_time = time.time()

                try:
                    # Deliver message to handler
                    if asyncio.iscoroutinefunction(handler):
                        await handler(envelope.message)
                    else:
                        handler(envelope.message)

                    # Update load based on processing time
                    processing_time = time.time() - start_time
                    self._update_agent_load(agent_id, processing_time)

                    # Mark as delivered
                    envelope.delivered_at = datetime.now(timezone.utc)

                    # Auto-acknowledge for fire-and-forget
                    if envelope.delivery_mode == DeliveryMode.FIRE_AND_FORGET:
                        self.acknowledgments.acknowledge_message(envelope.envelope_id)

                except Exception as e:
                    self.logger.error(f"Handler error for agent {agent_id}: {e}")

                    # Retry if possible
                    if (
                        envelope.attempts < envelope.max_retries
                        and not envelope.is_expired
                    ):
                        await asyncio.sleep(envelope.retry_delay)
                        await self._deliver_message(envelope)
                        self.stats["retries_attempted"] += 1
                    else:
                        self.dead_letter_queue.add_message(envelope, str(e))

            except asyncio.TimeoutError:
                # Normal timeout, continue
                continue
            except Exception as e:
                self.logger.error(f"Message processing error for agent {agent_id}: {e}")
                await asyncio.sleep(1)

    def _update_agent_load(self, agent_id: str, processing_time: float) -> None:
        """Update agent load factor based on processing time."""
        if agent_id in self.agents:
            # Simple load calculation based on processing time
            # This is a basic implementation - could be enhanced with more sophisticated metrics
            current_load = self.agents[agent_id].load_factor

            # Normalize processing time to load factor (0.0 to 1.0)
            time_factor = min(processing_time / 10.0, 1.0)  # 10 seconds = full load

            # Exponential moving average
            alpha = 0.1
            new_load = alpha * time_factor + (1 - alpha) * current_load

            self.agents[agent_id].load_factor = new_load

    async def _retry_loop(self) -> None:
        """Background task for handling message retries."""
        while self.running:
            try:
                # Check for timed out acknowledgments
                timed_out = self.acknowledgments.get_timed_out_messages()

                for envelope in timed_out:
                    if (
                        envelope.attempts < envelope.max_retries
                        and not envelope.is_expired
                    ):
                        await self._deliver_message(envelope)
                        self.stats["retries_attempted"] += 1
                    else:
                        self.acknowledgments.acknowledge_message(envelope.envelope_id)
                        self.dead_letter_queue.add_message(
                            envelope, "Acknowledgment timeout"
                        )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Retry loop error: {e}")
                await asyncio.sleep(5)

    async def _acknowledgment_timeout_loop(self) -> None:
        """Background task for handling acknowledgment timeouts."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                # Timeout handling is done in retry loop

            except Exception as e:
                self.logger.error(f"Acknowledgment timeout loop error: {e}")
                await asyncio.sleep(5)

    async def _load_monitoring_loop(self) -> None:
        """Background task for monitoring agent loads and health."""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)

                # Check agent heartbeats and update availability
                for agent_id, agent_info in self.agents.items():
                    time_since_heartbeat = current_time - agent_info.last_heartbeat

                    # Mark agent as inactive if no heartbeat for 5 minutes
                    if time_since_heartbeat.total_seconds() > 300:
                        agent_info.is_active = False
                        self.logger.warning(
                            f"Agent {agent_id} marked inactive due to missing heartbeat"
                        )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Load monitoring error: {e}")
                await asyncio.sleep(10)

    async def _cleanup_loop(self) -> None:
        """Background task for general cleanup."""
        while self.running:
            try:
                # Clean up inactive agents
                inactive_agents = [
                    agent_id
                    for agent_id, agent_info in self.agents.items()
                    if not agent_info.is_active
                ]

                for agent_id in inactive_agents:
                    # Remove after 1 hour of inactivity
                    last_heartbeat = self.agents[agent_id].last_heartbeat
                    if (
                        datetime.now(timezone.utc) - last_heartbeat
                    ).total_seconds() > 3600:
                        del self.agents[agent_id]
                        if agent_id in self.message_queues:
                            del self.message_queues[agent_id]

                        self.logger.info(f"Cleaned up inactive agent {agent_id}")

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(30)
