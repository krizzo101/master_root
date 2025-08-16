"""
Workflow definition and parsing for OPSVI Core.

Provides workflow definition parsing, validation, and management.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

import yaml
from opsvi_foundation import ComponentError, get_logger
from pydantic import BaseModel, Field, validator

logger = get_logger(__name__)


class WorkflowDefinitionError(ComponentError):
    """Raised when workflow definition is invalid."""

    pass


class StepType(str, Enum):
    """Types of workflow steps."""

    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    SUBWORKFLOW = "subworkflow"


class StepStatus(str, Enum):
    """Status of workflow steps."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepDefinition(BaseModel):
    """Definition of a workflow step."""

    id: str
    name: str
    type: StepType
    description: str | None = None
    action: str = Field(description="Action to execute")
    parameters: dict[str, Any] = Field(default_factory=dict)
    conditions: dict[str, Any] | None = None
    retry_policy: dict[str, Any] | None = None
    timeout: float | None = None
    depends_on: list[str] = Field(default_factory=list)
    parallel: bool = False
    error_handler: str | None = None

    @validator("id")
    def validate_id(cls, v):
        """Validate step ID."""
        if not v or not v.strip():
            raise ValueError("Step ID cannot be empty")
        return v.strip()

    @validator("action")
    def validate_action(cls, v):
        """Validate action."""
        if not v or not v.strip():
            raise ValueError("Action cannot be empty")
        return v.strip()


