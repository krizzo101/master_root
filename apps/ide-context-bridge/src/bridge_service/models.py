"""
Data models for the IDE Context Bridge Service.

Defines Pydantic models for request/response validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator


# Core context models
class CursorPosition(BaseModel):
    """Represents cursor position in editor."""

    line: int = Field(..., ge=0, description="Line number (0-indexed)")
    column: int = Field(..., ge=0, description="Column number (0-indexed)")
    offset: Optional[int] = Field(
        None, ge=0, description="Character offset from file start"
    )


class TextSelection(BaseModel):
    """Represents selected text in editor."""

    start: CursorPosition = Field(..., description="Selection start position")
    end: CursorPosition = Field(..., description="Selection end position")
    text: str = Field(..., description="Selected text content")


class ActiveFile(BaseModel):
    """Represents the currently active file in editor."""

    path: str = Field(..., description="Absolute file path")
    language: str = Field(..., description="Programming language identifier")
    content: Optional[str] = Field(
        None, description="File content (optional for large files)"
    )
    modified: bool = Field(False, description="Whether file has unsaved changes")
    line_count: int = Field(..., ge=0, description="Total number of lines")


class OpenFile(BaseModel):
    """Represents an open file in editor."""

    path: str = Field(..., description="Absolute file path")
    language: str = Field(..., description="Programming language identifier")
    modified: bool = Field(False, description="Whether file has unsaved changes")


class WorkspaceInfo(BaseModel):
    """Represents workspace/project information."""

    root_path: str = Field(..., description="Workspace root directory")
    folders: List[str] = Field(default_factory=list, description="Workspace folders")
    active_project: Optional[str] = Field(None, description="Active project name")


class GitInfo(BaseModel):
    """Represents Git repository information."""

    branch: str = Field(..., description="Current Git branch")
    repository: str = Field(..., description="Repository name/URL")
    uncommitted_changes: int = Field(
        0, ge=0, description="Number of uncommitted changes"
    )


class Diagnostic(BaseModel):
    """Represents a diagnostic message (error, warning, etc.)."""

    file_path: str = Field(..., description="File path where diagnostic occurs")
    severity: Literal["error", "warning", "info", "hint"] = Field(
        ..., description="Diagnostic severity"
    )
    line: int = Field(..., ge=0, description="Line number (0-indexed)")
    column: int = Field(..., ge=0, description="Column number (0-indexed)")
    message: str = Field(..., description="Diagnostic message")
    source: str = Field(
        ..., description="Source of diagnostic (e.g., 'typescript', 'pylint')"
    )


class QueryFilters(BaseModel):
    """Filters for search queries."""

    source_types: Optional[List[str]] = Field(
        None, description="Filter by source types"
    )
    entity_types: Optional[List[str]] = Field(
        None, description="Filter by entity types"
    )
    file_patterns: Optional[List[str]] = Field(
        None, description="Filter by file patterns"
    )
    languages: Optional[List[str]] = Field(
        None, description="Filter by programming languages"
    )


class QueryRequest(BaseModel):
    """Represents a search query."""

    text: str = Field(..., description="Search query text")
    type: Literal["semantic", "code", "hybrid", "chat_history"] = Field(
        ..., description="Search type"
    )
    filters: Optional[QueryFilters] = Field(None, description="Search filters")


# Main message types
class IDEContextMessage(BaseModel):
    """Main message format for IDE context updates."""

    type: Literal["context_update", "query_request", "suggestion_request"] = Field(
        ..., description="Message type"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp"
    )
    session_id: str = Field(..., description="Unique session identifier")
    editor_id: str = Field(..., description="Unique editor instance identifier")

    # Context data
    active_file: Optional[ActiveFile] = Field(None, description="Currently active file")
    cursor_position: Optional[CursorPosition] = Field(
        None, description="Current cursor position"
    )
    selection: Optional[TextSelection] = Field(
        None, description="Current text selection"
    )

    # Environment context
    workspace: Optional[WorkspaceInfo] = Field(
        None, description="Workspace information"
    )
    open_files: List[OpenFile] = Field(
        default_factory=list, description="List of open files"
    )

    # Git context
    git_info: Optional[GitInfo] = Field(None, description="Git repository information")

    # Diagnostics
    diagnostics: List[Diagnostic] = Field(
        default_factory=list, description="Current diagnostics"
    )

    # Query context (for search requests)
    query: Optional[QueryRequest] = Field(
        None, description="Search query (if applicable)"
    )


# Response models
class Suggestion(BaseModel):
    """Represents a code suggestion."""

    type: Literal["completion", "refactor", "fix", "documentation"] = Field(
        ..., description="Suggestion type"
    )
    priority: int = Field(
        ..., ge=1, le=10, description="Priority (1-10, higher is more important)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Suggestion description")
    code_snippet: Optional[str] = Field(
        None, description="Code snippet to insert/replace"
    )
    file_path: Optional[str] = Field(None, description="Target file path")
    line_range: Optional[List[int]] = Field(
        None, description="Target line range [start, end]"
    )
    source_context_id: Optional[str] = Field(
        None, description="Reference to source context item"
    )

    @validator("line_range")
    def validate_line_range(cls, v):
        if v is not None and len(v) != 2:
            raise ValueError("line_range must contain exactly 2 elements [start, end]")
        return v


class SearchResult(BaseModel):
    """Represents a search result."""

    id: str = Field(..., description="Result identifier")
    source_type: str = Field(
        ..., description="Source type (e.g., 'chat', 'code', 'git')"
    )
    entity_type: str = Field(
        ..., description="Entity type (e.g., 'function', 'message')"
    )
    title: str = Field(..., description="Result title")
    content: str = Field(..., description="Result content")
    file_path: Optional[str] = Field(None, description="Associated file path")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ChatContext(BaseModel):
    """Represents chat history context."""

    id: str = Field(..., description="Chat message/session identifier")
    session_id: str = Field(..., description="Chat session identifier")
    message_type: Literal["user", "assistant"] = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    file_references: List[str] = Field(
        default_factory=list, description="Referenced file paths"
    )


class ResponseMetrics(BaseModel):
    """Performance metrics for responses."""

    response_time_ms: int = Field(
        ..., ge=0, description="Total response time in milliseconds"
    )
    search_time_ms: Optional[int] = Field(
        None, ge=0, description="Search time in milliseconds"
    )
    embedding_time_ms: Optional[int] = Field(
        None, ge=0, description="Embedding generation time"
    )
    cache_hit: bool = Field(False, description="Whether result was served from cache")


class ResponseData(BaseModel):
    """Response data payload."""

    # Suggestions
    suggestions: Optional[List[Suggestion]] = Field(
        None, description="Code suggestions"
    )

    # Search results
    search_results: Optional[List[SearchResult]] = Field(
        None, description="Search results"
    )

    # Chat context
    chat_context: Optional[List[ChatContext]] = Field(
        None, description="Related chat history"
    )

    # Performance metrics
    metrics: Optional[ResponseMetrics] = Field(None, description="Performance metrics")

    # Generic data
    status: Optional[str] = Field(None, description="Status message")
    result_count: Optional[int] = Field(None, ge=0, description="Number of results")


class ErrorDetails(BaseModel):
    """Error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class BridgeResponse(BaseModel):
    """Main response format from bridge service."""

    type: Literal["context_ack", "suggestions", "search_results", "error"] = Field(
        ..., description="Response type"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
    request_id: Optional[str] = Field(None, description="Request identifier")
    session_id: str = Field(..., description="Session identifier")

    # Success response
    data: Optional[ResponseData] = Field(None, description="Response data")

    # Error response
    error: Optional[ErrorDetails] = Field(None, description="Error information")


# Request models for HTTP endpoints
class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    type: Literal["semantic", "code", "hybrid", "chat_history"] = Field(
        "hybrid", description="Search type"
    )
    filters: Optional[QueryFilters] = Field(None, description="Search filters")
    max_results: Optional[int] = Field(
        10, ge=1, le=100, description="Maximum number of results"
    )
    request_id: Optional[str] = Field(None, description="Request identifier")
    session_id: str = Field(..., description="Session identifier")


class SuggestionRequest(BaseModel):
    """Suggestion request model."""

    session_id: str = Field(..., description="Session identifier")
    file_path: str = Field(..., description="Current file path")
    cursor_position: CursorPosition = Field(..., description="Current cursor position")
    context: Optional[str] = Field(None, description="Additional context")
    types: List[Literal["completion", "refactor", "fix", "documentation"]] = Field(
        default=["completion"], description="Types of suggestions to generate"
    )
    request_id: Optional[str] = Field(None, description="Request identifier")


# Health and status models
class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Service status"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Check timestamp"
    )
    version: str = Field(..., description="Service version")
    active_connections: int = Field(
        ..., ge=0, description="Number of active WebSocket connections"
    )
    active_sessions: int = Field(..., ge=0, description="Number of active sessions")


# WebSocket message types
class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp"
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")


class ConnectionRegistration(BaseModel):
    """WebSocket connection registration."""

    session_id: str = Field(..., description="Session identifier")
    editor_id: str = Field(..., description="Editor identifier")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    subscriptions: List[str] = Field(
        default_factory=list, description="Event types to subscribe to"
    )
