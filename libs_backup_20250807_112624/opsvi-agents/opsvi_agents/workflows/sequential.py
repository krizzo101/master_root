"""
sequential workflow for opsvi-agents.

Sequential workflows
"""

from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel


class WorkflowError(ComponentError):
    """Raised when workflow operations fail."""


class SequentialWorkflowConfig(BaseModel):
    """Configuration for sequential workflow."""

    # Add specific configuration options here


class SequentialWorkflow(BaseComponent):
    """sequential workflow implementation."""

    def __init__(self, config: SequentialWorkflowConfig):
        """Initialize sequential workflow."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)

    def execute(self, input_data: Any) -> Any:
        """Execute the workflow."""
        # TODO: Implement sequential workflow logic
        return input_data
