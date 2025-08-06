"""
base core for opsvi-agents.

Base agent interface
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


class BaseAgentConfig(BaseModel):
    """Configuration for base."""

    # Add specific configuration options here


class BaseAgent(BaseComponent):
    """base implementation."""

    def __init__(self, config: BaseAgentConfig):
        """Initialize base."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)

    def execute(self, input_data: Any) -> Any:
        """Execute the base."""
        # TODO: Implement base logic
        return input_data
