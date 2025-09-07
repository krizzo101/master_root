"""Base Agent class for HECATON specialized agents."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Agent(ABC):
    """Base Agent class for all specialized agents."""

    def __init__(self, name: str, capabilities: List[str]):
        """Initialize base agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.capabilities = capabilities
        self.status = "idle"

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task.

        Args:
            task: Task dictionary containing task details

        Returns:
            Result dictionary with execution results
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary with agent details
        """
        return {
            "id": self.id,
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status,
            "type": self.__class__.__name__,
        }

    def set_status(self, status: str):
        """Set agent status.

        Args:
            status: New status
        """
        self.status = status
