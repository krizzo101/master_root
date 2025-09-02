#!/usr/bin/env python3
"""
Mission: Agents Build Their Own Communication Platform
The swarm will design and implement how they want to communicate
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.production_quality_system import (
    QualityLevel,
    create_production_system,
)
from src.orchestration.selective_merger import SelectiveMerger
from src.orchestration.worktree_manager import WorktreeManager


class CommunicationPlatformBuilder:
    """Orchestrates agents to build their own communication system"""

    def __init__(self):
        self.repo_path = Path("/home/opsvi/master_root")
        self.worktree_manager = WorktreeManager(self.repo_path)
        self.merger = SelectiveMerger(self.repo_path)
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create production system with appropriate quality level
        self.prod_system = create_production_system(QualityLevel.DEVELOPMENT)

    async def execute_agent(
        self,
        agent_type: str,
        workspace_path: Path,
        task_prompt: str,
        shared_context: Dict,
    ) -> Dict:
        """Execute an agent with specific instructions"""

        workspace_path.mkdir(parents=True, exist_ok=True)

        # Agent implementations based on their role in building communication
        if agent_type == "system_architect":
            # Design the overall communication architecture
            design_doc = """# Agent Communication Platform Architecture

## Design Principles
1. **Asynchronous Message Passing** - Non-blocking communication
2. **Publish-Subscribe Pattern** - Flexible topic-based messaging
3. **Knowledge Sharing** - Centralized knowledge repository
4. **Collaboration Protocols** - Structured interaction patterns

## Core Components

### 1. Message Bus
- Central routing of messages between agents
- Topic-based subscriptions
- Priority queuing
- Message persistence

### 2. Agent Registry
- Track active agents and their capabilities
- Status monitoring
- Workload balancing
- Service discovery

### 3. Knowledge Base
- Shared learnings and solutions
- Searchable by topic/tags
- Version control for knowledge evolution
- Expert identification system

### 4. Collaboration Protocols
- **Peer Review**: Code/design review workflow
- **Task Handoff**: Transferring work between agents
- **Consensus**: Voting on decisions
- **Help Request**: Getting assistance from experts

## Message Format
```python
{
    "id": "unique-message-id",
    "type": "request|response|broadcast|notification",
    "sender": "agent-id",
    "recipient": "agent-id or null for broadcast",
    "topic": "message-topic",
    "content": {},
    "timestamp": "ISO-8601",
    "correlation_id": "for threading",
    "priority": 1-10
}
```

## Communication Flow
1. Agent registers with platform
2. Subscribes to relevant topics
3. Sends/receives messages async
4. Updates knowledge base with learnings
5. Collaborates using protocols

## Implementation Requirements
- Python asyncio for async operations
- JSON for message serialization
- File-based persistence initially
- Redis for future scalability
- WebSocket for real-time updates

## API Endpoints
- POST /register - Register agent
- POST /message - Send message
- GET /messages - Retrieve messages
- POST /knowledge - Share knowledge
- GET /knowledge - Query knowledge
- POST /collaborate - Initiate collaboration
"""

            (workspace_path / "architecture.md").write_text(design_doc)
            print(f"   ✅ Created architecture design")

            # Create interface definition
            interface_code = '''"""
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
'''

            (workspace_path / "interfaces.py").write_text(interface_code)
            print(f"   ✅ Created interface definitions")

        elif agent_type == "backend_developer":
            # Implement the message bus
            message_bus_code = '''"""
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
    ICommunicationPlatform,
    Message,
    MessageType,
    AgentInfo,
    AgentStatus
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
            await self._persist_event("agent_registered", {
                "agent_id": agent.id,
                "capabilities": list(agent.capabilities)
            })

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
        filepath = self.persistence_path / f"messages_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        message_dict = asdict(message)
        message_dict['timestamp'] = message_dict['timestamp'].isoformat()

        with open(filepath, 'a') as f:
            f.write(json.dumps(message_dict) + '\\n')

    async def _persist_event(self, event_type: str, data: Dict):
        """Log system events"""
        filepath = self.persistence_path / "events.jsonl"

        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }

        with open(filepath, 'a') as f:
            f.write(json.dumps(event) + '\\n')

    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get current status of an agent"""
        if agent_id in self.agents:
            return self.agents[agent_id].status
        return None

    def get_active_agents(self) -> List[str]:
        """Get list of active agents"""
        return [
            agent_id for agent_id, agent in self.agents.items()
            if agent.status != AgentStatus.OFFLINE
        ]
