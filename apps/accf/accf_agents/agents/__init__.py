"""
Agent base classes and registry.

This module provides the foundation for all agents in the ACCF Research Agent system,
including the base agent class, task/result models, and agent discovery mechanisms.
"""

# Import base classes and models
from typing import Dict, Any, Optional, List
from .base import Task, Result, BaseAgent

# Import agent classes
from .consult_agent import ConsultAgent
from .knowledge_agent import KnowledgeAgent
from .memory_agent import MemoryAgent
from .collaboration_agent import CollaborationAgent


class AgentRegistry:
    """Registry for managing agent instances."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_types: Dict[str, type] = {}

    def register(self, agent_type: str, agent_class: type) -> None:
        """Register an agent class."""
        self._agent_types[agent_type] = agent_class

    def create_agent(self, agent_type: str, name: str, settings: Any) -> BaseAgent:
        """Create an agent instance."""
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = self._agent_types[agent_type]
        agent = agent_class(name, settings)
        self._agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def list_agent_types(self) -> List[str]:
        """List all registered agent types."""
        return list(self._agent_types.keys())


# Global agent registry
agent_registry = AgentRegistry()

# Export all classes
__all__ = [
    "Task",
    "Result",
    "BaseAgent",
    "AgentRegistry",
    "agent_registry",
    "ConsultAgent",
    "KnowledgeAgent",
    "MemoryAgent",
    "CollaborationAgent",
]
