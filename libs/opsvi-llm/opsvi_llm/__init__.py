"""
OPSVI LLM Library

Unified LLM integration library for the OPSVI ecosystem.
Provides interfaces for OpenAI, Anthropic, and other LLM providers with structured outputs.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

from .providers.anthropic_provider import AnthropicProvider
from .providers.base import BaseLLMProvider
from .providers.openai_provider import OpenAIProvider
from .schemas.responses import ChatMessage, FunctionCall, LLMResponse
from .utils.rate_limiting import RateLimiter
from .utils.retry import retry_with_backoff

__all__ = [
    # Schemas
    "LLMResponse",
    "ChatMessage",
    "FunctionCall",
    # Providers
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    # Utilities
    "retry_with_backoff",
    "RateLimiter",
]
