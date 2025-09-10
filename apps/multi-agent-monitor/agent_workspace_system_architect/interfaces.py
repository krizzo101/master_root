"""
Agent Communication Platform Interface Definitions
Defines contracts that all components must follow
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MessageType(Enum):
    """Types of messages agents can exchange"""

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"
    ERROR = "error"


class AgentStatus(Enum):
    """Agent status states"""

    IDLE = "idle"
    BUSY = "busy"
    BLOCKED = "blocked"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Message:
    """Standard message format for agent communication"""

    id: str
    type: MessageType
    sender: str
    recipient: Optional[str]
    topic: str
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 5


@dataclass
class AgentInfo:
    """Agent registration information"""

    id: str
    name: str
    capabilities: Set[str]
    status: AgentStatus
    workload: int  # 0-100


class ICommunicationPlatform(ABC):
    """Interface for the communication platform"""

    @abstractmethod
    async def register_agent(self, agent: AgentInfo) -> bool:
        """Register an agent with the platform"""
        pass

    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        """Send a message through the platform"""
        pass

    @abstractmethod
    async def receive_messages(self, agent_id: str) -> List[Message]:
        """Receive messages for an agent"""
        pass

    @abstractmethod
    async def subscribe(self, agent_id: str, topic: str) -> bool:
        """Subscribe to a topic"""
        pass

    @abstractmethod
    async def broadcast(self, message: Message) -> int:
        """Broadcast to all agents, returns count reached"""
        pass


class IKnowledgeBase(ABC):
    """Interface for knowledge management"""

    @abstractmethod
    async def store_knowledge(self, topic: str, content: Dict[str, Any]) -> str:
        """Store knowledge, returns knowledge ID"""
        pass

    @abstractmethod
    async def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Query knowledge base"""
        pass

    @abstractmethod
    async def get_expert(self, topic: str) -> Optional[str]:
        """Find expert agent for topic"""
        pass


class ICollaborationProtocol(ABC):
    """Interface for collaboration protocols"""

    @abstractmethod
    async def request_review(self, artifact: Dict, reviewers: List[str]) -> str:
        """Request peer review, returns review ID"""
        pass

    @abstractmethod
    async def vote_on_proposal(self, proposal_id: str, vote: bool) -> bool:
        """Vote on a proposal"""
        pass

    @abstractmethod
    async def handoff_task(self, task: Dict, from_agent: str, to_agent: str) -> bool:
        """Hand off task between agents"""
        pass
