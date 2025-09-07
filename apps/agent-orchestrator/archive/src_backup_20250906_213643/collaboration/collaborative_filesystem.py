#!/usr/bin/env python3
"""
Collaborative File System - Shared file operations with conflict resolution

This module provides the CollaborativeFileSystem class which handles:
- Concurrent file access and editing by multiple agents
- Conflict detection and resolution
- File locking and version management
- Real-time synchronization of file changes
"""

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .change_tracker import ChangeTracker


@dataclass
class FileLock:
    """Represents a file lock held by an agent"""

    file_path: str
    agent_id: str
    lock_type: str  # read, write, exclusive
    acquired_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    operation: str = ""


@dataclass
class FileVersion:
    """File version information"""

    file_path: str
    version: int
    checksum: str
    modified_by: str
    modified_at: datetime = field(default_factory=datetime.now)
    changes_summary: str = ""
    size: int = 0


@dataclass
class ConflictInfo:
    """Information about a file conflict"""

    file_path: str
    base_version: int
    agent1_version: int
    agent2_version: int
    agent1_id: str
    agent2_id: str
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_strategy: str = ""


class CollaborativeFileSystem:
    """
    Manages shared file operations with conflict resolution

    Provides concurrent file access, version control, and conflict
    resolution for multiple agents working on the same files.
    """

    def __init__(
        self, workspace_path: Path, change_tracker: Optional[ChangeTracker] = None
    ):
        self.workspace_path = Path(workspace_path)
        self.locks_path = self.workspace_path / ".locks"
        self.versions_path = self.workspace_path / ".versions"
        self.conflicts_path = self.workspace_path / ".conflicts"

        # Ensure directories exist
        self.locks_path.mkdir(parents=True, exist_ok=True)
        self.versions_path.mkdir(parents=True, exist_ok=True)
        self.conflicts_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.change_tracker = change_tracker

        # In-memory state
        self.file_locks: Dict[str, FileLock] = {}
        self.file_versions: Dict[str, List[FileVersion]] = {}
        self.active_conflicts: Dict[str, ConflictInfo] = {}

        # Locks for thread safety
        self.lock = asyncio.Lock()
        self.file_locks_lock = asyncio.Lock()

        # Load existing state
        self._load_file_state()

    def _load_file_state(self):
        """Load existing file locks, versions, and conflicts"""
        # Load file locks
        for lock_file in self.locks_path.glob("*.json"):
            try:
                lock_data = json.loads(lock_file.read_text())
                lock = FileLock(**lock_data)
                self.file_locks[lock.file_path] = lock
            except Exception as e:
                print(f"Failed to load lock {lock_file}: {e}")

        # Load file versions
        for version_file in self.versions_path.glob("*.json"):
            try:
                versions_data = json.loads(version_file.read_text())
                file_path = version_file.stem
                versions = [FileVersion(**v) for v in versions_data]
                self.file_versions[file_path] = versions
            except Exception as e:
                print(f"Failed to load versions {version_file}: {e}")

        # Load conflicts
        for conflict_file in self.conflicts_path.glob("*.json"):
            try:
                conflict_data = json.loads(conflict_file.read_text())
                conflict = ConflictInfo(**conflict_data)
                self.active_conflicts[conflict.file_path] = conflict
            except Exception as e:
                print(f"Failed to load conflict {conflict_file}: {e}")

    async def acquire_lock(
        self,
        file_path: str,
        agent_id: str,
        lock_type: str = "write",
        timeout: float = 30.0,
        operation: str = "",
    ) -> bool:
        """
        Acquire a lock on a file

        Args:
            file_path: Path to the file
            agent_id: ID of the agent requesting the lock
            lock_type: Type of lock (read, write, exclusive)
            timeout: Timeout in seconds
            operation: Description of the operation

        Returns:
            bool: True if lock acquired successfully
        """
        async with self.file_locks_lock:
            # Check if file is already locked
            existing_lock = self.file_locks.get(file_path)

            if existing_lock:
                # Check if this agent already has the lock
                if existing_lock.agent_id == agent_id:
                    return True

                # Check lock compatibility
                if not self._are_locks_compatible(existing_lock.lock_type, lock_type):
                    return False

            # Create new lock
            lock = FileLock(
                file_path=file_path,
                agent_id=agent_id,
                lock_type=lock_type,
                operation=operation,
                expires_at=datetime.now() + timedelta(seconds=timeout)
                if timeout > 0
                else None,
            )

            # Store lock
            self.file_locks[file_path] = lock
            await self._save_lock(lock)

            return True

    def _are_locks_compatible(self, existing_type: str, requested_type: str) -> bool:
        """Check if two lock types are compatible"""
        # Read locks are compatible with each other
        if existing_type == "read" and requested_type == "read":
            return True

        # All other combinations are incompatible
        return False

    async def release_lock(self, file_path: str, agent_id: str) -> bool:
        """
        Release a lock on a file

        Args:
            file_path: Path to the file
            agent_id: ID of the agent releasing the lock

        Returns:
            bool: True if lock released successfully
        """
        async with self.file_locks_lock:
            existing_lock = self.file_locks.get(file_path)

            if not existing_lock or existing_lock.agent_id != agent_id:
                return False

            # Remove lock
            del self.file_locks[file_path]

            # Remove lock file
            lock_file = self.locks_path / f"{self._safe_filename(file_path)}.json"
            lock_file.unlink(missing_ok=True)

            return True

    async def read_file(
        self, file_path: str, agent_id: str
    ) -> Optional[Tuple[str, int]]:
        """
        Read a file with version information

        Args:
            file_path: Path to the file
            agent_id: ID of the reading agent

        Returns:
            Tuple of (content, version) or None if file doesn't exist
        """
        full_path = self.workspace_path / file_path

        if not full_path.exists():
            return None

        # Acquire read lock
        if not await self.acquire_lock(file_path, agent_id, "read", operation="read"):
            return None

        try:
            content = full_path.read_text(encoding="utf-8")
            version = await self._get_current_version(file_path)

            # Track read operation
            if self.change_tracker:
                await self.change_tracker.track_file_event(
                    file_path, "read", {"agent_id": agent_id, "version": version}
                )

            return content, version

        finally:
            await self.release_lock(file_path, agent_id)

    async def write_file(
        self,
        file_path: str,
        content: str,
        agent_id: str,
        expected_version: Optional[int] = None,
        changes_summary: str = "",
    ) -> Tuple[bool, Optional[str]]:
        """
        Write a file with conflict detection

        Args:
            file_path: Path to the file
            content: File content to write
            agent_id: ID of the writing agent
            expected_version: Expected version number for conflict detection
            changes_summary: Summary of changes made

        Returns:
            Tuple of (success, error_message)
        """
        # Acquire write lock
        if not await self.acquire_lock(file_path, agent_id, "write", operation="write"):
            return False, "Could not acquire write lock"

        try:
            full_path = self.workspace_path / file_path
            current_version = await self._get_current_version(file_path)

            # Check for version conflict
            if expected_version is not None and current_version != expected_version:
                await self._handle_version_conflict(
                    file_path, agent_id, expected_version, current_version
                )
                return (
                    False,
                    f"Version conflict: expected {expected_version}, current {current_version}",
                )

            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            full_path.write_text(content, encoding="utf-8")

            # Create new version
            checksum = self._calculate_checksum(content)
            new_version = FileVersion(
                file_path=file_path,
                version=current_version + 1,
                checksum=checksum,
                modified_by=agent_id,
                changes_summary=changes_summary,
                size=len(content.encode("utf-8")),
            )

            # Store version
            await self._add_file_version(file_path, new_version)

            # Track write operation
            if self.change_tracker:
                await self.change_tracker.track_file_event(
                    file_path,
                    "write",
                    {
                        "agent_id": agent_id,
                        "version": new_version.version,
                        "size": new_version.size,
                        "changes": changes_summary,
                    },
                )

            return True, None

        except Exception as e:
            return False, str(e)

        finally:
            await self.release_lock(file_path, agent_id)

    async def append_to_file(
        self, file_path: str, content: str, agent_id: str, separator: str = "\n"
    ) -> Tuple[bool, Optional[str]]:
        """
        Append content to a file (thread-safe)

        Args:
            file_path: Path to the file
            content: Content to append
            agent_id: ID of the agent
            separator: Separator to use between appends

        Returns:
            Tuple of (success, error_message)
        """
        # Acquire write lock
        if not await self.acquire_lock(
            file_path, agent_id, "write", operation="append"
        ):
            return False, "Could not acquire write lock"

        try:
            full_path = self.workspace_path / file_path

            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing content
            existing_content = ""
            if full_path.exists():
                existing_content = full_path.read_text(encoding="utf-8")

            # Append new content
            new_content = (
                existing_content + separator + content if existing_content else content
            )

            # Write back
            success, error = await self.write_file(
                file_path,
                new_content,
                agent_id,
                changes_summary=f"Appended content by {agent_id}",
            )

            return success, error

        except Exception as e:
            return False, str(e)

        finally:
            await self.release_lock(file_path, agent_id)

    async def list_files(self, directory_path: str = "") -> List[Dict[str, Any]]:
        """
        List files in a directory with metadata

        Args:
            directory_path: Directory path relative to workspace

        Returns:
            List of file information dictionaries
        """
        full_path = self.workspace_path / directory_path

        if not full_path.exists() or not full_path.is_dir():
            return []

        files_info = []

        for item in full_path.iterdir():
            if item.name.startswith("."):  # Skip hidden files
                continue

            rel_path = str(item.relative_to(self.workspace_path))

            file_info = {
                "path": rel_path,
                "name": item.name,
                "is_directory": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
                "modified_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                "version": await self._get_current_version(rel_path)
                if item.is_file()
                else 0,
                "locked": rel_path in self.file_locks,
                "has_conflicts": rel_path in self.active_conflicts,
            }

            files_info.append(file_info)

        return sorted(files_info, key=lambda x: (not x["is_directory"], x["name"]))

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a file"""
        full_path = self.workspace_path / file_path

        if not full_path.exists():
            return None

        versions = self.file_versions.get(file_path, [])
        current_version = versions[-1] if versions else None

        return {
            "path": file_path,
            "name": full_path.name,
            "size": full_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(
                full_path.stat().st_mtime
            ).isoformat(),
            "version": current_version.version if current_version else 0,
            "modified_by": current_version.modified_by
            if current_version
            else "unknown",
            "checksum": current_version.checksum if current_version else "",
            "locked": file_path in self.file_locks,
            "locked_by": self.file_locks[file_path].agent_id
            if file_path in self.file_locks
            else None,
            "has_conflicts": file_path in self.active_conflicts,
            "version_count": len(versions),
        }

    async def get_file_history(self, file_path: str) -> List[FileVersion]:
        """Get version history for a file"""
        return self.file_versions.get(file_path, [])

    async def resolve_conflict(
        self,
        file_path: str,
        agent_id: str,
        resolution_strategy: str,
        resolved_content: Optional[str] = None,
    ) -> bool:
        """
        Resolve a file conflict

        Args:
            file_path: Path to the conflicted file
            agent_id: Agent resolving the conflict
            resolution_strategy: Strategy used (merge, overwrite, manual)
            resolved_content: Final resolved content

        Returns:
            bool: True if conflict resolved successfully
        """
        conflict = self.active_conflicts.get(file_path)
        if not conflict:
            return False

        if resolved_content:
            success, error = await self.write_file(
                file_path,
                resolved_content,
                agent_id,
                changes_summary=f"Conflict resolved using {resolution_strategy}",
            )

            if not success:
                return False

        # Mark conflict as resolved
        conflict.resolved = True
        conflict.resolution_strategy = resolution_strategy

        # Remove from active conflicts
        del self.active_conflicts[file_path]

        # Save resolved conflict for history
        await self._save_resolved_conflict(conflict)

        # Track resolution
        if self.change_tracker:
            await self.change_tracker.track_file_event(
                file_path,
                "conflict_resolved",
                {"agent_id": agent_id, "strategy": resolution_strategy},
            )

        return True

    async def _get_current_version(self, file_path: str) -> int:
        """Get the current version number of a file"""
        versions = self.file_versions.get(file_path, [])
        return versions[-1].version if versions else 0

    async def _add_file_version(self, file_path: str, version: FileVersion):
        """Add a new version to file history"""
        if file_path not in self.file_versions:
            self.file_versions[file_path] = []

        self.file_versions[file_path].append(version)
        await self._save_file_versions(file_path)

    async def _handle_version_conflict(
        self, file_path: str, agent_id: str, expected_version: int, current_version: int
    ):
        """Handle a detected version conflict"""
        conflict = ConflictInfo(
            file_path=file_path,
            base_version=expected_version,
            agent1_version=expected_version,
            agent2_version=current_version,
            agent1_id=agent_id,
            agent2_id="unknown",  # Would need to track who made the current version
        )

        self.active_conflicts[file_path] = conflict
        await self._save_conflict(conflict)

        if self.change_tracker:
            await self.change_tracker.track_file_event(
                file_path,
                "conflict_detected",
                {
                    "agent_id": agent_id,
                    "expected_version": expected_version,
                    "current_version": current_version,
                },
            )

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of content"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _safe_filename(self, file_path: str) -> str:
        """Convert file path to safe filename"""
        return file_path.replace("/", "_").replace("\\", "_")

    async def _save_lock(self, lock: FileLock):
        """Save file lock to disk"""
        lock_file = self.locks_path / f"{self._safe_filename(lock.file_path)}.json"
        lock_dict = asdict(lock)
        lock_dict["acquired_at"] = lock.acquired_at.isoformat()
        if lock.expires_at:
            lock_dict["expires_at"] = lock.expires_at.isoformat()

        lock_file.write_text(json.dumps(lock_dict, indent=2))

    async def _save_file_versions(self, file_path: str):
        """Save file versions to disk"""
        if file_path not in self.file_versions:
            return

        version_file = self.versions_path / f"{self._safe_filename(file_path)}.json"
        versions_data = []

        for version in self.file_versions[file_path]:
            version_dict = asdict(version)
            version_dict["modified_at"] = version.modified_at.isoformat()
            versions_data.append(version_dict)

        version_file.write_text(json.dumps(versions_data, indent=2))

    async def _save_conflict(self, conflict: ConflictInfo):
        """Save conflict information to disk"""
        conflict_file = (
            self.conflicts_path / f"{self._safe_filename(conflict.file_path)}.json"
        )
        conflict_dict = asdict(conflict)
        conflict_dict["detected_at"] = conflict.detected_at.isoformat()

        conflict_file.write_text(json.dumps(conflict_dict, indent=2))

    async def _save_resolved_conflict(self, conflict: ConflictInfo):
        """Save resolved conflict to history"""
        resolved_file = (
            self.conflicts_path
            / "resolved"
            / f"{self._safe_filename(conflict.file_path)}_{int(datetime.now().timestamp())}.json"
        )
        resolved_file.parent.mkdir(exist_ok=True)

        conflict_dict = asdict(conflict)
        conflict_dict["detected_at"] = conflict.detected_at.isoformat()

        resolved_file.write_text(json.dumps(conflict_dict, indent=2))

        # Remove active conflict file
        active_file = (
            self.conflicts_path / f"{self._safe_filename(conflict.file_path)}.json"
        )
        active_file.unlink(missing_ok=True)
