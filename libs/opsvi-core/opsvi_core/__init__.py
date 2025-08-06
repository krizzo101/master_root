"""
OPSVI Core Library

Application-level components and patterns for the OPSVI ecosystem.
Builds on opsvi-foundation for shared concerns.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Import foundation components
from opsvi_foundation import (
    AuthManager,
    BaseComponent,
    CircuitBreaker,
    FoundationConfig,
    get_logger,
)

# Import core-specific components
from .core import CoreConfig, config
from .core.exceptions import AgentError, CoreError, WorkflowError

__all__ = [
    # Foundation exports
    "FoundationConfig",
    "AuthManager",
    "CircuitBreaker",
    "BaseComponent",
    "get_logger",
    # Core exports
    "CoreConfig",
    "config",
    "CoreError",
    "AgentError",
    "WorkflowError",
]