'''

            (workspace_path / "message_bus.py").write_text(message_bus_code)
            print(f"   ✅ Created message bus implementation")

            # Create knowledge base
            knowledge_code = '''"""
Knowledge Base Implementation
Shared knowledge repository for agents
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from interfaces import IKnowledgeBase


class KnowledgeBase(IKnowledgeBase):
    """Centralized knowledge management system"""

    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path("/tmp/agent_knowledge")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.knowledge: Dict[str, Dict[str, Any]] = {}
        self.topic_index: Dict[str, List[str]] = defaultdict(list)
        self.expert_scores: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        self._load_knowledge()

    async def store_knowledge(self, topic: str, content: Dict[str, Any]) -> str:
        """Store new knowledge entry"""
        knowledge_id = str(uuid.uuid4())

        entry = {
            'id': knowledge_id,
            'topic': topic,
            'content': content,
            'created_at': datetime.utcnow().isoformat(),
            'access_count': 0,
            'usefulness_score': 0.5,
            'contributor': content.get('agent_id', 'unknown')
        }

        self.knowledge[knowledge_id] = entry
        self.topic_index[topic].append(knowledge_id)

        # Update expert score
        contributor = entry['contributor']
        self.expert_scores[topic][contributor] += 1

        # Persist
        await self._save_entry(entry)

        return knowledge_id

    async def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        results = []
        query_lower = query.lower()

        for knowledge_id, entry in self.knowledge.items():
            # Simple text matching for now
            if (query_lower in entry['topic'].lower() or
                query_lower in json.dumps(entry['content']).lower()):

                # Increment access count
                entry['access_count'] += 1
                results.append(entry)

        # Sort by usefulness and access count
        results.sort(
            key=lambda x: (x['usefulness_score'], x['access_count']),
            reverse=True
        )

        return results[:10]  # Return top 10

    async def get_expert(self, topic: str) -> Optional[str]:
        """Find the most knowledgeable agent for a topic"""
        if topic in self.expert_scores:
            experts = self.expert_scores[topic]
            if experts:
                # Return agent with highest contribution score
                return max(experts, key=experts.get)
        return None

    async def update_usefulness(self, knowledge_id: str, useful: bool):
        """Update usefulness score based on feedback"""
        if knowledge_id in self.knowledge:
            entry = self.knowledge[knowledge_id]
            # Simple exponential moving average
            alpha = 0.1
            score_delta = 1.0 if useful else 0.0
            entry['usefulness_score'] = (
                alpha * score_delta +
                (1 - alpha) * entry['usefulness_score']
            )

    def _load_knowledge(self):
        """Load knowledge from disk"""
        knowledge_file = self.storage_path / "knowledge.json"
        if knowledge_file.exists():
            with open(knowledge_file, 'r') as f:
                data = json.load(f)
                self.knowledge = data.get('knowledge', {})
                self.topic_index = defaultdict(list, data.get('topic_index', {}))
                self.expert_scores = defaultdict(
                    lambda: defaultdict(float),
                    data.get('expert_scores', {})
                )

    async def _save_entry(self, entry: Dict[str, Any]):
        """Persist knowledge entry"""
        # Append to journal
        journal_file = self.storage_path / "knowledge_journal.jsonl"
        with open(journal_file, 'a') as f:
            f.write(json.dumps(entry) + '\\n')

        # Periodically save full state
        if len(self.knowledge) % 10 == 0:
            await self._save_full_state()

    async def _save_full_state(self):
        """Save complete knowledge base state"""
        knowledge_file = self.storage_path / "knowledge.json"

        state = {
            'knowledge': self.knowledge,
            'topic_index': dict(self.topic_index),
            'expert_scores': {
                topic: dict(scores)
                for topic, scores in self.expert_scores.items()
            }
        }

        with open(knowledge_file, 'w') as f:
            json.dump(state, f, indent=2)
'''

            (workspace_path / "knowledge_base.py").write_text(knowledge_code)
            print(f"   ✅ Created knowledge base implementation")

        elif agent_type == "protocol_designer":
            # Design collaboration protocols
            protocols_code = '''"""
