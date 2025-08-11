"""
Base class for orchestration components (scheduler, router, etc).
"""

from abc import ABC, abstractmethod


class BaseOrchestrationComponent(ABC):
    """Abstract base class for orchestration components."""

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
