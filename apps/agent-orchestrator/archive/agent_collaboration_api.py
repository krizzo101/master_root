#!/usr/bin/env python3
"""
Agent Collaboration API
Real-time communication system for multi-agent collaboration
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the collaboration system"""

    # Coordination Messages
    TASK_HANDOFF = "task_handoff"
    HELP_REQUEST = "help_request"
    STATUS_UPDATE = "status_update"
    COORDINATION_REQUEST = "coordination_request"

    # Knowledge Sharing
    DISCOVERY_SHARE = "discovery_share"
    INSIGHT_SHARE = "insight_share"
    RESEARCH_FINDING = "research_finding"
    KNOWLEDGE_UPDATE = "knowledge_update"

    # Workspace Messages
    FILE_UPDATE = "file_update"
    WORKSPACE_SYNC = "workspace_sync"
    COLLABORATIVE_EDIT = "collaborative_edit"
    ARTIFACT_SHARE = "artifact_share"

    # System Messages
    AGENT_REGISTRATION = "agent_registration"
    HEARTBEAT = "heartbeat"
    ERROR_NOTIFICATION = "error_notification"
    SYSTEM_ALERT = "system_alert"


class Priority(Enum):
    """Message priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentStatus(Enum):
    """Agent status states"""

    ONLINE = "online"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Agent registration and status information"""

    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus
    last_seen: str
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Base message structure for agent communication"""

    message_id: str
    message_type: MessageType
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    content: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    workspace_id: Optional[str] = None
    correlation_id: Optional[str] = None  # For request/response tracking
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert enums to strings for JSON serialization
        result["message_type"] = self.message_type.value
        result["priority"] = self.priority.value
        return result


@dataclass
class TaskHandoffMessage:
    """Specific structure for task handoff coordination"""

    task_id: str
    task_type: str
    task_description: str
    from_agent: str
    to_agent: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HelpRequestMessage:
    """Structure for help requests between agents"""

    request_id: str
    requesting_agent: str
    help_type: str  # "expertise", "resource", "validation", "escalation"
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    urgency: Priority = Priority.NORMAL
    skills_needed: List[str] = field(default_factory=list)


@dataclass
class WorkspaceUpdate:
    """Structure for workspace collaboration messages"""

    workspace_id: str
    update_type: str  # "file_change", "artifact_add", "sync_request"
    affected_files: List[str] = field(default_factory=list)
    changes: Dict[str, Any] = field(default_factory=dict)
    version: str = ""
    author: str = ""


class CollaborationAPI:
    """
    Main API class for agent collaboration
    Handles message routing, agent registration, and workspace coordination
    """

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Agent registry
        self.agents: Dict[str, AgentInfo] = {}

        # Message queues - one per agent
        self.message_queues: Dict[str, asyncio.Queue] = {}

        # WebSocket connections for real-time communication
        self.websocket_connections: Dict[str, Any] = {}  # websocket objects

        # Workspace tracking
        self.workspaces: Dict[str, Dict] = {}

        # Message history for debugging/replay
        self.message_history: List[Message] = []

        self.logger = logging.getLogger(__name__)

    async def register_agent(self, agent_info: AgentInfo) -> Dict[str, Any]:
        """Register a new agent in the collaboration system"""
        self.agents[agent_info.agent_id] = agent_info
        self.message_queues[agent_info.agent_id] = asyncio.Queue()

        # Send registration confirmation
        registration_msg = Message(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.AGENT_REGISTRATION,
            from_agent="system",
            to_agent=agent_info.agent_id,
            content={
                "status": "registered",
                "agent_info": asdict(agent_info),
                "available_agents": [
                    aid for aid in self.agents.keys() if aid != agent_info.agent_id
                ],
            },
        )

        await self._route_message(registration_msg)

        self.logger.info(
            f"Agent {agent_info.agent_id} registered with capabilities: {agent_info.capabilities}"
        )

        return {"status": "success", "agent_id": agent_info.agent_id}

    async def send_message(self, message: Message) -> Dict[str, Any]:
        """Send a message through the collaboration system"""

        # Validate message
        if message.to_agent and message.to_agent not in self.agents:
            return {
                "status": "error",
                "error": f"Unknown recipient agent: {message.to_agent}",
            }

        if message.from_agent not in self.agents:
            return {
                "status": "error",
                "error": f"Unknown sender agent: {message.from_agent}",
            }

        # Store in message history
        self.message_history.append(message)

        # Route the message
        await self._route_message(message)

        return {"status": "success", "message_id": message.message_id}

    async def _route_message(self, message: Message):
        """Internal message routing"""

        if message.to_agent is None:
            # Broadcast message
            for agent_id in self.agents.keys():
                if agent_id != message.from_agent:
                    await self.message_queues[agent_id].put(message)
                    # Also send via WebSocket if connected
                    if agent_id in self.websocket_connections:
                        await self._send_websocket_message(agent_id, message)
        else:
            # Direct message
            if message.to_agent in self.message_queues:
                await self.message_queues[message.to_agent].put(message)
                # Also send via WebSocket if connected
                if message.to_agent in self.websocket_connections:
                    await self._send_websocket_message(message.to_agent, message)

    async def _send_websocket_message(self, agent_id: str, message: Message):
        """Send message via WebSocket connection"""
        if agent_id in self.websocket_connections:
            websocket = self.websocket_connections[agent_id]
            try:
                await websocket.send(json.dumps(message.to_dict()))
            except Exception as e:
                self.logger.warning(
                    f"Failed to send WebSocket message to {agent_id}: {e}"
                )

    async def get_messages(self, agent_id: str, max_messages: int = 10) -> List[Dict]:
        """Get messages for a specific agent (REST endpoint)"""
        if agent_id not in self.message_queues:
            return []

        messages = []
        queue = self.message_queues[agent_id]

        # Get available messages (non-blocking)
        count = 0
        while not queue.empty() and count < max_messages:
            try:
                message = queue.get_nowait()
                messages.append(message.to_dict())
                count += 1
            except asyncio.QueueEmpty:
                break

        return messages

    async def update_agent_status(
        self, agent_id: str, status: AgentStatus, metadata: Dict = None
    ) -> Dict:
        """Update agent status and metadata"""
        if agent_id not in self.agents:
            return {"status": "error", "error": "Agent not found"}

        self.agents[agent_id].status = status
        self.agents[agent_id].last_seen = datetime.now().isoformat()

        if metadata:
            self.agents[agent_id].metadata.update(metadata)

        # Broadcast status update to interested agents
        status_msg = Message(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.STATUS_UPDATE,
            from_agent=agent_id,
            to_agent=None,  # Broadcast
            content={
                "agent_id": agent_id,
                "status": status.value,
                "metadata": metadata or {},
            },
        )

        await self._route_message(status_msg)

        return {"status": "success"}

    async def get_active_agents(self) -> List[Dict]:
        """Get list of all active agents"""
        active_agents = []
        for agent_id, agent_info in self.agents.items():
            if agent_info.status in [
                AgentStatus.ONLINE,
                AgentStatus.BUSY,
                AgentStatus.IDLE,
            ]:
                active_agents.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent_info.agent_type,
                        "capabilities": agent_info.capabilities,
                        "status": agent_info.status.value,
                        "last_seen": agent_info.last_seen,
                        "workspace_id": agent_info.workspace_id,
                    }
                )

        return active_agents

    async def share_workspace_artifact(
        self, workspace_id: str, artifact_data: Dict
    ) -> Dict:
        """Share workspace artifact with collaborating agents"""
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = {
                "artifacts": [],
                "participants": [],
                "created_at": datetime.now().isoformat(),
            }

        # Add artifact
        artifact_id = str(uuid.uuid4())
        artifact = {
            "artifact_id": artifact_id,
            "data": artifact_data,
            "shared_at": datetime.now().isoformat(),
            "shared_by": artifact_data.get("author", "unknown"),
        }

        self.workspaces[workspace_id]["artifacts"].append(artifact)

        # Notify workspace participants
        workspace_msg = Message(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ARTIFACT_SHARE,
            from_agent="system",
            to_agent=None,  # Broadcast to workspace participants
            workspace_id=workspace_id,
            content={"workspace_id": workspace_id, "artifact": artifact},
        )

        await self._route_message(workspace_msg)

        return {"status": "success", "artifact_id": artifact_id}

    async def get_workspace_status(self, workspace_id: str) -> Dict:
        """Get status of shared workspace"""
        if workspace_id not in self.workspaces:
            return {"status": "error", "error": "Workspace not found"}

        workspace = self.workspaces[workspace_id]

        # Find active participants
        participants = []
        for agent_id, agent_info in self.agents.items():
            if agent_info.workspace_id == workspace_id:
                participants.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent_info.agent_type,
                        "status": agent_info.status.value,
                    }
                )

        return {
            "status": "success",
            "workspace_id": workspace_id,
            "participants": participants,
            "artifacts_count": len(workspace.get("artifacts", [])),
            "created_at": workspace.get("created_at"),
            "last_activity": workspace.get("last_activity", ""),
        }


# Message factory functions for common use cases
def create_task_handoff(
    from_agent: str, to_agent: str, task_data: TaskHandoffMessage
) -> Message:
    """Create a task handoff message"""
    return Message(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.TASK_HANDOFF,
        from_agent=from_agent,
        to_agent=to_agent,
        content=asdict(task_data),
        priority=Priority.HIGH,
    )


def create_help_request(
    requesting_agent: str, help_data: HelpRequestMessage
) -> Message:
    """Create a help request message"""
    return Message(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.HELP_REQUEST,
        from_agent=requesting_agent,
        to_agent=None,  # Broadcast
        content=asdict(help_data),
        priority=help_data.urgency,
    )


def create_workspace_update(
    from_agent: str, workspace_data: WorkspaceUpdate
) -> Message:
    """Create workspace update message"""
    return Message(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.WORKSPACE_SYNC,
        from_agent=from_agent,
        to_agent=None,  # Broadcast to workspace
        workspace_id=workspace_data.workspace_id,
        content=asdict(workspace_data),
        priority=Priority.NORMAL,
    )


def create_discovery_share(from_agent: str, discovery_data: Dict[str, Any]) -> Message:
    """Create knowledge discovery sharing message"""
    return Message(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.DISCOVERY_SHARE,
        from_agent=from_agent,
        to_agent=None,  # Broadcast
        content=discovery_data,
        priority=Priority.NORMAL,
    )
