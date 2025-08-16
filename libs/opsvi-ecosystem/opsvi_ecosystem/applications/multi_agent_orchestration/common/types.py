"""
Common data types and structures for the multi-agent orchestration system.

This module defines the core data structures used for communication,
task management, and workflow execution across all components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class MessageType(Enum):
    """Types of messages that can be sent between agents."""

    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COLLABORATION_REQUEST = "collaboration_request"
    BROADCAST = "broadcast"


class TaskStatus(Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(Enum):
    """Types of workflow execution patterns."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class WorkflowStatus(Enum):
    """Status of a workflow in the orchestration system."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """
    Inter-agent communication message.

    Attributes:
        id: Unique message identifier
        sender_id: ID of the sending agent
        recipient_id: ID of the receiving agent (None for broadcast)
        message_type: Type of message being sent
        content: Message payload
        timestamp: When the message was created
        correlation_id: ID to correlate related messages
    """

    sender_id: str
    message_type: MessageType
    content: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    recipient_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None


@dataclass
class Task:
    """
    Represents a unit of work to be executed by an agent.

    Attributes:
        id: Unique task identifier
        name: Human-readable task name
        description: Detailed task description
        agent_id: ID of the agent assigned to this task
        tool_name: Name of the tool to use (if applicable)
        parameters: Task-specific parameters
        dependencies: List of task IDs this task depends on
        status: Current task status
        result: Task execution result
        error: Error information if task failed
        created_at: Task creation timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
    """

    name: str
    description: str
    parameters: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str | None = None
    tool_name: str | None = None
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class TaskResult:
    """
    Result of a single task execution.

    Attributes:
        task_id: Unique task identifier
        status: Task execution status
        result: Task output/result
        error: Error message if task failed
        execution_time: Time taken to execute the task (seconds)
        started_at: Task start time
        completed_at: Task completion time
    """

    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    execution_time: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class AgentCapability:
    """
    Describes a capability that an agent possesses.

    Attributes:
        name: Capability name
        description: What this capability does
        input_schema: Expected input format
        output_schema: Expected output format
        tools_required: List of tools needed for this capability
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tools_required: list[str] = field(default_factory=list)


@dataclass
class ToolSchema:
    """
    Defines the input/output schema for a tool.

    Attributes:
        name: Tool name
        description: What the tool does
        input_schema: JSON schema for input validation
        output_schema: JSON schema for output validation
        required_params: List of required parameter names
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    required_params: list[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.

    Attributes:
        workflow_id: Unique workflow identifier
        status: Overall workflow status
        results: Results from individual tasks
        errors: Any errors that occurred
        execution_time: Total execution time in seconds
        task_count: Number of tasks executed
        started_at: Workflow start time
        completed_at: Workflow completion time
    """

    workflow_id: str
    status: TaskStatus
    results: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    execution_time: float | None = None
    task_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowDefinition:
    """
    Defines a workflow to be executed.

    Attributes:
        id: Unique workflow identifier
        name: Human-readable workflow name
        description: Workflow description
        workflow_type: Type of workflow execution
        tasks: List of tasks in the workflow
        conditions: Conditional logic for branching workflows
        max_parallel: Maximum parallel tasks (for parallel workflows)
        timeout: Workflow timeout in seconds
    """

    name: str
    description: str
    workflow_type: WorkflowType
    tasks: list[Task]
    id: str = field(default_factory=lambda: str(uuid4()))
    conditions: dict[str, Any] = field(default_factory=dict)
    max_parallel: int = 5
    timeout: int = 300  # 5 minutes default


# Custom exceptions for the multi-agent system
class MultiAgentError(Exception):
    """Base exception for multi-agent system errors."""

    pass


class AgentError(MultiAgentError):
    """Exception raised by agent operations."""

    pass


class ToolError(MultiAgentError):
    """Exception raised by tool operations."""

    pass


class WorkflowError(MultiAgentError):
    """Exception raised by workflow operations."""

    pass


class CommunicationError(MultiAgentError):
    """Exception raised by communication operations."""

    pass


# Type aliases for clarity
AgentId = str
TaskId = str
WorkflowId = str
