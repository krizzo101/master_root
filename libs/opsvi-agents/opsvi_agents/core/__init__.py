"""
Core module for opsvi-agents.

Domain-specific configuration and exceptions.
"""

from .config import AgentsConfig, config
from .exceptions import AgentsError, AgentsValidationError, AgentsConfigurationError

__all__ = [
    "AgentsConfig",
    "config", 
    "AgentsError",
    "AgentsValidationError",
    "AgentsConfigurationError",
]
