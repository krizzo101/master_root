"""
Data models for OpenAI Codex MCP Server
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CodexMode(str, Enum):
    """Codex operation modes"""

    COMPLETE = "complete"
    GENERATE = "generate"
    EXPLAIN = "explain"
    REFACTOR = "refactor"
    DEBUG = "debug"
    TEST = "test"
    DOCUMENT = "document"
    REVIEW = "review"
    TRANSLATE = "translate"


class CodexRequest(BaseModel):
    """Request model for Codex operations"""

    prompt: str = Field(description="The prompt or code to process")
    mode: CodexMode = Field(default=CodexMode.GENERATE, description="Operation mode")
    language: Optional[str] = Field(
        default=None, description="Target programming language"
    )
    context_files: Optional[List[str]] = Field(
        default=None, description="Files to include as context"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Override default max tokens"
    )
    temperature: Optional[float] = Field(
        default=None, description="Override default temperature"
    )
    stop_sequences: Optional[List[str]] = Field(
        default=None, description="Custom stop sequences"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class CodexResponse(BaseModel):
    """Response model for Codex operations"""

    success: bool = Field(description="Whether the operation succeeded")
    mode: CodexMode = Field(description="The mode that was used")
    result: Optional[str] = Field(default=None, description="Generated/processed code")
    explanation: Optional[str] = Field(
        default=None, description="Explanation if applicable"
    )
    suggestions: Optional[List[str]] = Field(
        default=None, description="Additional suggestions"
    )
    tokens_used: int = Field(default=0, description="Number of tokens consumed")
    execution_time: float = Field(default=0.0, description="Time taken in seconds")
    cached: bool = Field(default=False, description="Whether result was from cache")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class CodeContext(BaseModel):
    """Context information for code operations"""

    file_path: str = Field(description="Path to the file")
    content: str = Field(description="File content")
    language: str = Field(description="Programming language")
    line_start: Optional[int] = Field(default=None, description="Starting line number")
    line_end: Optional[int] = Field(default=None, description="Ending line number")
    dependencies: Optional[List[str]] = Field(
        default=None, description="File dependencies"
    )


class CodexJob(BaseModel):
    """Job tracking for async Codex operations"""

    job_id: str = Field(description="Unique job identifier")
    status: str = Field(default="pending", description="Job status")
    request: CodexRequest = Field(description="Original request")
    response: Optional[CodexResponse] = Field(
        default=None, description="Response when complete"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Job creation time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion time"
    )
    error: Optional[str] = Field(default=None, description="Error if job failed")
