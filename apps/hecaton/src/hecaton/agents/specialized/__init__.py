"""Specialized HECATON agent implementations."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class Agent(ABC):
    """Base agent class for HECATON specialized agents."""

    def __init__(self, name: str, capabilities: Optional[List[str]] = None):
        """Initialize base agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.capabilities = capabilities or []
        self.created_at = datetime.utcnow()
        self.tasks_completed = 0

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task.

        Args:
            task: Task dictionary containing task details

        Returns:
            Result dictionary with execution details
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary containing agent details
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat(),
            "tasks_completed": self.tasks_completed,
        }

    def log_task_completion(self):
        """Log task completion."""
        self.tasks_completed += 1


# Import specialized agents
from .code_agent import CodeAgent
from .research_agent import ResearchAgent
from .test_agent import TestAgent

__all__ = ["Agent", "CodeAgent", "ResearchAgent", "TestAgent"]
