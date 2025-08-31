"""
Inter-agent messaging system for HECATON.

This module provides asynchronous message passing capabilities between agents
using a topic-based pub/sub pattern with direct messaging support.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message in the messaging system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: Optional[str] = None
    topic: str = ""
    payload: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Ensure id and timestamp are set."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class MessageBroker:
    """
    Asynchronous message broker for inter-agent communication.

    Provides topic-based publish/subscribe pattern and direct messaging
    with thread-safe operations using asyncio locks.
    """

    def __init__(self):
        """Initialize the message broker."""
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._direct_queues: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Start the message broker."""
        async with self._lock:
            if self._running:
                logger.warning("Message broker is already running")
                return
            self._running = True
            logger.info("Message broker started")

    async def stop(self):
        """Stop the message broker and cleanup resources."""
        async with self._lock:
            if not self._running:
                logger.warning("Message broker is not running")
                return

            self._running = False

            # Cancel all running tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)

            self._tasks.clear()
            self._queues.clear()
            self._subscribers.clear()
            self._direct_queues.clear()

            logger.info("Message broker stopped")

    async def publish(self, topic: str, message: Message):
        """
        Publish a message to a topic.

        Args:
            topic: The topic to publish to
            message: The message to publish
        """
        if not self._running:
            raise RuntimeError("Message broker is not running")

        async with self._lock:
            # Create topic queue if it doesn't exist
            if topic not in self._queues:
                self._queues[topic] = asyncio.Queue()

            # Set the topic in the message
            message.topic = topic

            # Put message in queue
            await self._queues[topic].put(message)

            # Notify subscribers
            if topic in self._subscribers:
                for callback in self._subscribers[topic]:
                    # Create task for async callback
                    task = asyncio.create_task(self._invoke_callback(callback, message))
                    self._tasks.append(task)

        logger.debug(f"Published message {message.id} to topic {topic}")

    async def subscribe(self, topic: str, callback: Callable[[Message], Any]):
        """
        Subscribe to a topic with a callback.

        Args:
            topic: The topic to subscribe to
            callback: Async callback function to invoke on message receipt
        """
        if not self._running:
            raise RuntimeError("Message broker is not running")

        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
                self._queues[topic] = asyncio.Queue()

            self._subscribers[topic].append(callback)

        logger.debug(f"Subscribed to topic {topic}")

    async def unsubscribe(self, topic: str, callback: Callable[[Message], Any]):
        """
        Unsubscribe a callback from a topic.

        Args:
            topic: The topic to unsubscribe from
            callback: The callback to remove
        """
        async with self._lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)

                # Clean up empty topics
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
                    if topic in self._queues:
                        del self._queues[topic]

        logger.debug(f"Unsubscribed from topic {topic}")

    async def send_direct(self, agent_id: str, message: Message):
        """
        Send a message directly to a specific agent.

        Args:
            agent_id: The ID of the agent to send to
            message: The message to send
        """
        if not self._running:
            raise RuntimeError("Message broker is not running")

        async with self._lock:
            # Create agent queue if it doesn't exist
            if agent_id not in self._direct_queues:
                self._direct_queues[agent_id] = asyncio.Queue()

            # Set the receiver in the message
            message.receiver = agent_id

            # Put message in queue
            await self._direct_queues[agent_id].put(message)

        logger.debug(f"Sent direct message {message.id} to agent {agent_id}")

    async def receive_direct(
        self, agent_id: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Receive a direct message for an agent.

        Args:
            agent_id: The ID of the agent receiving messages
            timeout: Optional timeout in seconds

        Returns:
            The next message in the queue, or None if timeout
        """
        if not self._running:
            raise RuntimeError("Message broker is not running")

        async with self._lock:
            if agent_id not in self._direct_queues:
                self._direct_queues[agent_id] = asyncio.Queue()
            queue = self._direct_queues[agent_id]

        try:
            if timeout is not None:
                message = await asyncio.wait_for(queue.get(), timeout)
            else:
                message = await queue.get()

            logger.debug(f"Agent {agent_id} received message {message.id}")
            return message

        except asyncio.TimeoutError:
            return None

    async def get_topic_messages(self, topic: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from a topic queue without consuming them.

        Args:
            topic: The topic to get messages from
            limit: Maximum number of messages to return

        Returns:
            List of messages in the topic queue
        """
        async with self._lock:
            if topic not in self._queues:
                return []

            queue = self._queues[topic]
            messages = []

            # Temporarily get all messages
            temp_messages = []
            while not queue.empty():
                msg = await queue.get()
                temp_messages.append(msg)
                messages.append(msg)

                if limit and len(messages) >= limit:
                    break

            # Put messages back
            for msg in temp_messages:
                await queue.put(msg)

            return messages

    async def clear_topic(self, topic: str):
        """
        Clear all messages from a topic queue.

        Args:
            topic: The topic to clear
        """
        async with self._lock:
            if topic in self._queues:
                self._queues[topic] = asyncio.Queue()

        logger.debug(f"Cleared topic {topic}")

    async def get_topics(self) -> Set[str]:
        """
        Get all active topics.

        Returns:
            Set of topic names
        """
        async with self._lock:
            return set(self._queues.keys())

    async def get_agents(self) -> Set[str]:
        """
        Get all agents with direct message queues.

        Returns:
            Set of agent IDs
        """
        async with self._lock:
            return set(self._direct_queues.keys())

    async def _invoke_callback(self, callback: Callable, message: Message):
        """
        Invoke a callback with error handling.

        Args:
            callback: The callback to invoke
            message: The message to pass
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            logger.error(f"Error in callback for message {message.id}: {e}")