class WorkflowDefinition(BaseModel):
    """Definition of a workflow."""

    id: str
    name: str
    version: str = "1.0.0"
    description: str | None = None
    author: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Workflow structure
    steps: list[StepDefinition] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("id")
    def validate_id(cls, v):
        """Validate workflow ID."""
        if not v or not v.strip():
            raise ValueError("Workflow ID cannot be empty")
        return v.strip()

    @validator("name")
    def validate_name(cls, v):
        """Validate workflow name."""
        if not v or not v.strip():
            raise ValueError("Workflow name cannot be empty")
        return v.strip()

    @validator("steps")
    def validate_steps(cls, v):
        """Validate workflow steps."""
        if not v:
            raise ValueError("Workflow must have at least one step")

        # Check for duplicate step IDs
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step IDs found")

        # Validate dependencies
        for step in v:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.id} depends on undefined step {dep}")

        return v

    def get_step(self, step_id: str) -> StepDefinition | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_dependent_steps(self, step_id: str) -> list[StepDefinition]:
        """Get steps that depend on the given step."""
        dependent_steps = []
        for step in self.steps:
            if step_id in step.depends_on:
                dependent_steps.append(step)
        return dependent_steps

    def validate_workflow(self) -> list[str]:
        """Validate the workflow definition and return any errors."""
        errors = []

        try:
            # Basic validation
            self.validate_steps(self.steps)
        except ValueError as e:
            errors.append(str(e))

        # Check for circular dependencies
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in workflow steps")

        # Check for orphaned steps
        orphaned_steps = self._find_orphaned_steps()
        if orphaned_steps:
            errors.append(f"Orphaned steps found: {', '.join(orphaned_steps)}")

        return errors

    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies in workflow steps."""
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False

            visited.add(step_id)
            rec_stack.add(step_id)

            step = self.get_step(step_id)
            if step:
                for dep in step.depends_on:
                    if has_cycle(dep):
                        return True

            rec_stack.remove(step_id)
            return False

        for step in self.steps:
            if has_cycle(step.id):
                return True

        return False

    def _find_orphaned_steps(self) -> list[str]:
        """Find steps that are not reachable from any entry point."""
        # Find entry points (steps with no dependencies)
        entry_points = [step.id for step in self.steps if not step.depends_on]

        if not entry_points:
            return [step.id for step in self.steps]

        # Find all reachable steps
        reachable = set()
        to_visit = entry_points.copy()

        while to_visit:
            current = to_visit.pop(0)
            if current in reachable:
                continue

            reachable.add(current)
            step = self.get_step(current)
            if step:
                for dep in step.depends_on:
                    if dep not in reachable:
                        to_visit.append(dep)

        # Return unreachable steps
        all_step_ids = {step.id for step in self.steps}
        return list(all_step_ids - reachable)


class WorkflowDefinitionParser:
    """Parser for workflow definitions."""

    @staticmethod
    def parse_yaml(yaml_content: str) -> WorkflowDefinition:
        """
        Parse workflow definition from YAML.

        Args:
            yaml_content: YAML content as string

        Returns:
            Parsed workflow definition

        Raises:
            WorkflowDefinitionError: If parsing fails
        """
        try:
            data = yaml.safe_load(yaml_content)
            return WorkflowDefinitionParser._parse_dict(data)
        except yaml.YAMLError as e:
            raise WorkflowDefinitionError(f"Invalid YAML: {e}") from e
        except Exception as e:
            raise WorkflowDefinitionError(
                f"Failed to parse workflow definition: {e}"
            ) from e

    @staticmethod
    def parse_json(json_content: str) -> WorkflowDefinition:
        """
        Parse workflow definition from JSON.

        Args:
            json_content: JSON content as string

        Returns:
            Parsed workflow definition

        Raises:
            WorkflowDefinitionError: If parsing fails
        """
        try:
            data = json.loads(json_content)
            return WorkflowDefinitionParser._parse_dict(data)
        except json.JSONDecodeError as e:
            raise WorkflowDefinitionError(f"Invalid JSON: {e}") from e
        except Exception as e:
            raise WorkflowDefinitionError(
                f"Failed to parse workflow definition: {e}"
            ) from e

    @staticmethod
    def _parse_dict(data: dict[str, Any]) -> WorkflowDefinition:
        """Parse workflow definition from dictionary."""
        try:
            # Parse steps
            steps_data = data.get("steps", [])
            steps = []
            for step_data in steps_data:
                step = StepDefinition(**step_data)
                steps.append(step)

            # Create workflow definition
            workflow_data = {k: v for k, v in data.items() if k != "steps"}
            workflow_data["steps"] = steps

            return WorkflowDefinition(**workflow_data)

        except Exception as e:
            raise WorkflowDefinitionError(f"Failed to parse workflow data: {e}") from e

    @staticmethod
    def to_yaml(workflow: WorkflowDefinition) -> str:
        """
        Convert workflow definition to YAML.

        Args:
            workflow: Workflow definition to convert

        Returns:
            YAML representation
        """
        try:
            data = workflow.dict()
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise WorkflowDefinitionError(f"Failed to convert to YAML: {e}") from e

    @staticmethod
    def to_json(workflow: WorkflowDefinition) -> str:
        """
        Convert workflow definition to JSON.

        Args:
            workflow: Workflow definition to convert

        Returns:
            JSON representation
        """
        try:
            data = workflow.dict()
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            raise WorkflowDefinitionError(f"Failed to convert to JSON: {e}") from e


class WorkflowDefinitionRegistry:
    """Registry for workflow definitions."""

    def __init__(self):
        """Initialize the registry."""
        self._workflows: dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> None:
        """
        Register a workflow definition.

        Args:
            workflow: Workflow definition to register

        Raises:
            WorkflowDefinitionError: If workflow is invalid or already exists
        """
        # Validate workflow
        errors = workflow.validate_workflow()
        if errors:
            raise WorkflowDefinitionError(f"Invalid workflow: {'; '.join(errors)}")

        # Check if already exists
        if workflow.id in self._workflows:
            raise WorkflowDefinitionError(f"Workflow {workflow.id} already registered")

        self._workflows[workflow.id] = workflow
        logger.info(f"Registered workflow: {workflow.id}")

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        """
        Get a workflow definition by ID.

        Args:
            workflow_id: ID of the workflow to get

        Returns:
            Workflow definition if found, None otherwise
        """
        return self._workflows.get(workflow_id)

    def list(self) -> list[WorkflowDefinition]:
        """
        List all registered workflows.

        Returns:
            List of workflow definitions
        """
        return list(self._workflows.values())

    def unregister(self, workflow_id: str) -> bool:
        """
        Unregister a workflow definition.

        Args:
            workflow_id: ID of the workflow to unregister

        Returns:
            True if unregistered, False if not found
        """
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            logger.info(f"Unregistered workflow: {workflow_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all registered workflows."""
        self._workflows.clear()
        logger.info("Cleared all workflow definitions")
