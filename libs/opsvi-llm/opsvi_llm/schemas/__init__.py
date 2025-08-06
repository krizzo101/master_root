"""
Schemas module for opsvi-llm.

Provides request and response models for LLM APIs.
"""

from .requests import ChatRequest, CompletionRequest, EmbeddingRequest, ModerationRequest
from .responses import (
    LLMResponse,
    ChatMessage,
    MessageRole,
    FunctionCall,
    FunctionDefinition,
    StreamChunk,
    EmbeddingResponse,
    ModerationResponse
)

__all__ = [
    # Requests
    "ChatRequest",
    "CompletionRequest",
    "EmbeddingRequest",
    "ModerationRequest",
    # Responses
    "LLMResponse",
    "ChatMessage",
    "MessageRole",
    "FunctionCall",
    "FunctionDefinition",
    "StreamChunk",
    "EmbeddingResponse",
    "ModerationResponse",
]
