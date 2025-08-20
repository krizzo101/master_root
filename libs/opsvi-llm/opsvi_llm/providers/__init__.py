"""LLM providers for OPSVI applications."""

from .base import (
    BaseLLMProvider,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    LLMConfig,
    LLMConfigError,
    LLMError,
    LLMProviderError,
    LLMRequestError,
    LLMResponseError,
    Message,
)

try:
    from .anthropic_provider import AnthropicConfig, AnthropicProvider
except ImportError:
    AnthropicProvider = None
    AnthropicConfig = None

try:
    from .openai_provider import OpenAIConfig, OpenAIProvider
except ImportError:
    OpenAIProvider = None
    OpenAIConfig = None

try:
    from .perplexity_provider import PerplexityConfig, PerplexityProvider
except ImportError:
    PerplexityProvider = None
    PerplexityConfig = None

__all__ = [
    "BaseLLMProvider",
    "LLMConfig",
    "LLMError",
    "LLMProviderError",
    "LLMConfigError",
    "LLMRequestError",
    "LLMResponseError",
    "Message",
    "CompletionRequest",
    "ChatRequest",
    "EmbeddingRequest",
    "CompletionResponse",
    "ChatResponse",
    "EmbeddingResponse",
    "AnthropicProvider",
    "AnthropicConfig",
    "OpenAIProvider",
    "OpenAIConfig",
    "PerplexityProvider",
    "PerplexityConfig",
]
