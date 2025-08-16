"""
Correlation Context for Cross-Component Tracing

Enables tracking of operations across the entire DAG workflow with unique identifiers.
"""

import contextvars
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class CorrelationContext:
    """Context for correlating logs across workflow components"""

    # Primary identifiers
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Workflow context
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None

    # Execution context
    user_request: Optional[str] = None
    complexity_score: Optional[float] = None
    execution_mode: Optional[str] = None  # "linear" or "dag"

    # Timing context
    started_at: datetime = field(default_factory=datetime.now)
    parent_correlation_id: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def create_child_context(
        self, task_id: Optional[str] = None, agent_id: Optional[str] = None, **metadata
    ) -> "CorrelationContext":
        """Create a child context for sub-operations"""
        return CorrelationContext(
            correlation_id=str(uuid.uuid4()),
            session_id=self.session_id,
            workflow_id=self.workflow_id,
            task_id=task_id or self.task_id,
            agent_id=agent_id or self.agent_id,
            user_request=self.user_request,
            complexity_score=self.complexity_score,
            execution_mode=self.execution_mode,
            parent_correlation_id=self.correlation_id,
            metadata={**self.metadata, **metadata},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging"""
        return {
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "user_request": self.user_request,
            "complexity_score": self.complexity_score,
            "execution_mode": self.execution_mode,
            "started_at": self.started_at.isoformat(),
            "parent_correlation_id": self.parent_correlation_id,
            "metadata": self.metadata,
        }


# Context variable for correlation tracking
_correlation_context: contextvars.ContextVar[
    Optional[CorrelationContext]
] = contextvars.ContextVar("correlation_context", default=None)


def get_correlation_context() -> Optional[CorrelationContext]:
    """Get the current correlation context"""
    return _correlation_context.get()


def set_correlation_context(context: CorrelationContext) -> None:
    """Set the correlation context for the current execution"""
    _correlation_context.set(context)


def create_correlation_context(
    user_request: str,
    complexity_score: Optional[float] = None,
    execution_mode: Optional[str] = None,
    **metadata,
) -> CorrelationContext:
    """Create and set a new correlation context for a workflow"""
    context = CorrelationContext(
        user_request=user_request,
        complexity_score=complexity_score,
        execution_mode=execution_mode,
        metadata=metadata,
    )
    set_correlation_context(context)
    return context


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a temporary one"""
    context = get_correlation_context()
    if context:
        return context.correlation_id
    return str(uuid.uuid4())


class CorrelationContextManager:
    """Context manager for scoped correlation contexts"""

    def __init__(self, context: CorrelationContext):
        self.context = context
        self.previous_context = None

    def __enter__(self) -> CorrelationContext:
        self.previous_context = get_correlation_context()
        set_correlation_context(self.context)
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_context:
            set_correlation_context(self.previous_context)
        else:
            _correlation_context.set(None)
