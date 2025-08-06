"""
LLM request schemas.

Defines Pydantic models for LLM API requests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .responses import ChatMessage, FunctionDefinition


class CompletionRequest(BaseModel):
    """Text completion request."""
    prompt: str = Field(..., description="Input prompt")
    model: Optional[str] = Field(default=None, description="Model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="Stop sequences")
    user: Optional[str] = Field(default=None, description="User identifier")

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()


class ChatRequest(BaseModel):
    """Chat completion request."""
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(default=None, description="Model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="Stop sequences")
    user: Optional[str] = Field(default=None, description="User identifier")

    # Function calling
    functions: Optional[List[FunctionDefinition]] = Field(default=None, description="Available functions")
    function_call: Optional[Union[str, Dict[str, str]]] = Field(default=None, description="Function call preference")

    # Streaming
    stream: bool = Field(default=False, description="Enable streaming")

    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('Messages cannot be empty')
        return v

    @validator('function_call')
    def validate_function_call(cls, v, values):
        if v is not None and not values.get('functions'):
            raise ValueError('function_call requires functions to be specified')
        return v


class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    input: Union[str, List[str]] = Field(..., description="Text to embed")
    model: Optional[str] = Field(default=None, description="Embedding model to use")
    user: Optional[str] = Field(default=None, description="User identifier")

    @validator('input')
    def validate_input(cls, v):
        if isinstance(v, str):
            if not v.strip():
                raise ValueError('Input text cannot be empty')
            return v.strip()
        elif isinstance(v, list):
            if not v:
                raise ValueError('Input list cannot be empty')
            for i, text in enumerate(v):
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f'Input at index {i} must be non-empty string')
            return [text.strip() for text in v]
        else:
            raise ValueError('Input must be string or list of strings')


class ModerationRequest(BaseModel):
    """Content moderation request."""
    input: Union[str, List[str]] = Field(..., description="Content to moderate")
    model: Optional[str] = Field(default=None, description="Moderation model to use")

    @validator('input')
    def validate_input(cls, v):
        if isinstance(v, str):
            if not v.strip():
                raise ValueError('Input text cannot be empty')
            return v.strip()
        elif isinstance(v, list):
            if not v:
                raise ValueError('Input list cannot be empty')
            for i, text in enumerate(v):
                if not isinstance(text, str):
                    raise ValueError(f'Input at index {i} must be string')
            return v
        else:
            raise ValueError('Input must be string or list of strings')