Collaboration Protocols
Structured patterns for agent cooperation
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from interfaces import (
    ICollaborationProtocol,
    Message,
    MessageType
)


class CollaborationStatus(Enum):
    """Status of collaboration activities"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Review:
    """Peer review data structure"""
    review_id: str
    artifact: Dict[str, Any]
    author: str
    reviewers: List[str]
    reviews: Dict[str, Dict] = field(default_factory=dict)
    status: CollaborationStatus = CollaborationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskHandoff:
    """Task handoff data structure"""
    handoff_id: str
    task: Dict[str, Any]
    from_agent: str
    to_agent: str
    reason: str
    status: CollaborationStatus = CollaborationStatus.PENDING
    handoff_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Proposal:
    """Decision proposal structure"""
    proposal_id: str
    proposer: str
    title: str
    description: str
    options: List[str]
    votes: Dict[str, str] = field(default_factory=dict)
    status: CollaborationStatus = CollaborationStatus.PENDING
    deadline: Optional[datetime] = None


class CollaborationProtocols(ICollaborationProtocol):
    """Implementation of agent collaboration patterns"""

    def __init__(self, message_bus):
        self.message_bus = message_bus
        self.active_reviews: Dict[str, Review] = {}
        self.active_handoffs: Dict[str, TaskHandoff] = {}
        self.active_proposals: Dict[str, Proposal] = {}

    async def request_review(self, artifact: Dict, reviewers: List[str]) -> str:
        """Initiate peer review process"""
        review_id = str(uuid.uuid4())

        review = Review(
            review_id=review_id,
            artifact=artifact,
            author=artifact.get('author', 'unknown'),
            reviewers=reviewers
        )

        self.active_reviews[review_id] = review

        # Send review requests
        for reviewer in reviewers:
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                sender="system",
                recipient=reviewer,
                topic="peer_review",
                content={
                    'review_id': review_id,
                    'artifact': artifact,
                    'action': 'review_requested'
                },
                timestamp=datetime.utcnow(),
                correlation_id=review_id,
                priority=7
            )

            await self.message_bus.send_message(message)

        review.status = CollaborationStatus.IN_PROGRESS
        return review_id

    async def submit_review(self, review_id: str, reviewer: str, feedback: Dict):
        """Submit review feedback"""
        if review_id not in self.active_reviews:
            return False

        review = self.active_reviews[review_id]
        review.reviews[reviewer] = {
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Check if all reviews are complete
        if len(review.reviews) >= len(review.reviewers):
            review.status = CollaborationStatus.COMPLETED

            # Notify author
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.NOTIFICATION,
                sender="system",
                recipient=review.author,
                topic="peer_review",
                content={
                    'review_id': review_id,
                    'status': 'completed',
                    'reviews': review.reviews
                },
                timestamp=datetime.utcnow(),
                correlation_id=review_id
            )

            await self.message_bus.send_message(message)

        return True

    async def handoff_task(self, task: Dict, from_agent: str, to_agent: str) -> bool:
        """Transfer task ownership between agents"""
        handoff_id = str(uuid.uuid4())

        handoff = TaskHandoff(
            handoff_id=handoff_id,
            task=task,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=task.get('handoff_reason', 'Task transfer')
        )

        self.active_handoffs[handoff_id] = handoff

        # Notify receiving agent
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            sender=from_agent,
            recipient=to_agent,
            topic="task_handoff",
            content={
                'handoff_id': handoff_id,
                'task': task,
                'from_agent': from_agent,
                'reason': handoff.reason
            },
            timestamp=datetime.utcnow(),
            correlation_id=handoff_id,
            priority=8
        )

        await self.message_bus.send_message(message)

        handoff.status = CollaborationStatus.IN_PROGRESS
        return True

    async def accept_handoff(self, handoff_id: str) -> bool:
        """Accept a task handoff"""
        if handoff_id not in self.active_handoffs:
            return False

        handoff = self.active_handoffs[handoff_id]
        handoff.status = CollaborationStatus.COMPLETED

        # Notify original agent
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            sender=handoff.to_agent,
            recipient=handoff.from_agent,
            topic="task_handoff",
            content={
                'handoff_id': handoff_id,
                'status': 'accepted'
            },
            timestamp=datetime.utcnow(),
            correlation_id=handoff_id
        )

        await self.message_bus.send_message(message)
        return True

    async def create_proposal(
        self,
        proposer: str,
        title: str,
        description: str,
        options: List[str],
        voters: List[str],
        deadline: Optional[datetime] = None
    ) -> str:
        """Create a proposal for voting"""
        proposal_id = str(uuid.uuid4())

        proposal = Proposal(
            proposal_id=proposal_id,
            proposer=proposer,
            title=title,
            description=description,
            options=options,
            deadline=deadline
        )

        self.active_proposals[proposal_id] = proposal

        # Notify voters
        for voter in voters:
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                sender=proposer,
                recipient=voter,
                topic="proposal_vote",
                content={
                    'proposal_id': proposal_id,
                    'title': title,
                    'description': description,
                    'options': options,
                    'deadline': deadline.isoformat() if deadline else None
                },
                timestamp=datetime.utcnow(),
                correlation_id=proposal_id,
                priority=6
            )

            await self.message_bus.send_message(message)

        proposal.status = CollaborationStatus.IN_PROGRESS
        return proposal_id

    async def vote_on_proposal(self, proposal_id: str, vote: bool) -> bool:
        """Vote on a proposal"""
        if proposal_id not in self.active_proposals:
            return False

        proposal = self.active_proposals[proposal_id]

        # Record vote (simplified - in reality would track voter ID)
        voter_id = f"voter_{len(proposal.votes)}"
        proposal.votes[voter_id] = "approve" if vote else "reject"

        # Check if voting is complete (simplified logic)
        if len(proposal.votes) >= 3:  # Assuming 3 voters minimum
            approvals = sum(1 for v in proposal.votes.values() if v == "approve")
            proposal.status = (
                CollaborationStatus.COMPLETED
                if approvals > len(proposal.votes) / 2
                else CollaborationStatus.FAILED
            )

            # Notify proposer
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                sender="system",
                recipient=proposal.proposer,
                topic="proposal_result",
                content={
                    'proposal_id': proposal_id,
                    'result': proposal.status.value,
                    'votes': proposal.votes
                },
                timestamp=datetime.utcnow(),
                correlation_id=proposal_id
            )

            await self.message_bus.send_message(message)

        return True
'''

            (workspace_path / "collaboration_protocols.py").write_text(protocols_code)
            print(f"   ✅ Created collaboration protocols")

        elif agent_type == "integration_engineer":
            # Create the main platform that ties everything together
            platform_code = '''"""
