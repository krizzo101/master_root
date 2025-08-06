"""
LLM-specific exceptions.

Extends foundation exceptions with LLM domain errors.
"""

from opsvi_foundation import ComponentError


class LLMError(ComponentError):
    """Base exception for opsvi-llm."""
    pass


class LLMValidationError(LLMError):
    """Validation error specific to opsvi-llm."""
    pass


class LLMConfigurationError(LLMError):
    """Configuration error specific to opsvi-llm."""
    pass
