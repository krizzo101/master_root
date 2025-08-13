"""
Data models for Context Bridge

Defines the structure of context data shared between IDE and agents.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DiagnosticSeverity(str, Enum):
    """Diagnostic severity levels matching VS Code/LSP protocol"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class DiagnosticInfo(BaseModel):
    """Represents a diagnostic message from the IDE"""

    file_path: str
    line: int
    column: int
    severity: DiagnosticSeverity
    message: str
    source: Optional[str] = None
    code: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FileSelection(BaseModel):
    """Represents selected text in a file"""

    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    selected_text: str


class IDEContext(BaseModel):
    """Complete IDE context snapshot"""

    active_file: Optional[str] = None
    selection: Optional[FileSelection] = None
    open_tabs: List[str] = Field(default_factory=list)
    diagnostics: List[DiagnosticInfo] = Field(default_factory=list)
    project_root: str
    cursor_position: Optional[Dict[str, int]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def get_relevant_diagnostics(
        self, file_path: Optional[str] = None
    ) -> List[DiagnosticInfo]:
        """Get diagnostics for a specific file or current active file"""
        target_file = file_path or self.active_file
        if not target_file:
            return []
        return [d for d in self.diagnostics if d.file_path == target_file]


class ContextEventType(str, Enum):
    """Types of context events"""

    FILE_OPENED = "file_opened"
    FILE_CLOSED = "file_closed"
    FILE_CHANGED = "file_changed"
    SELECTION_CHANGED = "selection_changed"
    DIAGNOSTICS_UPDATED = "diagnostics_updated"
    CURSOR_MOVED = "cursor_moved"
    CONTEXT_SYNC = "context_sync"  # Full context refresh


class ContextEvent(BaseModel):
    """Event representing a context change"""

    event_type: ContextEventType
    event_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "ide"  # Could be 'ide', 'agent', 'manual'

    def to_redis_message(self) -> str:
        """Convert to Redis pub/sub message format"""
        return self.json()

    @classmethod
    def from_redis_message(cls, message: str) -> "ContextEvent":
        """Parse from Redis pub/sub message"""
        return cls.parse_raw(message)


class ContextQuery(BaseModel):
    """Query for context information"""

    include_diagnostics: bool = True
    include_selection: bool = True
    include_open_tabs: bool = True
    file_filter: Optional[List[str]] = None  # Filter to specific files
    diagnostic_severity_filter: Optional[List[DiagnosticSeverity]] = None


class ContextSubscription(BaseModel):
    """Subscription request for context updates"""

    subscriber_id: str
    event_types: List[ContextEventType]
    file_patterns: Optional[List[str]] = None  # Glob patterns for file filtering
    callback_url: Optional[str] = None  # For webhook-style callbacks