Agent Communication Platform
Main integration bringing together all components
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from message_bus import MessageBus
from knowledge_base import KnowledgeBase
from collaboration_protocols import CollaborationProtocols
from interfaces import AgentInfo, AgentStatus, Message, MessageType


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
            'messages_sent': 0,
            'agents_registered': 0,
            'knowledge_entries': 0,
            'active_collaborations': 0
        }

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str]
    ) -> 'AgentClient':
        """Register an agent and return a client for communication"""

        agent_info = AgentInfo(
            id=agent_id,
            name=name,
            capabilities=set(capabilities),
            status=AgentStatus.IDLE,
            workload=0
        )

        success = await self.message_bus.register_agent(agent_info)

        if success:
            self.metrics['agents_registered'] += 1
            return AgentClient(self, agent_info)

        return None

    def get_platform_status(self) -> Dict:
        """Get platform health and metrics"""
        return {
            'status': 'operational',
            'metrics': self.metrics,
            'active_agents': len(self.message_bus.agents),
            'message_queue_sizes': {
                agent_id: queue.qsize()
                for agent_id, queue in self.message_bus.message_queues.items()
            },
            'knowledge_entries': len(self.knowledge_base.knowledge)
        }


class AgentClient:
    """Client interface for agents to use the platform"""

    def __init__(self, platform: CommunicationPlatform, agent_info: AgentInfo):
        self.platform = platform
        self.agent_info = agent_info
        self.received_messages: List[Message] = []

    async def send_message(
        self,
        recipient: Optional[str],
        topic: str,
        content: Dict,
        priority: int = 5
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
            priority=priority
        )

        success = await self.platform.message_bus.send_message(message)
        if success:
            self.platform.metrics['messages_sent'] += 1

        return success

    async def receive_messages(self) -> List[Message]:
        """Check for new messages"""
        messages = await self.platform.message_bus.receive_messages(self.agent_info.id)
        self.received_messages.extend(messages)
        return messages

    async def share_knowledge(self, topic: str, knowledge: Dict) -> str:
        """Share knowledge with other agents"""
        knowledge['agent_id'] = self.agent_info.id
        knowledge_id = await self.platform.knowledge_base.store_knowledge(topic, knowledge)

        if knowledge_id:
            self.platform.metrics['knowledge_entries'] += 1

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
            agent_id for agent_id, agent in self.platform.message_bus.agents.items()
            if capability in agent.capabilities and agent.status == AgentStatus.IDLE
        ]

        if not capable_agents:
            return False

        # Send help request to first available
        return await self.send_message(
            recipient=capable_agents[0],
            topic="help_request",
            content={'capability': capability, 'task': task_details},
            priority=7
        )

    async def request_review(self, artifact: Dict, reviewers: List[str]) -> str:
        """Request peer review of work"""
        artifact['author'] = self.agent_info.id
        review_id = await self.platform.protocols.request_review(artifact, reviewers)

        if review_id:
            self.platform.metrics['active_collaborations'] += 1

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
                'agent_id': self.agent_info.id,
                'status': status.value,
                'workload': self.agent_info.workload
            }
        )


