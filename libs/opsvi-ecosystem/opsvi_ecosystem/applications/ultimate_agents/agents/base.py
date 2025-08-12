"""
Base class for all agent types. Defines the common interface and lifecycle methods for agents.
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def act(self, *args, **kwargs):
        """Perform the agent's primary action."""
        pass

    @abstractmethod
    def observe(self, *args, **kwargs):
        """Receive observations or inputs from the environment/system."""
        pass
