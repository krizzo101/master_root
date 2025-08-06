"""
Core module for opsvi-llm.

Domain-specific configuration and exceptions.
"""

from .config import LLMConfig, config
from .exceptions import LLMConfigurationError, LLMError, LLMValidationError

__all__ = [
    "LLMConfig",
    "config",
    "LLMError",
    "LLMValidationError",
    "LLMConfigurationError",
]