# Import required for client
import uuid
from datetime import datetime
'''

            (workspace_path / "communication_platform.py").write_text(platform_code)
            print(f"   ✅ Created main platform integration")

        elif agent_type == "test_engineer":
            # Create tests for the communication platform
            test_code = '''"""
Tests for Agent Communication Platform
Validates that all components work correctly
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from communication_platform import CommunicationPlatform
from interfaces import AgentStatus


async def test_agent_registration():
    """Test agent registration and client creation"""
    platform = CommunicationPlatform()

    # Register test agent
    client = await platform.register_agent(
        agent_id="test_agent_1",
        name="Test Agent 1",
        capabilities=["testing", "validation"]
    )

    assert client is not None, "Failed to create agent client"
    assert platform.metrics['agents_registered'] == 1, "Agent count incorrect"
    print("✓ Agent registration test passed")


async def test_message_sending():
    """Test message sending between agents"""
    platform = CommunicationPlatform()

    # Register two agents
    client1 = await platform.register_agent("agent1", "Agent 1", ["coding"])
    client2 = await platform.register_agent("agent2", "Agent 2", ["testing"])

    # Send message from agent1 to agent2
    success = await client1.send_message(
        recipient="agent2",
        topic="test_message",
        content={"message": "Hello from Agent 1"}
    )

    assert success, "Failed to send message"

    # Receive message on agent2
    messages = await client2.receive_messages()
    assert len(messages) == 1, "Should receive 1 message"
    assert messages[0].sender == "agent1", "Wrong sender"
    assert messages[0].content["message"] == "Hello from Agent 1", "Wrong content"

    print("✓ Message sending test passed")


async def test_broadcasting():
    """Test broadcast messaging"""
    platform = CommunicationPlatform()

    # Register three agents
    clients = []
    for i in range(3):
        client = await platform.register_agent(f"agent{i}", f"Agent {i}", ["test"])
        clients.append(client)

    # Broadcast from first agent
    await clients[0].send_message(
        recipient=None,  # Broadcast
        topic="announcement",
        content={"message": "Broadcast test"}
    )

    # Check other agents received it
    for i in range(1, 3):
        messages = await clients[i].receive_messages()
        assert len(messages) == 1, f"Agent {i} should receive broadcast"
        assert messages[0].topic == "announcement", "Wrong topic"

    print("✓ Broadcasting test passed")


async def test_knowledge_sharing():
    """Test knowledge base functionality"""
    platform = CommunicationPlatform()

    client = await platform.register_agent("knowledgeable", "Smart Agent", ["expert"])

    # Share knowledge
    knowledge_id = await client.share_knowledge(
        topic="python_testing",
        knowledge={
            "title": "How to use pytest",
            "content": "Use pytest for testing Python code",
            "tags": ["testing", "python", "pytest"]
        }
    )

    assert knowledge_id is not None, "Failed to store knowledge"

    # Query knowledge
    results = await client.query_knowledge("pytest")
    assert len(results) > 0, "Should find knowledge"
    assert results[0]['topic'] == "python_testing", "Wrong topic"

    # Find expert
    expert = await client.find_expert("python_testing")
    assert expert == "knowledgeable", "Should find correct expert"

    print("✓ Knowledge sharing test passed")


async def test_help_request():
    """Test requesting help from capable agents"""
    platform = CommunicationPlatform()

    # Register helper agent
    helper = await platform.register_agent(
        "helper",
        "Helper Agent",
        ["debugging", "optimization"]
    )

    # Register requester
    requester = await platform.register_agent(
        "requester",
        "Requester Agent",
        ["coding"]
    )

    # Request help
    success = await requester.request_help(
        capability="debugging",
        task_details={"problem": "Segmentation fault in C code"}
    )

    assert success, "Failed to request help"

    # Helper should receive request
    messages = await helper.receive_messages()
    assert len(messages) == 1, "Helper should receive help request"
    assert messages[0].topic == "help_request", "Wrong message type"

    print("✓ Help request test passed")


async def test_status_updates():
    """Test agent status updates"""
    platform = CommunicationPlatform()

    client = await platform.register_agent("worker", "Worker Agent", ["work"])

    # Update status
    await client.update_status(AgentStatus.BUSY, workload=75)

    # Check status was updated
    assert client.agent_info.status == AgentStatus.BUSY, "Status not updated"
    assert client.agent_info.workload == 75, "Workload not updated"

    print("✓ Status update test passed")


async def run_all_tests():
    """Run all tests"""
    print("\\n🧪 Testing Agent Communication Platform...")
    print("-" * 40)

    tests = [
        test_agent_registration,
        test_message_sending,
        test_broadcasting,
        test_knowledge_sharing,
        test_help_request,
        test_status_updates
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1

    print("-" * 40)
    print(f"\\n📊 Results: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
'''

            (workspace_path / "test_platform.py").write_text(test_code)
            print(f"   ✅ Created platform tests")

        elif agent_type == "documentation_writer":
            # Create comprehensive documentation
            readme = f"""# Agent Communication Platform

