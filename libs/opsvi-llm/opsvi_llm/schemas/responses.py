"""
LLM response schemas.

Defines Pydantic models for LLM API responses and related data structures.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatMessage(BaseModel):
    """Chat message with role and content."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Message name (for function messages)")

    @validator('content')
    def validate_content(cls, v):
        if v is None:
            return ""
        return str(v)


class FunctionParameter(BaseModel):
    """Function parameter definition."""
    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(default=None, description="Parameter description")
    enum: Optional[List[str]] = Field(default=None, description="Allowed values for enum types")
    items: Optional[Dict[str, Any]] = Field(default=None, description="Array item schema")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Object properties")
    required: Optional[List[str]] = Field(default=None, description="Required properties")


class FunctionDefinition(BaseModel):
    """Function definition for function calling."""
    name: str = Field(..., description="Function name")
    description: Optional[str] = Field(default=None, description="Function description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Function parameters schema")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Function name cannot be empty')
        # Function names must be valid identifiers
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Function name must contain only alphanumeric characters, hyphens, and underscores')
        return v.strip()


class FunctionCall(BaseModel):
    """Function call from LLM."""
    name: str = Field(..., description="Function name")
    arguments: str = Field(..., description="Function arguments as JSON string")

    @validator('arguments')
    def validate_arguments(cls, v):
        if not v:
            return "{}"
        try:
            # Validate that arguments is valid JSON
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f'Arguments must be valid JSON: {e}')

    def get_arguments(self) -> Dict[str, Any]:
        """Parse arguments as dictionary.

        Returns:
            Parsed arguments dictionary
        """
        return json.loads(self.arguments)


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int = Field(..., description="Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")


class LLMResponse(BaseModel):
    """LLM response with generated content and metadata."""
    generated_text: str = Field(default="", description="Generated text content")
    messages: List[ChatMessage] = Field(default_factory=list, description="Response messages")
    function_calls: List[FunctionCall] = Field(default_factory=list, description="Function calls made")
    model: str = Field(..., description="Model used for generation")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage information")
    finish_reason: Optional[str] = Field(default=None, description="Reason generation finished")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def has_function_calls(self) -> bool:
        """Check if response contains function calls.

        Returns:
            True if response has function calls
        """
        return len(self.function_calls) > 0

    def get_content(self) -> str:
        """Get the main content from the response.

        Returns:
            Generated text or content from first message
        """
        if self.generated_text:
            return self.generated_text

        if self.messages:
            return self.messages[0].content

        return ""

    def get_total_tokens(self) -> int:
        """Get total tokens used.

        Returns:
            Total token count, 0 if not available
        """
        return self.usage.get('total_tokens', 0)


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    content: str = Field(default="", description="Content chunk")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason if stream ended")
    function_call: Optional[FunctionCall] = Field(default=None, description="Function call chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")

    def is_final(self) -> bool:
        """Check if this is the final chunk.

        Returns:
            True if this is the final chunk
        """
        return self.finish_reason is not None


class EmbeddingVector(BaseModel):
    """Embedding vector with metadata."""
    embedding: List[float] = Field(..., description="Embedding vector")
    index: int = Field(..., description="Input index")
    object: str = Field(default="embedding", description="Object type")


class EmbeddingResponse(BaseModel):
    """Embedding generation response."""
    data: List[EmbeddingVector] = Field(..., description="Embedding vectors")
    model: str = Field(..., description="Model used")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_embeddings(self) -> List[List[float]]:
        """Get embedding vectors as list.

        Returns:
            List of embedding vectors
        """
        return [item.embedding for item in self.data]


class ModerationCategory(BaseModel):
    """Moderation category result."""
    flagged: bool = Field(..., description="Whether content was flagged")
    score: float = Field(..., description="Confidence score")


class ModerationResult(BaseModel):
    """Content moderation result."""
    flagged: bool = Field(..., description="Whether any category was flagged")
    categories: Dict[str, bool] = Field(..., description="Category flags")
    category_scores: Dict[str, float] = Field(..., description="Category confidence scores")


class ModerationResponse(BaseModel):
    """Content moderation response."""
    id: str = Field(..., description="Response ID")
    model: str = Field(..., description="Model used")
    results: List[ModerationResult] = Field(..., description="Moderation results")

    def is_flagged(self) -> bool:
        """Check if any content was flagged.

        Returns:
            True if any content was flagged
        """
        return any(result.flagged for result in self.results)
