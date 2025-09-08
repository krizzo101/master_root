#!/usr/bin/env python3
"""
Enhanced Agent Task Class

Extends base AgentTask with enhanced features for monitoring, quality gates,
and background execution. Fully backward compatible with standard tasks.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EnhancedAgentTask:
    """
    Enhanced agent task with quality gate and monitoring support.

    Core fields (compatible with base AgentTask):
    - task_id: Unique task identifier
    - task_type: Type of task (e.g., "code_generation", "analysis")
    - prompt: Task prompt/instructions
    - context: Additional context data
    - dependencies: List of task IDs this task depends on
    - status: Current status ("pending", "running", "completed", "failed")
    - result: Task execution result
    - error: Error message if failed
    - start_time: Execution start timestamp
    - end_time: Execution end timestamp

    Enhanced fields:
    - quality_gates: List of quality gate IDs this task depends on
    - validation_required: Whether to validate deliverable
    - phase_id: Execution phase this task belongs to
    - agent_uuid: Predictable UUID for log file tracking
    - team_id: Team identifier for coordinated execution
    - monitoring_enabled: Enable real-time monitoring
    - background_execution: Allow background execution
    """

    # Core fields (backward compatible)
    task_id: str
    task_type: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    # Enhanced fields for quality gates
    quality_gates: List[str] = field(default_factory=list)
    validation_required: bool = True
    phase_id: Optional[str] = None

    # Enhanced fields for monitoring
    agent_uuid: Optional[str] = None
    team_id: Optional[str] = None
    monitoring_enabled: bool = True
    background_execution: bool = False

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing"""
        # Generate UUID if not provided
        if self.agent_uuid is None:
            self.agent_uuid = str(uuid.uuid4())

        # Extract team_id from agent_uuid if follows pattern
        if self.team_id is None and self.agent_uuid:
            parts = self.agent_uuid.split("-")
            if len(parts) >= 3 and parts[0] == "team":
                self.team_id = "-".join(parts[:3])  # team-phase1-001

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            # Core fields
            "task_id": self.task_id,
            "task_type": self.task_type,
            "prompt": self.prompt,
            "context": self.context,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            # Enhanced fields
            "quality_gates": self.quality_gates,
            "validation_required": self.validation_required,
            "phase_id": self.phase_id,
            "agent_uuid": self.agent_uuid,
            "team_id": self.team_id,
            "monitoring_enabled": self.monitoring_enabled,
            "background_execution": self.background_execution,
            "metadata": self.metadata,
            # Computed fields
            "duration": (self.end_time - self.start_time)
            if self.end_time and self.start_time
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedAgentTask":
        """Create task from dictionary representation"""
        # Remove computed fields that shouldn't be set
        data = data.copy()
        data.pop("duration", None)

        return cls(**data)

    def is_ready(self) -> bool:
        """Check if task is ready to run (no pending dependencies)"""
        return self.status == "pending" and not self.dependencies

    def mark_running(self):
        """Mark task as running"""
        self.status = "running"
        self.start_time = datetime.now().timestamp()

    def mark_completed(self, result: Any = None):
        """Mark task as completed"""
        self.status = "completed"
        self.end_time = datetime.now().timestamp()
        if result is not None:
            self.result = result

    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = "failed"
        self.end_time = datetime.now().timestamp()
        self.error = error

    def get_duration(self) -> Optional[float]:
        """Get task execution duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def add_metadata(self, key: str, value: Any):
        """Add metadata to task"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)

    def __str__(self) -> str:
        """String representation"""
        return (
            f"EnhancedAgentTask(id={self.task_id}, type={self.task_type}, "
            f"status={self.status}, uuid={self.agent_uuid})"
        )

    def __repr__(self) -> str:
        """Detailed representation"""
        return (
            f"EnhancedAgentTask(task_id='{self.task_id}', "
            f"task_type='{self.task_type}', status='{self.status}', "
            f"agent_uuid='{self.agent_uuid}', team_id='{self.team_id}', "
            f"dependencies={self.dependencies}, quality_gates={self.quality_gates})"
        )


class TaskFactory:
    """Factory for creating enhanced tasks with common configurations"""

    @staticmethod
    def create_simple_task(
        task_id: str, task_type: str, prompt: str, dependencies: List[str] = None
    ) -> EnhancedAgentTask:
        """Create a simple task without enhanced features"""
        return EnhancedAgentTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            monitoring_enabled=False,
            validation_required=False,
            quality_gates=[],
        )

    @staticmethod
    def create_monitored_task(
        task_id: str,
        task_type: str,
        prompt: str,
        team_id: str = None,
        dependencies: List[str] = None,
    ) -> EnhancedAgentTask:
        """Create a task with monitoring enabled"""
        agent_uuid = None
        if team_id:
            # Generate predictable UUID for team tasks
            import hashlib

            hash_input = f"{team_id}-{task_id}"
            agent_uuid = f"{team_id}-{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"

        return EnhancedAgentTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            team_id=team_id,
            agent_uuid=agent_uuid,
            monitoring_enabled=True,
            validation_required=False,
        )

    @staticmethod
    def create_quality_gated_task(
        task_id: str,
        task_type: str,
        prompt: str,
        quality_gates: List[str],
        phase_id: str = None,
        dependencies: List[str] = None,
    ) -> EnhancedAgentTask:
        """Create a task with quality gate requirements"""
        return EnhancedAgentTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            quality_gates=quality_gates,
            validation_required=True,
            phase_id=phase_id,
            monitoring_enabled=True,
        )

    @staticmethod
    def create_background_task(
        task_id: str,
        task_type: str,
        prompt: str,
        team_id: str,
        dependencies: List[str] = None,
    ) -> EnhancedAgentTask:
        """Create a task for background execution"""
        return EnhancedAgentTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            dependencies=dependencies or [],
            team_id=team_id,
            background_execution=True,
            monitoring_enabled=True,
            validation_required=False,
        )

    @staticmethod
    def create_from_base_task(
        base_task: Dict[str, Any],
        enable_monitoring: bool = False,
        quality_gates: List[str] = None,
    ) -> EnhancedAgentTask:
        """Create enhanced task from base task dictionary"""
        # Extract base fields
        task = EnhancedAgentTask(
            task_id=base_task.get("task_id", str(uuid.uuid4())),
            task_type=base_task.get("task_type", "generic"),
            prompt=base_task.get("prompt", ""),
            context=base_task.get("context", {}),
            dependencies=base_task.get("dependencies", []),
            status=base_task.get("status", "pending"),
            result=base_task.get("result"),
            error=base_task.get("error"),
            start_time=base_task.get("start_time"),
            end_time=base_task.get("end_time"),
        )

        # Add enhanced features if requested
        if enable_monitoring:
            task.monitoring_enabled = True

        if quality_gates:
            task.quality_gates = quality_gates
            task.validation_required = True

        return task
