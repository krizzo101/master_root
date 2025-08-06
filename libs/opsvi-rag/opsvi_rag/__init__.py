"""
opsvi-rag Library

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
from .core import RAGConfig, config
from .core.exceptions import RAGError, RAGValidationError, RAGConfigurationError

__all__ = [
    # Foundation exports
    "FoundationConfig",
    "AuthManager", 
    "CircuitBreaker",
    "BaseComponent",
    "get_logger",
    # Domain exports
    "RAGConfig",
    "config",
    "RAGError",
    "RAGValidationError", 
    "RAGConfigurationError",
]
