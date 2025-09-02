"""
Core schemas for HECATON with validation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..utils.enhanced_logging import get_logger

logger = get_logger(__name__)


class MessageType(Enum):
    """Types of messages in the system"""

    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    TASK_STATUS = "task_status"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class AgentType(Enum):
    """Supported agent types"""

    CODE = "code"
    TEST = "test"
    RESEARCH = "research"
    REVIEW = "review"
    DOCS = "docs"
    SECURITY = "security"
    PERFORMANCE = "performance"


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class PermissionMode(Enum):
    """Claude permission modes for headless execution"""

    PLAN = "plan"  # Default safe mode
    ACCEPT_EDITS = "acceptEdits"
    DEFAULT = "default"
    # Never use dangerously-skip-permissions in production


@dataclass
class Message:
    """Base message with validation"""

    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.TASK_REQUEST
    topic: str = ""
    sender: str = ""
    correlation_id: Optional[UUID] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate message structure"""
        if not self.topic:
            raise ValueError("Message must have a topic")
        if not self.sender:
            raise ValueError("Message must have a sender")
        if self.type == MessageType.TASK_REQUEST and "task" not in self.payload:
            raise ValueError("Task request must have task in payload")
        return True


@dataclass
class AgentTaskRequest:
    """Validated task request for agents"""

    task_id: str
    agent_type: AgentType
    task_prompt: str
    worktree_path: str
    token_index: int
    mcp_profile: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=lambda: ["Read", "Write", "Edit"])
    permission_mode: PermissionMode = PermissionMode.PLAN
    timeout_seconds: int = 300
    max_retries: int = 3
    system_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for executor"""
        return {
            "id": self.task_id,
            "prompt": self.task_prompt,
            "agent_type": self.agent_type.value,
            "worktree": self.worktree_path,
            "token_index": self.token_index,
            "mcp_profile": self.mcp_profile,
            "allowed_tools": self.allowed_tools,
            "permission_mode": self.permission_mode.value,
            "system_prompt": self.system_prompt,
        }

    def validate(self) -> bool:
        """Validate task request"""
        if not self.task_id:
            raise ValueError("Task must have an ID")
        if not self.task_prompt:
            raise ValueError("Task must have a prompt")
        if not self.worktree_path:
            raise ValueError("Task must have a worktree path")
        if self.token_index < 0:
            raise ValueError("Token index must be non-negative")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        return True


@dataclass
class AgentTaskResult:
    """Result from agent execution"""

    task_id: str
    agent_type: AgentType
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    token_usage: Optional[Dict[str, int]] = None
    num_turns: Optional[int] = None

    def is_success(self) -> bool:
        """Check if task succeeded"""
        return self.status == TaskStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "token_usage": self.token_usage,
            "num_turns": self.num_turns,
        }
