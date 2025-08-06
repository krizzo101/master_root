"""
opsvi-agents Library

Domain-specific components for the OPSVI ecosystem.
Builds on opsvi-foundation for shared concerns.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Import foundation components
from opsvi_foundation import (
    FoundationConfig,
    AuthManager,
    CircuitBreaker,
    BaseComponent,
    get_logger,
)

# Import domain-specific components
from .core import AgentsConfig, config
from .core.exceptions import AgentsError, AgentsValidationError, AgentsConfigurationError

__all__ = [
    # Foundation exports
    "FoundationConfig",
    "AuthManager", 
    "CircuitBreaker",
    "BaseComponent",
    "get_logger",
    # Domain exports
    "AgentsConfig",
    "config",
    "AgentsError",
    "AgentsValidationError", 
    "AgentsConfigurationError",
]
