"""Base agent class for the autonomous software factory."""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

from opsvi_auto_forge.config.models import AgentRole, Artifact, Result
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution
from opsvi_auto_forge.core.prompting.gateway import PromptGateway

# Optional import to avoid circular dependencies
try:
    from opsvi_auto_forge.infrastructure.memory.vector.context_store import ContextStore
except ImportError:
    ContextStore = None

T = TypeVar("T", bound=BaseModel)


class AgentResponse(BaseModel):
    """Response from an agent execution."""

    success: bool = Field(..., description="Whether the agent execution was successful")
    content: str = Field(..., description="Main content/output from the agent")
    artifacts: List[Dict[str, Any]] = Field(
        default_factory=list, description="Generated artifacts"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Any warnings generated"
    )
    execution_time_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class BaseAgent(ABC):
    """Base class for all agents in the autonomous software factory."""

    def __init__(
        self,
        role: AgentRole,
        neo4j_client: Optional[Neo4jClient] = None,
        logger: Optional[logging.Logger] = None,
        prompt_gateway: Optional[PromptGateway] = None,
        context_store: Optional[ContextStore] = None,
    ):
        """Initialize the base agent.

        Args:
            role: The role of this agent
            neo4j_client: Optional Neo4j client for lineage tracking
            logger: Optional logger instance
            prompt_gateway: Optional PromptGateway for LLM integration
            context_store: Optional ContextStore for context management
        """
        self.role = role
        self.neo4j_client = neo4j_client
        self.logger = logger or logging.getLogger(f"agent.{role.value}")
        self.prompt_gateway = prompt_gateway
        self.context_store = context_store
        self.execution_id = uuid4()

    @abstractmethod
    async def execute(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Execute the agent's main logic.

        Args:
            task_execution: The task execution instance
            inputs: Input data for the task

        Returns:
            AgentResponse with execution results
        """
        pass

    async def run(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> Result:
        """Run the agent with full lifecycle management.

        Args:
            task_execution: The task execution instance
            inputs: Input data for the task

        Returns:
            Result object with execution outcome
        """
        start_time = time.time()

        try:
            # Log task start
            self.logger.info(
                f"Starting {self.role.value} agent execution",
                extra={
                    "task_id": str(task_execution.id),
                    "execution_id": str(self.execution_id),
                    "inputs": inputs,
                },
            )

            # Execute agent logic
            response = await self.execute(task_execution, inputs)

            # Calculate execution time
            execution_time = time.time() - start_time
            response.execution_time_seconds = execution_time

            # Create artifacts
            artifacts = []
            for artifact_data in response.artifacts:
                artifact = await self._create_artifact(artifact_data)
                artifacts.append(artifact)

            # Create result
            result = Result(
                status="ok" if response.success else "fail",
                score=1.0 if response.success else 0.0,
                metrics={
                    "execution_time_seconds": execution_time,
                    "tokens_used": response.tokens_used or 0,
                    "cost": response.cost or 0.0,
                    "artifacts_count": len(artifacts),
                },
                errors=response.errors,
                warnings=response.warnings,
                execution_time_seconds=execution_time,
            )

            # Log task completion
            self.logger.info(
                f"Completed {self.role.value} agent execution",
                extra={
                    "task_id": str(task_execution.id),
                    "execution_id": str(self.execution_id),
                    "success": response.success,
                    "execution_time": execution_time,
                    "artifacts_count": len(artifacts),
                },
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"Failed {self.role.value} agent execution: {str(e)}",
                extra={
                    "task_id": str(task_execution.id),
                    "execution_id": str(self.execution_id),
                    "error": str(e),
                    "execution_time": execution_time,
                },
                exc_info=True,
            )

            return Result(
                status="fail",
                score=0.0,
                metrics={
                    "execution_time_seconds": execution_time,
                    "tokens_used": 0,
                    "cost": 0.0,
                },
                errors=[str(e)],
                execution_time_seconds=execution_time,
            )

    async def _create_artifact(self, artifact_data: Dict[str, Any]) -> Artifact:
        """Create an artifact from the agent's output.

        Args:
            artifact_data: Artifact data dictionary

        Returns:
            Artifact object
        """
        # Generate content hash
        content = artifact_data.get("content", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Create artifact path
        artifact_type = artifact_data.get("type", "unknown")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{artifact_type}_{timestamp}_{self.execution_id.hex[:8]}.txt"
        artifact_path = f"artifacts/{artifact_type}/{filename}"

        # Ensure directory exists
        Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        with open(artifact_path, "w") as f:
            f.write(content)

        return Artifact(
            type=artifact_data.get("type", "unknown"),
            path=artifact_path,
            hash=content_hash,
            metadata=artifact_data.get("metadata", {}),
            size_bytes=len(content.encode()),
            mime_type="text/plain",
        )

    def _log_decision(
        self,
        task_execution: TaskExecution,
        decision: str,
        confidence: float = 1.0,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a decision made by the agent.

        Args:
            task_execution: The task execution instance
            decision: Description of the decision made
            confidence: Confidence level (0.0 to 1.0)
            params: Additional parameters for the decision
        """
        if self.neo4j_client:
            # This would be implemented when Neo4j integration is complete
            pass

        self.logger.info(
            f"Agent decision: {decision}",
            extra={
                "task_id": str(task_execution.id),
                "execution_id": str(self.execution_id),
                "decision": decision,
                "confidence": confidence,
                "params": params or {},
            },
        )

    async def _call_llm(
        self,
        task_type: str,
        goal: str,
        schema: type[T],
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> T:
        """Call LLM using PromptGateway for structured output.

        Args:
            task_type: Type of task being performed
            goal: User goal or request
            schema: Pydantic schema for structured output
            constraints: Optional constraints for the task
            tools: Optional tools to make available
            **kwargs: Additional parameters for the LLM call

        Returns:
            Structured response matching the schema

        Raises:
            ValueError: If PromptGateway is not available
            Exception: If LLM call fails
        """
        if not self.prompt_gateway:
            raise ValueError("PromptGateway is required for LLM integration")

        try:
            # Call PromptGateway for structured response with schema class
            response_data = await self.prompt_gateway.create_structured_response(
                run_id=str(self.execution_id),
                role=self.role.value,
                task_type=task_type,
                user_goal=goal,
                schema=schema,  # Pass the schema class directly
                constraints=constraints,
                tools=tools,
                **kwargs,
            )

            # The response is already a Pydantic model instance
            return response_data

        except Exception as e:
            self.logger.error(
                f"LLM call failed for {task_type}: {str(e)}",
                extra={
                    "task_type": task_type,
                    "goal": goal,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
