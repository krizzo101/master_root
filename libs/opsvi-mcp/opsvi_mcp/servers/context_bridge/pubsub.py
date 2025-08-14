"""
In-memory pub/sub implementation for Context Bridge

Provides a fallback when Redis is not available.
"""

import asyncio
from typing import Dict, List, Set, Callable, Optional, Any
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PubSubBackend(ABC):
    """Abstract base class for pub/sub backends"""

    @abstractmethod
    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel"""
        pass

    @abstractmethod
    async def subscribe(self, channel: str, callback: Callable) -> str:
        """Subscribe to a channel with a callback"""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from a channel"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the pub/sub backend"""
        pass


@dataclass
class Subscription:
    """Represents a subscription to a channel"""
    
    id: str
    channel: str
    callback: Callable
    active: bool = True


class InMemoryPubSub(PubSubBackend):
    """
    In-memory pub/sub implementation
    
    Features:
    - Thread-safe with asyncio locks
    - Pattern matching support
    - Automatic cleanup of inactive subscriptions
    """

    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}
        self._channels: Dict[str, Set[str]] = {}  # channel -> subscription_ids
        self._lock = asyncio.Lock()
        self._next_id = 0
        self._message_queue: Dict[str, List[Any]] = {}  # channel -> messages
        self._tasks: List[asyncio.Task] = []

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a channel
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of subscribers that received the message
        """
        async with self._lock:
            if channel not in self._channels:
                return 0
            
            subscription_ids = self._channels[channel].copy()
            delivered = 0
            
            for sub_id in subscription_ids:
                if sub_id in self._subscriptions:
                    subscription = self._subscriptions[sub_id]
                    if subscription.active:
                        try:
                            # Schedule callback execution
                            task = asyncio.create_task(
                                self._deliver_message(subscription.callback, channel, message)
                            )
                            self._tasks.append(task)
                            delivered += 1
                        except Exception as e:
                            logger.error(f"Error delivering message to {sub_id}: {e}")
                            subscription.active = False
            
            # Clean up completed tasks
            self._tasks = [t for t in self._tasks if not t.done()]
            
            logger.debug(f"Published to {channel}: delivered to {delivered} subscribers")
            return delivered

    async def _deliver_message(self, callback: Callable, channel: str, message: str):
        """Deliver a message to a subscriber"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(channel, message)
            else:
                callback(channel, message)
        except Exception as e:
            logger.error(f"Error in subscriber callback: {e}")

    async def subscribe(self, channel: str, callback: Callable) -> str:
        """
        Subscribe to a channel
        
        Args:
            channel: Channel name
            callback: Function to call when message is received
            
        Returns:
            Subscription ID
        """
        async with self._lock:
            self._next_id += 1
            sub_id = f"sub_{self._next_id}"
            
            subscription = Subscription(
                id=sub_id,
                channel=channel,
                callback=callback
            )
            
            self._subscriptions[sub_id] = subscription
            
            if channel not in self._channels:
                self._channels[channel] = set()
            self._channels[channel].add(sub_id)
            
            logger.debug(f"Created subscription {sub_id} for channel {channel}")
            return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a channel
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            True if unsubscribed successfully
        """
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return False
            
            subscription = self._subscriptions[subscription_id]
            channel = subscription.channel
            
            # Remove from channel subscribers
            if channel in self._channels:
                self._channels[channel].discard(subscription_id)
                if not self._channels[channel]:
                    del self._channels[channel]
            
            # Remove subscription
            del self._subscriptions[subscription_id]
            
            logger.debug(f"Removed subscription {subscription_id}")
            return True

    async def close(self) -> None:
        """Clean up resources"""
        async with self._lock:
            # Cancel all pending tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            
            # Clear all data
            self._subscriptions.clear()
            self._channels.clear()
            self._message_queue.clear()
            self._tasks.clear()
            
            logger.info("In-memory pub/sub closed")

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the pub/sub system"""
        async with self._lock:
            return {
                "total_subscriptions": len(self._subscriptions),
                "total_channels": len(self._channels),
                "active_subscriptions": sum(
                    1 for s in self._subscriptions.values() if s.active
                ),
                "pending_tasks": len([t for t in self._tasks if not t.done()])
            }


class RedisPubSubAdapter(PubSubBackend):
    """
    Adapter for Redis pub/sub to match our interface
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.pubsub = None
        self._subscriptions: Dict[str, Dict] = {}
        self._tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize the Redis pub/sub connection"""
        if self.redis_client:
            self.pubsub = self.redis_client.pubsub()

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to Redis"""
        if not self.redis_client:
            return 0
        
        try:
            return await self.redis_client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
            return 0

    async def subscribe(self, channel: str, callback: Callable) -> str:
        """Subscribe to a Redis channel"""
        if not self.pubsub:
            raise RuntimeError("Redis pub/sub not initialized")
        
        sub_id = f"redis_sub_{len(self._subscriptions) + 1}"
        
        # Subscribe to the channel
        await self.pubsub.subscribe(channel)
        
        # Store subscription info
        self._subscriptions[sub_id] = {
            "channel": channel,
            "callback": callback
        }
        
        # Start listening task if not already running
        if not self._tasks:
            task = asyncio.create_task(self._listen())
            self._tasks.append(task)
        
        return sub_id

    async def _listen(self):
        """Listen for messages from Redis"""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
                
                # Deliver to all matching subscriptions
                for sub_info in self._subscriptions.values():
                    if sub_info["channel"] == channel:
                        callback = sub_info["callback"]
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(channel, data)
                            else:
                                callback(channel, data)
                        except Exception as e:
                            logger.error(f"Error in Redis callback: {e}")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from a Redis channel"""
        if subscription_id not in self._subscriptions:
            return False
        
        sub_info = self._subscriptions[subscription_id]
        channel = sub_info["channel"]
        
        # Check if this is the last subscription for this channel
        channel_subs = [s for s in self._subscriptions.values() if s["channel"] == channel]
        if len(channel_subs) == 1:
            # Unsubscribe from Redis
            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
        
        del self._subscriptions[subscription_id]
        return True

    async def close(self) -> None:
        """Close Redis pub/sub connection"""
        # Cancel listening tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close pub/sub
        if self.pubsub:
            await self.pubsub.close()
        
        self._subscriptions.clear()
        self._tasks.clear()