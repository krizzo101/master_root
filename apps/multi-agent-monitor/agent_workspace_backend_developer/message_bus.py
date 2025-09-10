"""
Message Bus Implementation
Core messaging infrastructure for agent communication
"""

import asyncio
import json
import uuid
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from interfaces import (
    AgentInfo,
    AgentStatus,
    ICommunicationPlatform,
    Message,
    MessageType,
)


class MessageBus(ICommunicationPlatform):
    """Central message routing system"""

    def __init__(self, persistence_path: Path = None):
        self.agents: Dict[str, AgentInfo] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[Message] = []
        self.persistence_path = persistence_path or Path("/tmp/agent_messages")
        self.persistence_path.mkdir(parents=True, exist_ok=True)

    async def register_agent(self, agent: AgentInfo) -> bool:
        """Register an agent with the platform"""
        try:
            self.agents[agent.id] = agent
            self.message_queues[agent.id] = asyncio.Queue()

            # Auto-subscribe to own channel and broadcast
            self.subscriptions[f"agent.{agent.id}"].add(agent.id)
            self.subscriptions["broadcast"].add(agent.id)

            # Log registration
            await self._persist_event(
                "agent_registered",
                {"agent_id": agent.id, "capabilities": list(agent.capabilities)},
            )

            return True
        except Exception as e:
            print(f"Registration failed: {e}")
            return False

    async def send_message(self, message: Message) -> bool:
        """Route a message to recipient(s)"""
        try:
            # Add timestamp if not set
            if not message.timestamp:
                message.timestamp = datetime.utcnow()

            # Store in history
            self.message_history.append(message)

            # Route based on recipient
            if message.recipient:
                # Direct message
                if message.recipient in self.message_queues:
                    await self.message_queues[message.recipient].put(message)
            else:
                # Topic-based routing
                if message.topic in self.subscriptions:
                    for subscriber_id in self.subscriptions[message.topic]:
                        if subscriber_id != message.sender:
                            await self.message_queues[subscriber_id].put(message)

            # Persist message
            await self._persist_message(message)
            return True

        except Exception as e:
            print(f"Message send failed: {e}")
            return False

    async def receive_messages(self, agent_id: str) -> List[Message]:
        """Get pending messages for an agent"""
        messages = []

        if agent_id not in self.message_queues:
            return messages

        queue = self.message_queues[agent_id]

        # Non-blocking receive of all pending messages
        while not queue.empty():
            try:
                message = queue.get_nowait()
                messages.append(message)
            except asyncio.QueueEmpty:
                break

        return messages

    async def subscribe(self, agent_id: str, topic: str) -> bool:
        """Subscribe agent to a topic"""
        try:
            self.subscriptions[topic].add(agent_id)
            return True
        except Exception:
            return False

    async def broadcast(self, message: Message) -> int:
        """Broadcast to all agents"""
        message.topic = "broadcast"
        message.recipient = None

        count = 0
        for agent_id in self.agents:
            if agent_id != message.sender:
                await self.message_queues[agent_id].put(message)
                count += 1

        return count

    async def _persist_message(self, message: Message):
        """Save message to disk"""
        filepath = (
            self.persistence_path
            / f"messages_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        )

        message_dict = asdict(message)
        message_dict["timestamp"] = message_dict["timestamp"].isoformat()

        with open(filepath, "a") as f:
            f.write(json.dumps(message_dict) + "\n")

    async def _persist_event(self, event_type: str, data: Dict):
        """Log system events"""
        filepath = self.persistence_path / "events.jsonl"

        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        with open(filepath, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get current status of an agent"""
        if agent_id in self.agents:
            return self.agents[agent_id].status
        return None

    def get_active_agents(self) -> List[str]:
        """Get list of active agents"""
        return [
            agent_id
            for agent_id, agent in self.agents.items()
            if agent.status != AgentStatus.OFFLINE
        ]
