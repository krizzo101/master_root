"""LLM providers for OPSVI applications."""

from .base import (
    BaseLLMProvider,
    LLMConfig,
    LLMError,
    LLMProviderError,
    LLMConfigError,
    LLMRequestError,
    LLMResponseError,
    Message,
    CompletionRequest,
    ChatRequest,
    EmbeddingRequest,
    CompletionResponse,
    ChatResponse,
    EmbeddingResponse,
)

try:
    from .openai_provider import OpenAIProvider, OpenAIConfig
except ImportError:
    OpenAIProvider = None
    OpenAIConfig = None

try:
    from .perplexity_provider import PerplexityProvider, PerplexityConfig
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
    "OpenAIProvider",
    "OpenAIConfig",
    "PerplexityProvider",
    "PerplexityConfig",
]
