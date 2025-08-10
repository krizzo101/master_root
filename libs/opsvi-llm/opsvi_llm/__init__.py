"""opsvi-llm - LLM services for OPSVI applications.

Comprehensive LLM library for the OPSVI ecosystem
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Provider exports
from .providers import (
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
    OpenAIProvider,
    OpenAIConfig,
)

# OpenAI Interface exports
from .providers.openai_embeddings_interface import (
    OpenAIEmbeddingsInterface,
    OpenAIEmbeddingsError,
)

from .providers.openai_models_interface import (
    OpenAIModelsInterface,
    OpenAIModelsError,
    ModelInfo,
)

from .providers.openai_batch_interface import (
    OpenAIBatchInterface,
    OpenAIBatchError,
)

from .providers.openai_responses_interface import (
    OpenAIResponsesInterface,
    AsyncOpenAIResponsesInterface,
    OpenAIResponsesError,
    StructuredResponse,
)

__all__ = [
    # Base classes
    "BaseLLMProvider",
    "LLMConfig",
    "LLMError",
    "LLMProviderError",
    "LLMConfigError",
    "LLMRequestError",
    "LLMResponseError",
    # Data models
    "Message",
    "CompletionRequest",
    "ChatRequest",
    "EmbeddingRequest",
    "CompletionResponse",
    "ChatResponse",
    "EmbeddingResponse",
    # Providers
    "OpenAIProvider",
    "OpenAIConfig",
    # OpenAI Interfaces
    "OpenAIEmbeddingsInterface",
    "OpenAIEmbeddingsError",
    "OpenAIModelsInterface",
    "OpenAIModelsError",
    "ModelInfo",
    "OpenAIBatchInterface",
    "OpenAIBatchError",
    "OpenAIResponsesInterface",
    "AsyncOpenAIResponsesInterface",
    "OpenAIResponsesError",
    "StructuredResponse",
]


# Version info
def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__
