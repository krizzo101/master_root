"""
opsvi-llm Library

Domain-specific components for the OPSVI ecosystem.
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

# Import domain-specific components
from .core import LLMConfig, config
from .core.exceptions import LLMConfigurationError, LLMError, LLMValidationError

__all__ = [
    # Foundation exports
    "FoundationConfig",
    "AuthManager",
    "CircuitBreaker",
    "BaseComponent",
    "get_logger",
    # Domain exports
    "LLMConfig",
    "config",
    "LLMError",
    "LLMValidationError",
    "LLMConfigurationError",
]
