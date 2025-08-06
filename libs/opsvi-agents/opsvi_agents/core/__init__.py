"""
Core module for opsvi-agents.

Domain-specific configuration and exceptions.
"""

from .config import AgentsConfig, config
from .exceptions import AgentsConfigurationError, AgentsError, AgentsValidationError

__all__ = [
    "AgentsConfig",
    "AgentsConfigurationError",
    "AgentsError",
    "AgentsValidationError",
    "config",
]
