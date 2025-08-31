import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List


class Agent(ABC):
    """Base Agent class for HECATON specialized agents."""

    def __init__(self, name: str, capabilities: List[str] = None):
        """Initialize base agent with common attributes.

        Args:
            name: Agent name/identifier
            capabilities: List of agent capabilities
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.capabilities = capabilities or []
        self.created_at = datetime.utcnow()
        self.task_history = []

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return results.

        Args:
            task: Task dictionary containing task details

        Returns:
            Dictionary containing execution results
        """
        pass

    def log_task(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Log task execution for history tracking.

        Args:
            task: The executed task
            result: The task result
        """
        self.task_history.append(
            {"timestamp": datetime.utcnow().isoformat(), "task": task, "result": result}
        )

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities."""
        return self.capabilities

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "id": self.id,
            "name": self.name,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat(),
            "task_count": len(self.task_history),
        }
