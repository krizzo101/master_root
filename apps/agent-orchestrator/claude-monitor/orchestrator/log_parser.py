"""
Claude Monitor Log Parser

Handles chat log parsing, session ID tracking, and rolling buffer management
for the Claude monitoring system.
"""

import json
import re
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LogEntry:
    """Represents a single log entry"""

    timestamp: datetime
    session_id: str
    message_type: str  # 'user', 'assistant', 'system', 'error'
    content: str
    raw_line: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "raw_line": self.raw_line,
            "metadata": self.metadata or {},
        }


class RollingBuffer:
    """Manages a rolling buffer of log entries with configurable size"""

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self._session_buffers: Dict[str, deque] = {}

    def add(self, entry: LogEntry):
        """Add entry to main buffer and session-specific buffer"""
        self.buffer.append(entry)

        # Maintain per-session buffers
        if entry.session_id not in self._session_buffers:
            self._session_buffers[entry.session_id] = deque(maxlen=self.max_size)
        self._session_buffers[entry.session_id].append(entry)

    def get_recent(self, count: Optional[int] = None) -> List[LogEntry]:
        """Get recent entries from main buffer"""
        if count is None:
            return list(self.buffer)
        return list(self.buffer)[-count:]

    def get_session_recent(
        self, session_id: str, count: Optional[int] = None
    ) -> List[LogEntry]:
        """Get recent entries for specific session"""
        if session_id not in self._session_buffers:
            return []

        session_buffer = self._session_buffers[session_id]
        if count is None:
            return list(session_buffer)
        return list(session_buffer)[-count:]

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self._session_buffers.keys())

    def clear_session(self, session_id: str):
        """Clear buffer for specific session"""
        if session_id in self._session_buffers:
            del self._session_buffers[session_id]


