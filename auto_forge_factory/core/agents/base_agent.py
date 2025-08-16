"""
Base agent class for the Auto-Forge factory.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from ...models.schemas import AgentType, AgentConfig, JobStatus, Artifact


class AgentResult(BaseModel):
    """Result from an agent execution."""

    success: bool
    content: str
    artifacts: List[Artifact] = []
    metadata: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    execution_time_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class BaseAgent(ABC):
    """Base class for all agents in the Auto-Forge factory."""

    def __init__(
        self,
        agent_type: AgentType,
        job_id: UUID,
        config: Optional[AgentConfig] = None,
        **kwargs,
    ):
        """Initialize the base agent.

        Args:
            agent_type: The type of this agent
            job_id: The job ID this agent is working on
            config: Agent configuration
            **kwargs: Additional arguments
        """
        self.agent_type = agent_type
        self.job_id = job_id
        self.config = config
        self.logger = logging.getLogger(f"agent.{agent_type.value}")
        self.status = JobStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.progress_percent = 0.0
        self.current_task = ""
        self.artifacts_generated = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, Any] = {}

        # Initialize agent-specific attributes
        self._init_agent(**kwargs)

    def _init_agent(self, **kwargs):
        """Initialize agent-specific attributes. Override in subclasses."""
        pass

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute the agent's main logic.

        Args:
            inputs: Input data for the task

        Returns:
            AgentResult with execution results
        """
        pass

    async def run(self, inputs: Dict[str, Any]) -> AgentResult:
        """Run the agent with proper error handling and timing.

        Args:
            inputs: Input data for the task

        Returns:
            AgentResult with execution results
        """
        self.start_time = datetime.utcnow()
        self.status = JobStatus.RUNNING
        self.progress_percent = 0.0

        try:
            self.logger.info(
                f"Starting {self.agent_type.value} agent for job {self.job_id}"
            )

            # Execute the agent's logic
            result = await self.execute(inputs)

            # Update status and timing
            self.end_time = datetime.utcnow()
            self.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
            self.progress_percent = 100.0
            self.artifacts_generated = len(result.artifacts)
            self.errors = result.errors
            self.warnings = result.warnings
            self.metrics = result.metadata

            execution_time = (self.end_time - self.start_time).total_seconds()
            result.execution_time_seconds = execution_time

            self.logger.info(
                f"Completed {self.agent_type.value} agent for job {self.job_id} "
                f"in {execution_time:.2f}s (success: {result.success})"
            )

            return result

        except Exception as e:
            self.end_time = datetime.utcnow()
            self.status = JobStatus.FAILED
            self.errors.append(str(e))

            execution_time = (self.end_time - self.start_time).total_seconds()

            self.logger.error(
                f"Failed {self.agent_type.value} agent for job {self.job_id} "
                f"after {execution_time:.2f}s: {e}"
            )

            return AgentResult(
                success=False,
                content=f"Agent execution failed: {e}",
                errors=[str(e)],
                execution_time_seconds=execution_time,
            )

    def update_progress(self, percent: float, task: str = ""):
        """Update the agent's progress.

        Args:
            percent: Progress percentage (0-100)
            task: Current task description
        """
        self.progress_percent = max(0.0, min(100.0, percent))
        if task:
            self.current_task = task

        self.logger.debug(
            f"{self.agent_type.value} agent progress: {self.progress_percent:.1f}% - {task}"
        )

    def add_artifact(
        self, name: str, content: str, artifact_type: str = "code", **metadata
    ) -> Artifact:
        """Add an artifact to the agent's output.

        Args:
            name: Artifact name
            content: Artifact content
            artifact_type: Type of artifact
            **metadata: Additional metadata

        Returns:
            Created artifact
        """
        artifact = Artifact(
            name=name,
            type=artifact_type,
            path=f"artifacts/{self.job_id}/{self.agent_type.value}/{name}",
            content=content,
            size_bytes=len(content.encode("utf-8")),
            metadata=metadata,
        )

        self.artifacts_generated += 1
        self.logger.debug(f"Generated artifact: {name} ({artifact_type})")

        return artifact

    def add_error(self, error: str):
        """Add an error to the agent's error list.

        Args:
            error: Error message
        """
        self.errors.append(error)
        self.logger.error(f"{self.agent_type.value} agent error: {error}")

    def add_warning(self, warning: str):
        """Add a warning to the agent's warning list.

        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
        self.logger.warning(f"{self.agent_type.value} agent warning: {warning}")

    def add_metric(self, key: str, value: Any):
        """Add a metric to the agent's metrics.

        Args:
            key: Metric key
            value: Metric value
        """
        self.metrics[key] = value

    async def cleanup(self):
        """Clean up agent resources. Override in subclasses if needed."""
        self.logger.debug(
            f"Cleaning up {self.agent_type.value} agent for job {self.job_id}"
        )

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's current status.

        Returns:
            Status summary dictionary
        """
        return {
            "agent_type": self.agent_type.value,
            "job_id": str(self.job_id),
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_task": self.current_task,
            "artifacts_generated": self.artifacts_generated,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else None
            ),
        }

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.agent_type.value}Agent(job_id={self.job_id}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"agent_type={self.agent_type.value}, "
            f"job_id={self.job_id}, "
            f"status={self.status.value}, "
            f"progress={self.progress_percent:.1f}%"
            f")"
        )