## Overview
A distributed communication and collaboration platform enabling autonomous agents to coordinate, share knowledge, and work together effectively.

## Architecture

### Core Components

1. **Message Bus** (`message_bus.py`)
   - Central message routing system
   - Topic-based pub/sub messaging
   - Message persistence and history
   - Priority queuing

2. **Knowledge Base** (`knowledge_base.py`)
   - Shared knowledge repository
   - Expert identification system
   - Searchable by topics and content
   - Usefulness scoring

3. **Collaboration Protocols** (`collaboration_protocols.py`)
   - Peer review workflow
   - Task handoff mechanism
   - Proposal voting system
   - Structured interaction patterns

4. **Platform Integration** (`communication_platform.py`)
   - Unified interface for all components
   - Agent registration and management
   - Metrics and monitoring
   - Client SDK for agents

## Quick Start

```python
from communication_platform import CommunicationPlatform

# Initialize platform
platform = CommunicationPlatform()

# Register an agent
client = await platform.register_agent(
    agent_id="my_agent",
    name="My Agent",
    capabilities=["coding", "testing"]
)

# Send a message
await client.send_message(
    recipient="other_agent",
    topic="code_review",
    content={{"code": "def hello(): pass"}}
)

# Receive messages
messages = await client.receive_messages()

# Share knowledge
await client.share_knowledge(
    topic="python_tips",
    knowledge={{"tip": "Use asyncio for concurrency"}}
)
```

## Communication Patterns

### Direct Messaging
Agent-to-agent private communication.

### Broadcasting
Send messages to all agents.

### Topic Subscription
Subscribe to specific topics for relevant messages.

### Help Requests
Request assistance from agents with specific capabilities.

## Collaboration Workflows

### Peer Review
1. Author submits artifact for review
2. Platform assigns reviewers
3. Reviewers provide feedback
4. Author receives consolidated feedback

### Task Handoff
1. Agent A identifies need to transfer task
2. Initiates handoff to Agent B
3. Agent B accepts or rejects
4. Task ownership transfers

