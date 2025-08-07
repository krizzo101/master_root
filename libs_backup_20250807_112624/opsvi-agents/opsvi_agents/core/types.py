"""
types core for opsvi-agents.

Agent types and enums
"""

from dataclasses import dataclass
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel


class AgentError(ComponentError):
    """Raised when agent operations fail."""


@dataclass
class AgentState:
    """Represents agent state."""

    id: str
    status: str
    data: dict[str, Any]


class AgentTypesConfig(BaseModel):
    """Configuration for types."""

    # Add specific configuration options here


class AgentTypes(BaseComponent):
    """types implementation."""

    def __init__(self, config: AgentTypesConfig):
        """Initialize types."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)

    def execute(self, input_data: Any) -> Any:
        """Execute the types."""
        # TODO: Implement types logic
        return input_data
