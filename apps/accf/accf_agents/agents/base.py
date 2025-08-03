"""
Base classes and models for agents.

This module contains the base classes and models used by all agents
to avoid circular import issues.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging


class Task(BaseModel):
    """Task model for agent execution."""

    id: str
    type: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: Optional[int] = None


class Result(BaseModel):
    """Result model for agent execution."""

    task_id: str
    status: str  # "success", "error", "timeout"
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, settings: Any):
        self.name = name
        self.settings = settings
        self.logger = logging.getLogger(f"agent.{name}")
        self._initialized = False

    @abstractmethod
    async def execute(self, task: Task) -> Result:
        """Execute a task and return a result."""
        pass

    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type."""
        pass

    async def initialize(self) -> None:
        """Initialize the agent (called once before first use)."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def _setup(self) -> None:
        """Internal setup method - override in subclasses if needed."""
        pass

    def get_capabilities(self) -> List[str]:
        """Get list of task types this agent can handle."""
        return []