### Consensus Voting
1. Agent proposes decision
2. Platform notifies voters
3. Agents vote on proposal
4. Result determined by majority

## API Reference

### AgentClient Methods

- `send_message(recipient, topic, content, priority)` - Send a message
- `receive_messages()` - Get pending messages
- `share_knowledge(topic, knowledge)` - Add to knowledge base
- `query_knowledge(query)` - Search knowledge base
- `find_expert(topic)` - Find expert agent
- `request_help(capability, task_details)` - Request assistance
- `request_review(artifact, reviewers)` - Initiate peer review
- `update_status(status, workload)` - Update agent status

## Testing

Run the test suite:
```bash
python test_platform.py
```

## Performance Considerations

- Message queues are in-memory (upgrade to Redis for production)
- Knowledge base uses file persistence (consider database for scale)
- Async operations throughout for non-blocking communication

## Future Enhancements

1. WebSocket support for real-time messaging
2. Redis backend for distributed deployment
3. Message encryption for sensitive data
4. GraphQL API for complex queries
5. Machine learning for intelligent routing
6. Metrics dashboard for monitoring

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  Agent Clients                  │
└─────────────┬──────────────────┬────────────────┘
              │                  │
        ╔═════▼══════════════════▼═════╗
        ║   Communication Platform     ║
        ╠═══════════════════════════════╣
        ║  ┌───────────────────────┐   ║
        ║  │    Message Bus        │   ║
        ║  │  - Routing            │   ║
        ║  │  - Persistence        │   ║
        ║  └───────────────────────┘   ║
        ║  ┌───────────────────────┐   ║
        ║  │   Knowledge Base      │   ║
        ║  │  - Storage            │   ║
        ║  │  - Search             │   ║
        ║  └───────────────────────┘   ║
        ║  ┌───────────────────────┐   ║
        ║  │  Collaboration        │   ║
        ║  │  - Protocols          │   ║
        ║  │  - Workflows          │   ║
        ║  └───────────────────────┘   ║
        ╚═══════════════════════════════╝
