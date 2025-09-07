"""
Event Type Definitions

Defines all event types used in the agent coordination system.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """Core event types for agent coordination"""

    # Coordination Events
    TASK_HANDOFF = "task_handoff"
    HELP_REQUEST = "help_request"
    AGENT_AVAILABLE = "agent_available"
    WORK_REQUEST = "work_request"
    RESOURCE_REQUEST = "resource_request"

    # Progress Events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    MILESTONE_REACHED = "milestone_reached"
    PROGRESS_UPDATE = "progress_update"

    # Discovery Events
    INSIGHT_FOUND = "insight_found"
    PROBLEM_SOLVED = "problem_solved"
    RESOURCE_FOUND = "resource_found"
    KNOWLEDGE_SHARED = "knowledge_shared"

    # System Events
    AGENT_JOINED = "agent_joined"
    AGENT_LEFT = "agent_left"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_SHARED = "workspace_shared"

    # Error Events
    AGENT_ERROR = "agent_error"
    SYSTEM_ALERT = "system_alert"
    COMMUNICATION_FAILURE = "communication_failure"


class Priority(Enum):
    """Event priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BaseEvent:
    """Base class for all events"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = None
    timestamp: float = field(default_factory=time.time)
    source_agent_id: str = ""
    priority: Priority = Priority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else None,
            "timestamp": self.timestamp,
            "source_agent_id": self.source_agent_id,
            "priority": self.priority.value,
            "metadata": self.metadata,
            **self._event_specific_data(),
        }

    def _event_specific_data(self) -> Dict[str, Any]:
        """Override in subclasses for event-specific data"""
        return {}


@dataclass
class CoordinationEvent(BaseEvent):
    """Events for agent coordination and task management"""

    target_agent_ids: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    coordination_type: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def _event_specific_data(self) -> Dict[str, Any]:
        return {
            "target_agent_ids": self.target_agent_ids,
            "task_id": self.task_id,
            "coordination_type": self.coordination_type,
            "payload": self.payload,
        }


@dataclass
class ProgressEvent(BaseEvent):
    """Events for task and agent progress tracking"""

    task_id: str = ""
    progress_percentage: float = 0.0
    status_message: str = ""
    estimated_completion: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def _event_specific_data(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "progress_percentage": self.progress_percentage,
            "status_message": self.status_message,
            "estimated_completion": self.estimated_completion,
            "metrics": self.metrics,
        }


@dataclass
class DiscoveryEvent(BaseEvent):
    """Events for knowledge sharing and discoveries"""

    discovery_type: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 1.0
    shared_artifacts: List[str] = field(default_factory=list)

    def _event_specific_data(self) -> Dict[str, Any]:
        return {
            "discovery_type": self.discovery_type,
            "content": self.content,
            "tags": self.tags,
            "relevance_score": self.relevance_score,
            "shared_artifacts": self.shared_artifacts,
        }


@dataclass
class SystemEvent(BaseEvent):
    """Events for system-level operations"""

    system_component: str = ""
    action: str = ""
    status: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def _event_specific_data(self) -> Dict[str, Any]:
        return {
            "system_component": self.system_component,
            "action": self.action,
            "status": self.status,
            "details": self.details,
        }


@dataclass
class ErrorEvent(BaseEvent):
    """Events for errors and system alerts"""

    error_type: str = ""
    error_message: str = ""
    stack_trace: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    affected_components: List[str] = field(default_factory=list)

    def _event_specific_data(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "recovery_suggestion": self.recovery_suggestion,
            "affected_components": self.affected_components,
        }


# Helper functions for creating specific event instances


def create_task_handoff_event(
    source_agent_id: str,
    target_agent_id: str,
    task_id: str,
    task_data: Dict[str, Any],
    context: str = "",
) -> CoordinationEvent:
    """Create a task handoff event"""
    return CoordinationEvent(
        event_type=EventType.TASK_HANDOFF,
        source_agent_id=source_agent_id,
        target_agent_ids=[target_agent_id],
        task_id=task_id,
        coordination_type="handoff",
        payload={"task_data": task_data, "context": context},
        priority=Priority.HIGH,
    )


def create_help_request_event(
    source_agent_id: str,
    problem_description: str,
    required_skills: List[str] = None,
    urgency: Priority = Priority.NORMAL,
) -> CoordinationEvent:
    """Create a help request event"""
    return CoordinationEvent(
        event_type=EventType.HELP_REQUEST,
        source_agent_id=source_agent_id,
        coordination_type="help_request",
        payload={
            "problem_description": problem_description,
            "required_skills": required_skills or [],
            "urgency": urgency.value,
        },
        priority=urgency,
    )


def create_insight_event(
    source_agent_id: str,
    insight_content: str,
    tags: List[str] = None,
    relevance: float = 1.0,
) -> DiscoveryEvent:
    """Create an insight discovery event"""
    return DiscoveryEvent(
        event_type=EventType.INSIGHT_FOUND,
        source_agent_id=source_agent_id,
        discovery_type="insight",
        content=insight_content,
        tags=tags or [],
        relevance_score=relevance,
    )


def create_progress_event(
    source_agent_id: str, task_id: str, progress: float, message: str = ""
) -> ProgressEvent:
    """Create a progress update event"""
    return ProgressEvent(
        event_type=EventType.PROGRESS_UPDATE,
        source_agent_id=source_agent_id,
        task_id=task_id,
        progress_percentage=progress,
        status_message=message,
    )