class LogParser:
    """Main log parser class for Claude chat logs"""

    # Common patterns for different log formats
    PATTERNS = {
        "timestamp": r"(\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "session_marker": r"session[_\-]?id[:\s=]([a-f0-9\-]{8,36})",
        "user_message": r"(?:user|human)[:>\s]+(.*)",
        "assistant_message": r"(?:assistant|claude|ai)[:>\s]+(.*)",
        "system_message": r"(?:system|debug)[:>\s]+(.*)",
        "error_message": r"(?:error|exception|traceback)[:>\s]+(.*)",
        "tool_call": r"tool[_\s]call[:>\s]+(.*)",
        "function_call": r"function[_\s]call[:>\s]+(.*)",
    }

    def __init__(self, buffer_size: int = 20):
        self.buffer = RollingBuffer(buffer_size)
        self._current_session = None
        self._session_counter = 0

    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        match = re.search(self.PATTERNS["timestamp"], line)
        if match:
            try:
                timestamp_str = match.group(1)
                # Try common formats
                for fmt in [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                ]:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        return datetime.now()

    def _extract_session_id(self, line: str) -> Optional[str]:
        """Extract session ID from log line"""
        match = re.search(self.PATTERNS["session_marker"], line, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _determine_message_type(self, line: str) -> Tuple[str, str]:
        """Determine message type and extract content"""
        line_lower = line.lower()

        # Check for different message types
        for pattern_name, pattern in self.PATTERNS.items():
            if pattern_name.endswith("_message") or pattern_name.endswith("_call"):
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    message_type = pattern_name.replace("_message", "").replace(
                        "_call", ""
                    )
                    content = match.group(1).strip()
                    return message_type, content

        # Default classification based on keywords
        if any(
            keyword in line_lower
            for keyword in ["error", "exception", "traceback", "failed"]
        ):
            return "error", line.strip()
        elif (
            any(keyword in line_lower for keyword in ["user", "human"]) and ":" in line
        ):
            return "user", line.split(":", 1)[1].strip()
        elif (
            any(keyword in line_lower for keyword in ["assistant", "claude", "ai"])
            and ":" in line
        ):
            return "assistant", line.split(":", 1)[1].strip()
        elif (
            any(keyword in line_lower for keyword in ["system", "debug"])
            and ":" in line
        ):
            return "system", line.split(":", 1)[1].strip()
        else:
            return "unknown", line.strip()

    def _get_or_create_session_id(self, line: str) -> str:
        """Get session ID from line or create new one"""
        session_id = self._extract_session_id(line)

        if session_id:
            self._current_session = session_id
            return session_id

        # If no session ID found, use current or create new
        if not self._current_session:
            self._session_counter += 1
            self._current_session = (
                f"session-{self._session_counter:04d}-{uuid.uuid4().hex[:8]}"
            )

        return self._current_session

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line"""
        if not line.strip():
            return None

        timestamp = self._extract_timestamp(line)
        session_id = self._get_or_create_session_id(line)
        message_type, content = self._determine_message_type(line)

        # Extract additional metadata
        metadata = {}
        if "token" in line.lower():
            token_match = re.search(r"(\d+)\s*tokens?", line, re.IGNORECASE)
            if token_match:
                metadata["tokens"] = int(token_match.group(1))

        if "cost" in line.lower():
            cost_match = re.search(r"\$?(\d+\.?\d*)", line)
            if cost_match:
                metadata["cost"] = float(cost_match.group(1))

        entry = LogEntry(
            timestamp=timestamp,
            session_id=session_id,
            message_type=message_type,
            content=content,
            raw_line=line.strip(),
            metadata=metadata,
        )

        self.buffer.add(entry)
        return entry

    def parse_lines(self, lines: List[str]) -> List[LogEntry]:
        """Parse multiple log lines"""
        entries = []
        for line in lines:
            entry = self.parse_line(line)
            if entry:
                entries.append(entry)
        return entries

    def parse_file(self, file_path: str) -> List[LogEntry]:
        """Parse log file"""
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = self.parse_line(line)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            # Create error entry for parsing failure
            error_entry = LogEntry(
                timestamp=datetime.now(),
                session_id=self._get_or_create_session_id(""),
                message_type="error",
                content=f"Failed to parse log file {file_path}: {str(e)}",
                raw_line=f"ERROR: {str(e)}",
                metadata={"file_path": file_path},
            )
            entries.append(error_entry)

        return entries

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session"""
        session_entries = self.buffer.get_session_recent(session_id)

        if not session_entries:
            return {"session_id": session_id, "entry_count": 0}

        message_types = {}
        total_tokens = 0
        total_cost = 0.0

        for entry in session_entries:
            message_types[entry.message_type] = (
                message_types.get(entry.message_type, 0) + 1
            )

            if entry.metadata:
                total_tokens += entry.metadata.get("tokens", 0)
                total_cost += entry.metadata.get("cost", 0.0)

        return {
            "session_id": session_id,
            "entry_count": len(session_entries),
            "message_types": message_types,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "first_entry": session_entries[0].timestamp.isoformat()
            if session_entries
            else None,
            "last_entry": session_entries[-1].timestamp.isoformat()
            if session_entries
            else None,
        }

    def get_recent_entries(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent entries as dictionaries"""
        entries = self.buffer.get_recent(count)
        return [entry.to_dict() for entry in entries]

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return self.buffer.get_active_sessions()

    def start_new_session(self) -> str:
        """Start a new session and return its ID"""
        self._session_counter += 1
        self._current_session = (
            f"session-{self._session_counter:04d}-{uuid.uuid4().hex[:8]}"
        )
        return self._current_session

    def export_session(self, session_id: str, format: str = "json") -> str:
        """Export session data in specified format"""
        session_entries = self.buffer.get_session_recent(session_id)

        if format.lower() == "json":
            return json.dumps([entry.to_dict() for entry in session_entries], indent=2)
        elif format.lower() == "txt":
            lines = []
            for entry in session_entries:
                lines.append(
                    f"[{entry.timestamp}] {entry.message_type}: {entry.content}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
