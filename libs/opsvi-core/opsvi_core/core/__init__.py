"""
Core module for opsvi-core.

Domain-specific configuration and exceptions.
"""

from .config import CoreConfig, config
from .exceptions import AgentError, CoreError, WorkflowError

__all__ = [
    "CoreConfig",
    "config",
    "CoreError",
    "AgentError",
    "WorkflowError",
]
