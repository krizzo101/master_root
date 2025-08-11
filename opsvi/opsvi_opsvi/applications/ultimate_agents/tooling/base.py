"""
Base class for tooling components (codegen, testing, etc).
"""

from abc import ABC, abstractmethod


class BaseToolingComponent(ABC):
    """Abstract base class for tooling components."""

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
