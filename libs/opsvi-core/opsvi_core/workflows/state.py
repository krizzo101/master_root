"""
Workflow state management for OPSVI Core.

Provides workflow state persistence, recovery, and management.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from opsvi_foundation import ComponentError, get_logger
from pydantic import BaseModel, Field

from .definition import WorkflowDefinition
from .engine import WorkflowContext

logger = get_logger(__name__)


class StateError(ComponentError):
    """Raised when state operations fail."""

    pass


class WorkflowState(BaseModel):
    """Workflow execution state."""

    workflow_id: str
    execution_id: str
    current_step: str | None = None
    step_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_step_state(self, step_id: str, state_data: dict[str, Any]) -> None:
        """Update state for a specific step."""
        self.step_states[step_id] = state_data
        self.updated_at = datetime.now()

    def get_step_state(self, step_id: str) -> dict[str, Any] | None:
        """Get state for a specific step."""
        return self.step_states.get(step_id)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a workflow variable."""
        self.variables[name] = value
        self.updated_at = datetime.now()

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a workflow variable."""
        return self.variables.get(name, default)

    def set_output(self, name: str, value: Any) -> None:
        """Set a workflow output."""
        self.outputs[name] = value
        self.updated_at = datetime.now()

    def get_output(self, name: str, default: Any = None) -> Any:
        """Get a workflow output."""
        return self.outputs.get(name, default)


class StateBackend(ABC):
    """Abstract base class for state backends."""

    @abstractmethod
    async def save_state(self, state: WorkflowState) -> None:
        """Save workflow state."""
        pass

    @abstractmethod
    async def load_state(
        self, workflow_id: str, execution_id: str
    ) -> WorkflowState | None:
        """Load workflow state."""
        pass

    @abstractmethod
    async def delete_state(self, workflow_id: str, execution_id: str) -> bool:
        """Delete workflow state."""
        pass

    @abstractmethod
    async def list_states(self, workflow_id: str | None = None) -> list[WorkflowState]:
        """List workflow states."""
        pass


class InMemoryStateBackend(StateBackend):
    """In-memory state backend for development and testing."""

    def __init__(self):
        """Initialize the in-memory backend."""
        self._states: dict[str, WorkflowState] = {}

    async def save_state(self, state: WorkflowState) -> None:
        """Save workflow state to memory."""
        key = f"{state.workflow_id}:{state.execution_id}"
        self._states[key] = state
        logger.debug(f"Saved state: {key}")

    async def load_state(
        self, workflow_id: str, execution_id: str
    ) -> WorkflowState | None:
        """Load workflow state from memory."""
        key = f"{workflow_id}:{execution_id}"
        state = self._states.get(key)
        if state:
            logger.debug(f"Loaded state: {key}")
        return state

    async def delete_state(self, workflow_id: str, execution_id: str) -> bool:
        """Delete workflow state from memory."""
        key = f"{workflow_id}:{execution_id}"
        if key in self._states:
            del self._states[key]
            logger.debug(f"Deleted state: {key}")
            return True
        return False

    async def list_states(self, workflow_id: str | None = None) -> list[WorkflowState]:
        """List workflow states from memory."""
        states = list(self._states.values())
        if workflow_id:
            states = [s for s in states if s.workflow_id == workflow_id]
        return states


class FileStateBackend(StateBackend):
    """File-based state backend for persistence."""

    def __init__(self, storage_path: str = "./workflow_states"):
        """Initialize the file backend."""
        import os

        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _get_state_path(self, workflow_id: str, execution_id: str) -> str:
        """Get file path for state."""
        import os

        filename = f"{workflow_id}_{execution_id}.json"
        return os.path.join(self.storage_path, filename)

    async def save_state(self, state: WorkflowState) -> None:
        """Save workflow state to file."""
        try:
            path = self._get_state_path(state.workflow_id, state.execution_id)

            # Convert to dict and serialize
            state_dict = state.dict()
            state_dict["created_at"] = state_dict["created_at"].isoformat()
            state_dict["updated_at"] = state_dict["updated_at"].isoformat()

            with open(path, "w") as f:
                json.dump(state_dict, f, indent=2)

            logger.debug(f"Saved state to file: {path}")

        except Exception as e:
            raise StateError(f"Failed to save state: {e}") from e

    async def load_state(
        self, workflow_id: str, execution_id: str
    ) -> WorkflowState | None:
        """Load workflow state from file."""
        try:
            import os

            path = self._get_state_path(workflow_id, execution_id)

            if not os.path.exists(path):
                return None

            with open(path) as f:
                state_dict = json.load(f)

            # Parse datetime fields
            state_dict["created_at"] = datetime.fromisoformat(state_dict["created_at"])
            state_dict["updated_at"] = datetime.fromisoformat(state_dict["updated_at"])

            state = WorkflowState(**state_dict)
            logger.debug(f"Loaded state from file: {path}")
            return state

        except Exception as e:
            raise StateError(f"Failed to load state: {e}") from e

    async def delete_state(self, workflow_id: str, execution_id: str) -> bool:
        """Delete workflow state file."""
        try:
            import os

            path = self._get_state_path(workflow_id, execution_id)

            if os.path.exists(path):
                os.remove(path)
                logger.debug(f"Deleted state file: {path}")
                return True
            return False

        except Exception as e:
            raise StateError(f"Failed to delete state: {e}") from e

    async def list_states(self, workflow_id: str | None = None) -> list[WorkflowState]:
        """List workflow states from files."""
        try:
            import glob
            import os

            states = []
            pattern = os.path.join(self.storage_path, "*.json")

            for file_path in glob.glob(pattern):
                try:
                    with open(file_path) as f:
                        state_dict = json.load(f)

                    # Parse datetime fields
                    state_dict["created_at"] = datetime.fromisoformat(
                        state_dict["created_at"]
                    )
                    state_dict["updated_at"] = datetime.fromisoformat(
                        state_dict["updated_at"]
                    )

                    state = WorkflowState(**state_dict)

                    if workflow_id is None or state.workflow_id == workflow_id:
                        states.append(state)

                except Exception as e:
                    logger.warning(f"Failed to load state from {file_path}: {e}")
                    continue

            return states

        except Exception as e:
            raise StateError(f"Failed to list states: {e}") from e


class StateManager:
    """Manager for workflow state operations."""

    def __init__(self, backend: StateBackend | None = None):
        """Initialize the state manager."""
        self.backend = backend or InMemoryStateBackend()
        self._cache: dict[str, WorkflowState] = {}

    async def initialize(
        self, workflow_definition: "WorkflowDefinition", context: "WorkflowContext"
    ) -> WorkflowState:
        """
        Initialize workflow state.

        Args:
            workflow_definition: Workflow definition
            context: Workflow execution context

        Returns:
            Initialized workflow state
        """
        # Check if state already exists
        existing_state = await self.backend.load_state(
            workflow_definition.id, context.execution_id
        )

        if existing_state:
            logger.info(f"Using existing state for execution: {context.execution_id}")
            self._cache[context.execution_id] = existing_state
            return existing_state

        # Create new state
        state = WorkflowState(
            workflow_id=workflow_definition.id,
            execution_id=context.execution_id,
            variables=context.variables.copy(),
            metadata=context.metadata.copy(),
        )

        # Save initial state
        await self.backend.save_state(state)
        self._cache[context.execution_id] = state

        logger.info(f"Initialized new state for execution: {context.execution_id}")
        return state

    async def get_state(self, execution_id: str) -> WorkflowState | None:
        """Get workflow state for execution."""
        # Check cache first
        if execution_id in self._cache:
            return self._cache[execution_id]

        # Load from backend
        # Note: We need workflow_id to load from backend
        # This is a limitation of the current design
        return None

    async def update_state(self, state: WorkflowState) -> None:
        """Update workflow state."""
        state.updated_at = datetime.now()
        await self.backend.save_state(state)
        self._cache[state.execution_id] = state

    async def update_step_state(
        self, execution_id: str, step_id: str, state_data: dict[str, Any]
    ) -> None:
        """Update state for a specific step."""
        state = await self.get_state(execution_id)
        if state:
            state.update_step_state(step_id, state_data)
            await self.update_state(state)

    async def set_variable(self, execution_id: str, name: str, value: Any) -> None:
        """Set a workflow variable."""
        state = await self.get_state(execution_id)
        if state:
            state.set_variable(name, value)
            await self.update_state(state)

    async def get_variable(
        self, execution_id: str, name: str, default: Any = None
    ) -> Any:
        """Get a workflow variable."""
        state = await self.get_state(execution_id)
        if state:
            return state.get_variable(name, default)
        return default

    async def set_output(self, execution_id: str, name: str, value: Any) -> None:
        """Set a workflow output."""
        state = await self.get_state(execution_id)
        if state:
            state.set_output(name, value)
            await self.update_state(state)

    async def get_output(
        self, execution_id: str, name: str, default: Any = None
    ) -> Any:
        """Get a workflow output."""
        state = await self.get_state(execution_id)
        if state:
            return state.get_output(name, default)
        return default

    async def cleanup_state(self, execution_id: str) -> None:
        """Clean up state for an execution."""
        # Remove from cache
        self._cache.pop(execution_id, None)

        # Note: We don't delete from backend by default
        # This allows for state recovery and debugging
        logger.debug(f"Cleaned up state cache for execution: {execution_id}")

    async def list_execution_states(
        self, workflow_id: str | None = None
    ) -> list[WorkflowState]:
        """List all execution states."""
        return await self.backend.list_states(workflow_id)