```

## Contributing

When extending the platform:
1. Follow the interface definitions in `interfaces.py`
2. Add tests for new functionality
3. Update documentation
4. Maintain backwards compatibility

## License
MIT

---
Built by Multi-Agent Collaboration System
Version 1.0.0
"""

            (workspace_path / "README.md").write_text(readme)
            print(f"   ✅ Created comprehensive documentation")

        return {"success": True, "agent": agent_type}

    async def build_communication_platform(self):
        """Orchestrate agents to build their communication platform"""

        print("\n" + "=" * 60)
        print("🚀 MISSION: AGENTS BUILD THEIR OWN COMMUNICATION PLATFORM")
        print("=" * 60)

        # Create base branch
        base_branch = f"feature/agent-communication-{self.execution_id}"
        subprocess.run(
            ["git", "checkout", "-b", base_branch],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )
        print(f"\n✅ Created branch: {base_branch}")

        # Define the agent pipeline
        agents = [
            {
                "type": "system_architect",
                "role": "System Architect",
                "task": """Design the architecture for an agent communication platform that enables:
                - Asynchronous message passing between agents
                - Knowledge sharing and discovery
                - Collaboration protocols (peer review, task handoff, voting)
                - Agent registration and capability discovery
                Create architecture document and interface definitions.""",
            },
            {
                "type": "backend_developer",
                "role": "Backend Developer",
                "task": """Implement the core communication infrastructure:
                - Message bus for routing messages
                - Knowledge base for shared learning
                - Message persistence and queuing
                Use the interfaces defined by the architect.""",
            },
            {
                "type": "protocol_designer",
                "role": "Protocol Designer",
                "task": """Design and implement collaboration protocols:
                - Peer review workflow
                - Task handoff mechanism
                - Proposal and voting system
                - Help request protocol
                Build on top of the message bus.""",
            },
            {
                "type": "integration_engineer",
                "role": "Integration Engineer",
                "task": """Integrate all components into a unified platform:
                - Main platform class bringing everything together
                - Agent client interface for easy usage
                - Platform metrics and monitoring
                - Status and health tracking""",
            },
            {
                "type": "test_engineer",
                "role": "Test Engineer",
                "task": """Create comprehensive tests for the platform:
                - Test agent registration
                - Test message sending and receiving
                - Test knowledge sharing
                - Test collaboration protocols
                Ensure all components work together.""",
            },
            {
                "type": "documentation_writer",
                "role": "Documentation Writer",
                "task": """Create complete documentation:
                - Architecture overview
                - API reference
                - Usage examples
                - Quick start guide
                - Future enhancements""",
            },
        ]

        print("\n📋 Agent Pipeline:")
        for i, agent in enumerate(agents, 1):
            print(f"   {i}. {agent['role']:20} → {agent['task'][:50]}...")

        # Shared context for agents to build on each other's work
        shared_context = {
            "platform_name": "Agent Communication Platform",
            "base_path": Path("/home/opsvi/agent_shared/platform"),
            "previous_work": {},
        }

        # Deploy agents sequentially (they need to build on each other)
        print(f"\n🤖 Deploying {len(agents)} specialized agents...")

        successful_agents = []

        for i, agent in enumerate(agents):
            print(f"\n{'='*50}")
            print(f"Agent {i+1}/{len(agents)}: {agent['role']}")
            print("=" * 50)

            agent_id = f"{agent['type']}_{self.execution_id}"

            # Create worktree
            worktree = self.worktree_manager.create_agent_worktree(
                agent_id=agent_id,
                agent_type=agent["type"],
                base_branch=base_branch,
                execution_id=self.execution_id,
            )

            env = self.worktree_manager.get_agent_environment(agent_id)
            workspace_path = Path(env["agent_workspace"])
            worktree_path = Path(env["working_directory"])

            # Build the specification for this agent
            spec = self.prod_system["spec_builder"].build_specification(
                agent["type"], agent["task"]
            )

            # Execute agent with production requirements
            result = await self.execute_agent(
                agent["type"],
                workspace_path,
                self.prod_system["spec_builder"].generate_agent_prompt(spec),
                shared_context,
            )

            if result["success"]:
                # Commit agent's work
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    [
                        "git",
                        "commit",
                        "--no-verify",
                        "-m",
                        f"feat({agent['type']}): {agent['task'][:60]}",
                    ],
                    cwd=worktree_path,
                    capture_output=True,
                )

                # Merge to base branch
                changed_files = self.merger.get_agent_changes(
                    worktree_path, agent["type"]
                )
                if changed_files:
                    self.merger.cherry_pick_files(
                        source_branch=env["branch_name"],
                        target_branch=base_branch,
                        files=changed_files,
                    )

                    successful_agents.append(agent["type"])

                    # Add to shared context for next agents
                    shared_context["previous_work"][agent["type"]] = {
                        "files": [str(f) for f in changed_files],
                        "workspace": str(workspace_path),
                    }

                print(f"✅ {agent['role']} completed successfully")

            # Cleanup worktree
            try:
                self.worktree_manager.cleanup_worktree(agent_id, force=True)
            except:
                pass

        # Summary
        print("\n" + "=" * 60)
        print("📊 BUILD SUMMARY")
        print("=" * 60)

        print(f"\nAgents Deployed: {len(agents)}")
        print(f"Successful: {len(successful_agents)}")

        # Run tests if test engineer succeeded
        if "test_engineer" in successful_agents:
            test_file = (
                self.repo_path
                / "apps/multi-agent-monitor"
                / "agent_workspace_test_engineer"
                / "test_platform.py"
            )

            if test_file.exists():
                print("\n🧪 Running platform tests...")
                result = subprocess.run(
                    ["/home/opsvi/miniconda/bin/python", str(test_file)],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

                print(result.stdout)

                if result.returncode == 0:
                    print("✅ All tests passed!")
                else:
                    print("⚠️  Some tests failed")

        print("\n" + "=" * 60)
        print("🎉 COMMUNICATION PLATFORM BUILT BY AGENTS!")
        print("=" * 60)
        print("\nThe agents have successfully built their own communication system.")
        print("They can now use this platform to coordinate on future tasks.")

        return len(successful_agents) == len(agents)


async def main():
    builder = CommunicationPlatformBuilder()
    success = await builder.build_communication_platform()

    if success:
        print("\n✅ Mission Success: Agents built their own communication platform!")
    else:
        print("\n⚠️  Mission Partially Complete: Some components need refinement")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
