"""
Data Models for Collaboration Persistence Layer
Optimized schema design for PostgreSQL with Redis caching
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AgentStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COORDINATION = "coordination"
    ERROR = "error"
    STATUS_UPDATE = "status_update"
    HANDOFF = "handoff"


class EventType(str, Enum):
    AGENT_REGISTERED = "agent_registered"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    COLLABORATION_STARTED = "collaboration_started"
    COLLABORATION_ENDED = "collaboration_ended"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_MODIFIED = "workspace_modified"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"


# Association tables for many-to-many relationships
agent_session_table = Table(
    "agent_sessions",
    Base.metadata,
    Column("agent_id", String, ForeignKey("agents.agent_id")),
    Column("session_id", String, ForeignKey("sessions.session_id")),
)


class Agent(Base):
    """Agent registry and status tracking"""

    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False, index=True)
    capabilities = Column(JSON, default=list)  # List of capability strings
    status = Column(String(20), default=AgentStatus.IDLE, index=True)
    metadata = Column(JSON, default=dict)

    # Performance metrics
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    last_active = Column(DateTime, default=datetime.utcnow, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sent_messages = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender"
    )
    received_messages = relationship(
        "Message", foreign_keys="Message.receiver_id", back_populates="receiver"
    )
    sessions = relationship(
        "Session", secondary=agent_session_table, back_populates="agents"
    )

    __table_args__ = (
        Index("ix_agent_status_active", "status", "last_active"),
        Index("ix_agent_type_status", "agent_type", "status"),
    )


class Session(Base):
    """Collaboration session tracking"""

    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    session_type = Column(
        String(100), nullable=False, index=True
    )  # orchestration, collaboration, etc.

    # Session status and metadata
    status = Column(String(20), default="active", index=True)
    metadata = Column(JSON, default=dict)

    # Performance tracking
    total_messages = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agents = relationship(
        "Agent", secondary=agent_session_table, back_populates="sessions"
    )
    messages = relationship("Message", back_populates="session")
    workspaces = relationship("Workspace", back_populates="session")

    __table_args__ = (
        Index("ix_session_status_started", "status", "started_at"),
        Index("ix_session_type_status", "session_type", "status"),
    )


class Message(Base):
    """Inter-agent communication tracking"""

    __tablename__ = "messages"

    message_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=False, index=True
    )
    sender_id = Column(
        String, ForeignKey("agents.agent_id"), nullable=False, index=True
    )
    receiver_id = Column(
        String, ForeignKey("agents.agent_id"), nullable=True, index=True
    )  # None for broadcasts

    # Message content and metadata
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)

    # Threading and conversation tracking
    thread_id = Column(String, nullable=True, index=True)
    parent_message_id = Column(String, ForeignKey("messages.message_id"), nullable=True)

    # Delivery and processing status
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    delivered_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="messages")
    sender = relationship(
        "Agent", foreign_keys=[sender_id], back_populates="sent_messages"
    )
    receiver = relationship(
        "Agent", foreign_keys=[receiver_id], back_populates="received_messages"
    )
    parent_message = relationship("Message", remote_side=[message_id])

    __table_args__ = (
        Index("ix_message_session_sent", "session_id", "sent_at"),
        Index("ix_message_thread_sent", "thread_id", "sent_at"),
        Index("ix_message_type_sent", "message_type", "sent_at"),
    )


class Workspace(Base):
    """Shared workspaces and artifacts"""

    __tablename__ = "workspaces"

    workspace_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Workspace configuration
    workspace_type = Column(
        String(100), nullable=False, index=True
    )  # code, document, data, etc.
    permissions = Column(JSON, default=dict)  # Agent permissions
    metadata = Column(JSON, default=dict)

    # Storage location
    storage_path = Column(String(500), nullable=True)
    storage_type = Column(String(50), default="filesystem")  # filesystem, s3, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="workspaces")
    artifacts = relationship("Artifact", back_populates="workspace")

    __table_args__ = (
        Index("ix_workspace_session_created", "session_id", "created_at"),
        Index("ix_workspace_type_created", "workspace_type", "created_at"),
    )


class Artifact(Base):
    """Shared artifacts and files"""

    __tablename__ = "artifacts"

    artifact_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String, ForeignKey("workspaces.workspace_id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    artifact_type = Column(
        String(100), nullable=False, index=True
    )  # file, code, document, etc.

    # Content and storage
    content = Column(Text, nullable=True)  # For small artifacts
    storage_path = Column(String(500), nullable=True)  # For large artifacts
    size_bytes = Column(Integer, default=0)
    checksum = Column(String(64), nullable=True)  # SHA-256

    # Version control
    version = Column(Integer, default=1)
    parent_artifact_id = Column(
        String, ForeignKey("artifacts.artifact_id"), nullable=True
    )

    # Metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="artifacts")
    parent_artifact = relationship("Artifact", remote_side=[artifact_id])

    __table_args__ = (
        Index("ix_artifact_workspace_created", "workspace_id", "created_at"),
        Index("ix_artifact_type_created", "artifact_type", "created_at"),
        UniqueConstraint(
            "workspace_id", "name", "version", name="uq_artifact_name_version"
        ),
    )


class Event(Base):
    """Complete audit trail of all system events"""

    __tablename__ = "events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, default=dict)

    # Context
    correlation_id = Column(
        String, nullable=True, index=True
    )  # For tracing related events
    parent_event_id = Column(String, ForeignKey("events.event_id"), nullable=True)

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer, nullable=True)  # For events with duration

    # Relationships
    parent_event = relationship("Event", remote_side=[event_id])

    __table_args__ = (
        Index("ix_event_session_timestamp", "session_id", "timestamp"),
        Index("ix_event_agent_timestamp", "agent_id", "timestamp"),
        Index("ix_event_type_timestamp", "event_type", "timestamp"),
        Index("ix_event_correlation_timestamp", "correlation_id", "timestamp"),
    )


class Metric(Base):
    """Time-series performance metrics"""

    __tablename__ = "metrics"

    metric_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=True, index=True)

    # Metric definition
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)

    # Context
    tags = Column(JSON, default=dict)  # For dimensional data
    metadata = Column(JSON, default=dict)

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_metric_name_timestamp", "metric_name", "timestamp"),
        Index(
            "ix_metric_session_name_timestamp", "session_id", "metric_name", "timestamp"
        ),
        Index("ix_metric_agent_name_timestamp", "agent_id", "metric_name", "timestamp"),
    )


# Pydantic models for API serialization
class AgentModel(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[str] = []
    status: AgentStatus
    metadata: Dict[str, Any] = {}
    total_tasks: int = 0
    successful_tasks: int = 0
    avg_response_time: float = 0.0
    last_active: datetime
    created_at: datetime
    updated_at: datetime


class SessionModel(BaseModel):
    session_id: str
    name: str
    description: Optional[str] = None
    session_type: str
    status: str
    metadata: Dict[str, Any] = {}
    total_messages: int = 0
    total_tasks: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    started_at: datetime
    ended_at: Optional[datetime] = None
    agents: List[AgentModel] = []


class MessageModel(BaseModel):
    message_id: str
    session_id: str
    sender_id: str
    receiver_id: Optional[str] = None
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = {}
    thread_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    response_time_ms: Optional[int] = None


class WorkspaceModel(BaseModel):
    workspace_id: str
    session_id: str
    name: str
    description: Optional[str] = None
    workspace_type: str
    permissions: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    storage_path: Optional[str] = None
    storage_type: str = "filesystem"
    created_at: datetime
    updated_at: datetime


class ArtifactModel(BaseModel):
    artifact_id: str
    workspace_id: str
    name: str
    artifact_type: str
    content: Optional[str] = None
    storage_path: Optional[str] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    version: int = 1
    parent_artifact_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime


class EventModel(BaseModel):
    event_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_type: EventType
    event_data: Dict[str, Any] = {}
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    timestamp: datetime
    duration_ms: Optional[int] = None


class MetricModel(BaseModel):
    metric_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    tags: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    timestamp: datetime
