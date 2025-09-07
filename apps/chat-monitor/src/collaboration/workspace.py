"""
Workspace Tracker

Monitors shared workspace coordination, file access patterns, and potential
conflicts between agents working on the same resources.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class FileAccess:
    """Represents a file access event."""

    session_id: str
    file_path: str
    access_type: str  # Read, Write, Edit, MultiEdit
    timestamp: float
    content_hash: Optional[str] = None  # For conflict detection
    line_ranges: List[Tuple[int, int]] = field(
        default_factory=list
    )  # For Edit operations


@dataclass
class WorkspaceConflict:
    """Represents a detected workspace conflict."""

    file_path: str
    primary_session: str
    conflicting_session: str
    conflict_type: str  # write_write, read_write, edit_collision
    severity: str  # low, medium, high, critical
    timestamp: float
    description: str
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class WorkspaceMetrics:
    """Workspace collaboration metrics."""

    total_files_accessed: int = 0
    concurrent_access_count: int = 0
    conflict_count: int = 0
    collaboration_hotspots: List[str] = field(default_factory=list)
    most_active_agents: List[str] = field(default_factory=list)
    conflict_rate: float = 0.0
    collaboration_efficiency: float = 0.0


class WorkspaceTracker:
    """
    Tracks shared workspace coordination and detects collaboration patterns
    and conflicts between agents working on the same files.
    """

    def __init__(self, settings):
        self.settings = settings

        # File access tracking
        self.file_access_history: deque = deque(maxlen=settings.workspace_history_size)
        self.active_file_sessions: Dict[str, Set[str]] = defaultdict(
            set
        )  # file -> sessions
        self.session_files: Dict[str, Set[str]] = defaultdict(set)  # session -> files

        # Conflict detection
        self.detected_conflicts: List[WorkspaceConflict] = []
        self.conflict_patterns: Dict[str, int] = defaultdict(int)

        # Collaboration metrics
        self.collaboration_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "files_accessed": set(),
                "write_operations": 0,
                "read_operations": 0,
                "last_access": 0.0,
                "collaboration_score": 0.0,
            }
        )

    async def process_entry(self, session_id: str, entry: Dict):
        """Process a log entry for workspace-related activity."""
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return

        timestamp = self._parse_timestamp(entry.get("timestamp", ""))

        for item in content:
            if isinstance(item, dict) and "name" in item:
                await self._process_file_operation(session_id, item, timestamp)

    async def _process_file_operation(
        self, session_id: str, tool_item: Dict, timestamp: float
    ):
        """Process file operation tools for workspace tracking."""
        tool_name = tool_item["name"]
        tool_input = tool_item.get("input", {})

        if tool_name not in ["Read", "Write", "Edit", "MultiEdit"]:
            return

        # Extract file access information
        file_accesses = await self._extract_file_accesses(
            tool_name, tool_input, session_id, timestamp
        )

        for file_access in file_accesses:
            await self._record_file_access(file_access)
            await self._check_for_conflicts(file_access)
            await self._update_collaboration_stats(file_access)

    async def _extract_file_accesses(
        self, tool_name: str, tool_input: Dict, session_id: str, timestamp: float
    ) -> List[FileAccess]:
        """Extract file access events from tool input."""
        accesses = []

        if tool_name in ["Read", "Write", "Edit"]:
            file_path = tool_input.get("file_path")
            if file_path:
                access = FileAccess(
                    session_id=session_id,
                    file_path=file_path,
                    access_type=tool_name,
                    timestamp=timestamp,
                )

                # For Edit operations, try to extract line information
                if tool_name == "Edit":
                    old_string = tool_input.get("old_string", "")
                    if old_string:
                        # Estimate line ranges (simplified)
                        line_count = len(old_string.split("\n"))
                        access.line_ranges = [(1, line_count)]  # Simplified

                accesses.append(access)

        elif tool_name == "MultiEdit":
            edits = tool_input.get("edits", [])
            for edit in edits:
                if isinstance(edit, dict) and "file_path" in edit:
                    file_path = edit["file_path"]
                    access = FileAccess(
                        session_id=session_id,
                        file_path=file_path,
                        access_type="MultiEdit",
                        timestamp=timestamp,
                    )
                    accesses.append(access)

        return accesses

    async def _record_file_access(self, file_access: FileAccess):
        """Record a file access event."""
        self.file_access_history.append(file_access)

        # Track active sessions per file
        self.active_file_sessions[file_access.file_path].add(file_access.session_id)
        self.session_files[file_access.session_id].add(file_access.file_path)

        # Clean up old active sessions
        await self._cleanup_stale_sessions(file_access.timestamp)

    async def _cleanup_stale_sessions(self, current_time: float):
        """Clean up stale session tracking."""
        stale_threshold = current_time - 300.0  # 5 minutes

        # Remove sessions that haven't been active recently
        for file_path, sessions in list(self.active_file_sessions.items()):
            active_sessions = set()

            for session_id in sessions:
                # Check if session has recent activity on this file
                has_recent_activity = any(
                    access.session_id == session_id
                    and access.file_path == file_path
                    and access.timestamp > stale_threshold
                    for access in self.file_access_history
                )

                if has_recent_activity:
                    active_sessions.add(session_id)
                else:
                    # Remove from session files tracking too
                    self.session_files[session_id].discard(file_path)

            if active_sessions:
                self.active_file_sessions[file_path] = active_sessions
            else:
                del self.active_file_sessions[file_path]

    async def _check_for_conflicts(self, file_access: FileAccess):
        """Check for potential workspace conflicts."""
        current_sessions = self.active_file_sessions[file_access.file_path]

        if len(current_sessions) <= 1:
            return  # No conflict possible with single session

        # Look for recent conflicting accesses
        conflict_window = self.settings.workspace_conflict_threshold

        for other_access in reversed(self.file_access_history):
            if (
                other_access.file_path == file_access.file_path
                and other_access.session_id != file_access.session_id
                and file_access.timestamp - other_access.timestamp <= conflict_window
            ):
                conflict = await self._analyze_potential_conflict(
                    file_access, other_access
                )
                if conflict:
                    self.detected_conflicts.append(conflict)
                    self.conflict_patterns[conflict.conflict_type] += 1

                    # Log high-severity conflicts (rate-limited)
                    if conflict.severity in ["high", "critical"]:
                        # Rate limit: max 1 message per file per 5 seconds
                        current_time = datetime.now().timestamp()
                        rate_limit_key = f"conflict_{conflict.file_path}"

                        if not hasattr(self, "_last_conflict_warnings"):
                            self._last_conflict_warnings = {}

                        last_warning = self._last_conflict_warnings.get(
                            rate_limit_key, 0
                        )
                        if current_time - last_warning > 5.0:  # 5 second cooldown
                            self._last_conflict_warnings[rate_limit_key] = current_time
                            print(
                                f"⚠️  Workspace conflict detected: {conflict.description}"
                            )

    async def _analyze_potential_conflict(
        self, access1: FileAccess, access2: FileAccess
    ) -> Optional[WorkspaceConflict]:
        """Analyze two file accesses for potential conflicts."""
        write_ops = {"Write", "Edit", "MultiEdit"}

        # Determine conflict type
        conflict_type = None
        severity = "low"
        description = ""
        resolution_suggestions = []

        if access1.access_type in write_ops and access2.access_type in write_ops:
            conflict_type = "write_write"
            severity = "high"
            description = (
                f"Multiple agents writing to {access1.file_path} simultaneously"
            )
            resolution_suggestions = [
                "Coordinate write operations between agents",
                "Implement file locking mechanism",
                "Use different sections of the file",
            ]

        elif (access1.access_type in write_ops and access2.access_type == "Read") or (
            access2.access_type in write_ops and access1.access_type == "Read"
        ):
            conflict_type = "read_write"
            severity = "medium"
            description = f"Agent reading {access1.file_path} while another is writing"
            resolution_suggestions = [
                "Read before write operations",
                "Implement read-write coordination",
            ]

        elif (
            access1.access_type == "Edit"
            and access2.access_type == "Edit"
            and self._check_line_overlap(access1, access2)
        ):
            conflict_type = "edit_collision"
            severity = "critical"
            description = f"Overlapping edit operations on {access1.file_path}"
            resolution_suggestions = [
                "Coordinate edit regions",
                "Use MultiEdit for batch operations",
                "Sequence edit operations",
            ]

        if conflict_type:
            return WorkspaceConflict(
                file_path=access1.file_path,
                primary_session=access1.session_id,
                conflicting_session=access2.session_id,
                conflict_type=conflict_type,
                severity=severity,
                timestamp=access1.timestamp,
                description=description,
                resolution_suggestions=resolution_suggestions,
            )

        return None

    def _check_line_overlap(self, access1: FileAccess, access2: FileAccess) -> bool:
        """Check if two edit accesses have overlapping line ranges."""
        if not access1.line_ranges or not access2.line_ranges:
            return True  # Assume overlap if ranges unknown

        for start1, end1 in access1.line_ranges:
            for start2, end2 in access2.line_ranges:
                if not (end1 < start2 or end2 < start1):
                    return True  # Ranges overlap

        return False

    async def _update_collaboration_stats(self, file_access: FileAccess):
        """Update collaboration statistics for an agent."""
        stats = self.collaboration_stats[file_access.session_id]

        stats["files_accessed"].add(file_access.file_path)
        stats["last_access"] = file_access.timestamp

        if file_access.access_type in ["Write", "Edit", "MultiEdit"]:
            stats["write_operations"] += 1
        else:
            stats["read_operations"] += 1

        # Calculate collaboration score based on shared file access
        collaboration_score = 0.0
        for other_session, other_stats in self.collaboration_stats.items():
            if other_session != file_access.session_id:
                shared_files = stats["files_accessed"] & other_stats["files_accessed"]
                if shared_files:
                    collaboration_score += len(shared_files) * 0.1

        stats["collaboration_score"] = min(collaboration_score, 1.0)

    async def update_analysis(self, active_sessions: Dict):
        """Update workspace analysis with current session data."""
        # Clean up old data for inactive sessions
        current_time = time.time()
        inactive_threshold = current_time - 600.0  # 10 minutes

        for session_id in list(self.collaboration_stats.keys()):
            if (
                session_id not in active_sessions
                or self.collaboration_stats[session_id]["last_access"]
                < inactive_threshold
            ):
                # Clean up tracking for inactive session
                files_to_clean = self.session_files[session_id].copy()
                for file_path in files_to_clean:
                    self.active_file_sessions[file_path].discard(session_id)
                    if not self.active_file_sessions[file_path]:
                        del self.active_file_sessions[file_path]

                del self.session_files[session_id]
                # Keep collaboration stats for historical analysis

    async def get_current_status(self) -> WorkspaceMetrics:
        """Get current workspace collaboration status."""
        metrics = WorkspaceMetrics()

        # Count total files accessed
        all_files = set()
        for files in self.session_files.values():
            all_files.update(files)
        metrics.total_files_accessed = len(all_files)

        # Count concurrent access
        metrics.concurrent_access_count = sum(
            1 for sessions in self.active_file_sessions.values() if len(sessions) > 1
        )

        # Count recent conflicts
        current_time = time.time()
        recent_conflicts = [
            conflict
            for conflict in self.detected_conflicts
            if current_time - conflict.timestamp <= 300.0  # 5 minutes
        ]
        metrics.conflict_count = len(recent_conflicts)

        # Find collaboration hotspots (most accessed files)
        file_access_counts = defaultdict(int)
        for file_path, sessions in self.active_file_sessions.items():
            file_access_counts[file_path] = len(sessions)

        hotspots = sorted(file_access_counts.items(), key=lambda x: x[1], reverse=True)
        metrics.collaboration_hotspots = [
            file_path for file_path, count in hotspots[:5]
        ]

        # Find most active agents
        active_agents = sorted(
            self.collaboration_stats.items(),
            key=lambda x: len(x[1]["files_accessed"]),
            reverse=True,
        )
        metrics.most_active_agents = [
            session_id for session_id, stats in active_agents[:5]
        ]

        # Calculate conflict rate
        if metrics.total_files_accessed > 0:
            metrics.conflict_rate = (
                metrics.conflict_count / metrics.total_files_accessed
            )

        # Calculate collaboration efficiency
        total_file_accesses = len(self.file_access_history)
        if total_file_accesses > 0:
            collaborative_accesses = sum(
                1 for _ in self.active_file_sessions.values() if len(_) > 1
            )
            metrics.collaboration_efficiency = collaborative_accesses / len(
                self.active_file_sessions
            )

        return metrics

    def get_file_status(self, file_path: str) -> Dict[str, Any]:
        """Get detailed status for a specific file."""
        status = {
            "active_sessions": list(self.active_file_sessions.get(file_path, set())),
            "recent_accesses": [],
            "conflicts": [],
            "collaboration_level": "none",
        }

        # Get recent accesses for this file
        current_time = time.time()
        recent_window = 300.0  # 5 minutes

        for access in reversed(self.file_access_history):
            if (
                access.file_path == file_path
                and current_time - access.timestamp <= recent_window
            ):
                status["recent_accesses"].append(
                    {
                        "session_id": access.session_id,
                        "access_type": access.access_type,
                        "timestamp": access.timestamp,
                    }
                )

        # Get conflicts for this file
        for conflict in self.detected_conflicts:
            if (
                conflict.file_path == file_path
                and current_time - conflict.timestamp <= recent_window
            ):
                status["conflicts"].append(
                    {
                        "conflict_type": conflict.conflict_type,
                        "severity": conflict.severity,
                        "description": conflict.description,
                        "sessions": [
                            conflict.primary_session,
                            conflict.conflicting_session,
                        ],
                    }
                )

        # Determine collaboration level
        active_count = len(status["active_sessions"])
        if active_count >= 3:
            status["collaboration_level"] = "high"
        elif active_count == 2:
            status["collaboration_level"] = "medium"
        elif active_count == 1:
            status["collaboration_level"] = "low"

        return status

    def get_session_workspace_summary(self, session_id: str) -> Dict[str, Any]:
        """Get workspace summary for a specific session."""
        stats = self.collaboration_stats[session_id]

        return {
            "files_accessed": list(stats["files_accessed"]),
            "file_count": len(stats["files_accessed"]),
            "write_operations": stats["write_operations"],
            "read_operations": stats["read_operations"],
            "collaboration_score": stats["collaboration_score"],
            "last_access": stats["last_access"],
            "shared_files": [
                file_path
                for file_path in stats["files_accessed"]
                if len(self.active_file_sessions.get(file_path, set())) > 1
            ],
        }

    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to float."""
        if not timestamp_str:
            return time.time()

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError):
            return time.time()
