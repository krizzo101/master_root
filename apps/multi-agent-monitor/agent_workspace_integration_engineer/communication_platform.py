"""
Agent Communication Platform
Main integration bringing together all components
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from collaboration_protocols import CollaborationProtocols
from interfaces import AgentInfo, AgentStatus, Message, MessageType
from knowledge_base import KnowledgeBase
from message_bus import MessageBus


class CommunicationPlatform:
    """Integrated platform for agent communication and collaboration"""

    def __init__(self, workspace_path: Path = None):
        self.workspace = workspace_path or Path("/home/opsvi/agent_shared/platform")
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.message_bus = MessageBus(self.workspace / "messages")
        self.knowledge_base = KnowledgeBase(self.workspace / "knowledge")
        self.protocols = CollaborationProtocols(self.message_bus)

        # Platform metrics
        self.metrics = {
            "messages_sent": 0,
            "agents_registered": 0,
            "knowledge_entries": 0,
            "active_collaborations": 0,
        }

    async def register_agent(
        self, agent_id: str, name: str, capabilities: List[str]
    ) -> "AgentClient":
        """Register an agent and return a client for communication"""

        agent_info = AgentInfo(
            id=agent_id,
            name=name,
            capabilities=set(capabilities),
            status=AgentStatus.IDLE,
            workload=0,
        )

        success = await self.message_bus.register_agent(agent_info)

        if success:
            self.metrics["agents_registered"] += 1
            return AgentClient(self, agent_info)

        return None

    def get_platform_status(self) -> Dict:
        """Get platform health and metrics"""
        return {
            "status": "operational",
            "metrics": self.metrics,
            "active_agents": len(self.message_bus.agents),
            "message_queue_sizes": {
                agent_id: queue.qsize()
                for agent_id, queue in self.message_bus.message_queues.items()
            },
            "knowledge_entries": len(self.knowledge_base.knowledge),
        }


class AgentClient:
    """Client interface for agents to use the platform"""

    def __init__(self, platform: CommunicationPlatform, agent_info: AgentInfo):
        self.platform = platform
        self.agent_info = agent_info
        self.received_messages: List[Message] = []

    async def send_message(
        self, recipient: Optional[str], topic: str, content: Dict, priority: int = 5
    ) -> bool:
        """Send a message to another agent or broadcast"""

        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            sender=self.agent_info.id,
            recipient=recipient,
            topic=topic,
            content=content,
            timestamp=datetime.utcnow(),
            priority=priority,
        )

        success = await self.platform.message_bus.send_message(message)
        if success:
            self.platform.metrics["messages_sent"] += 1

        return success

    async def receive_messages(self) -> List[Message]:
        """Check for new messages"""
        messages = await self.platform.message_bus.receive_messages(self.agent_info.id)
        self.received_messages.extend(messages)
        return messages

    async def share_knowledge(self, topic: str, knowledge: Dict) -> str:
        """Share knowledge with other agents"""
        knowledge["agent_id"] = self.agent_info.id
        knowledge_id = await self.platform.knowledge_base.store_knowledge(
            topic, knowledge
        )

        if knowledge_id:
            self.platform.metrics["knowledge_entries"] += 1

        return knowledge_id

    async def query_knowledge(self, query: str) -> List[Dict]:
        """Search the knowledge base"""
        return await self.platform.knowledge_base.query_knowledge(query)

    async def find_expert(self, topic: str) -> Optional[str]:
        """Find an expert on a topic"""
        return await self.platform.knowledge_base.get_expert(topic)

    async def request_help(self, capability: str, task_details: Dict) -> bool:
        """Request help from agents with specific capability"""

        # Find capable agents
        capable_agents = [
            agent_id
            for agent_id, agent in self.platform.message_bus.agents.items()
            if capability in agent.capabilities and agent.status == AgentStatus.IDLE
        ]

        if not capable_agents:
            return False

        # Send help request to first available
        return await self.send_message(
            recipient=capable_agents[0],
            topic="help_request",
            content={"capability": capability, "task": task_details},
            priority=7,
        )

    async def request_review(self, artifact: Dict, reviewers: List[str]) -> str:
        """Request peer review of work"""
        artifact["author"] = self.agent_info.id
        review_id = await self.platform.protocols.request_review(artifact, reviewers)

        if review_id:
            self.platform.metrics["active_collaborations"] += 1

        return review_id

    async def update_status(self, status: AgentStatus, workload: int = None):
        """Update agent status"""
        self.agent_info.status = status
        if workload is not None:
            self.agent_info.workload = workload

        # Broadcast status update
        await self.send_message(
            recipient=None,
            topic="status_update",
            content={
                "agent_id": self.agent_info.id,
                "status": status.value,
                "workload": self.agent_info.workload,
            },
        )


# Import required for client
import uuid
from datetime import datetime
