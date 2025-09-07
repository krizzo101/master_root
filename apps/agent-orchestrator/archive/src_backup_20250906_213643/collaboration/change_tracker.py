#!/usr/bin/env python3
"""
Change Tracker - Track changes and collaboration history

This module provides the ChangeTracker class which handles:
- Version control for collaborative artifacts
- Change history and attribution
- Event tracking for collaboration activities
- Git-like functionality for shared workspaces
"""

import asyncio
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ChangeEvent:
    """Represents a change event in the system"""

    event_id: str
    event_type: str  # file_create, file_modify, file_delete, workspace_event
    resource_path: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum_before: Optional[str] = None
    checksum_after: Optional[str] = None
    diff_summary: str = ""


@dataclass
class Commit:
    """Represents a commit in the change history"""

    commit_id: str
    agent_id: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    changes: List[ChangeEvent] = field(default_factory=list)
    parent_commit: Optional[str] = None
    workspace_id: str = ""


@dataclass
class Branch:
    """Represents a collaboration branch"""

    branch_name: str
    workspace_id: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    head_commit: Optional[str] = None
    description: str = ""


class ChangeTracker:
    """
    Tracks changes and maintains collaboration history

    Provides Git-like version control functionality for collaborative
    workspaces with change attribution and history management.
    """

    def __init__(self, tracking_path: Path):
        self.tracking_path = Path(tracking_path)
        self.events_path = self.tracking_path / "events"
        self.commits_path = self.tracking_path / "commits"
        self.branches_path = self.tracking_path / "branches"
        self.snapshots_path = self.tracking_path / "snapshots"

        # Ensure directories exist
        self.events_path.mkdir(parents=True, exist_ok=True)
        self.commits_path.mkdir(parents=True, exist_ok=True)
        self.branches_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_path.mkdir(parents=True, exist_ok=True)

        # In-memory state
        self.pending_changes: List[ChangeEvent] = []
        self.branches: Dict[str, Branch] = {}
        self.current_branch: str = "main"

        # Thread safety
        self.lock = asyncio.Lock()

        # Load existing state
        self._load_branches()

    def _load_branches(self):
        """Load existing branches"""
        for branch_file in self.branches_path.glob("*.json"):
            try:
                branch_data = json.loads(branch_file.read_text())
                # Convert datetime strings back to datetime objects
                if "created_at" in branch_data:
                    branch_data["created_at"] = datetime.fromisoformat(
                        branch_data["created_at"]
                    )
                branch = Branch(**branch_data)
                self.branches[branch.branch_name] = branch
            except Exception as e:
                print(f"Failed to load branch {branch_file}: {e}")

        # Create main branch if it doesn't exist
        if "main" not in self.branches:
            main_branch = Branch(
                branch_name="main",
                workspace_id="default",
                created_by="system",
                description="Main collaboration branch",
            )
            self.branches["main"] = main_branch
            self._save_branch(main_branch)

    async def track_file_event(
        self,
        file_path: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: str = "system",
        checksum_before: Optional[str] = None,
        checksum_after: Optional[str] = None,
    ) -> str:
        """
        Track a file-related event

        Args:
            file_path: Path to the file
            event_type: Type of event (create, modify, delete, read, etc.)
            metadata: Additional event metadata
            agent_id: Agent that performed the action
            checksum_before: File checksum before change
            checksum_after: File checksum after change

        Returns:
            str: Event ID
        """
        async with self.lock:
            event_id = str(uuid.uuid4())

            event = ChangeEvent(
                event_id=event_id,
                event_type=f"file_{event_type}",
                resource_path=file_path,
                agent_id=agent_id,
                metadata=metadata or {},
                checksum_before=checksum_before,
                checksum_after=checksum_after,
            )

            # Add to pending changes
            self.pending_changes.append(event)

            # Save event
            await self._save_event(event)

            return event_id

    async def track_workspace_event(
        self,
        workspace_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: str = "system",
    ) -> str:
        """
        Track a workspace-related event

        Args:
            workspace_id: Workspace ID
            event_type: Type of event (created, shared, deleted, etc.)
            metadata: Additional event metadata
            agent_id: Agent that performed the action

        Returns:
            str: Event ID
        """
        async with self.lock:
            event_id = str(uuid.uuid4())

            event = ChangeEvent(
                event_id=event_id,
                event_type=f"workspace_{event_type}",
                resource_path=f"workspace:{workspace_id}",
                agent_id=agent_id,
                metadata=metadata or {},
            )

            # Add to pending changes
            self.pending_changes.append(event)

            # Save event
            await self._save_event(event)

            return event_id

    async def commit_changes(
        self, agent_id: str, message: str, workspace_id: str = "default"
    ) -> str:
        """
        Commit pending changes

        Args:
            agent_id: Agent making the commit
            message: Commit message
            workspace_id: Workspace ID

        Returns:
            str: Commit ID
        """
        async with self.lock:
            if not self.pending_changes:
                return ""  # No changes to commit

            commit_id = str(uuid.uuid4())

            # Get parent commit
            current_branch = self.branches.get(self.current_branch)
            parent_commit = current_branch.head_commit if current_branch else None

            # Create commit
            commit = Commit(
                commit_id=commit_id,
                agent_id=agent_id,
                message=message,
                changes=self.pending_changes.copy(),
                parent_commit=parent_commit,
                workspace_id=workspace_id,
            )

            # Save commit
            await self._save_commit(commit)

            # Update branch head
            if current_branch:
                current_branch.head_commit = commit_id
                self._save_branch(current_branch)

            # Clear pending changes
            self.pending_changes.clear()

            return commit_id

    async def create_branch(
        self,
        branch_name: str,
        agent_id: str,
        workspace_id: str,
        description: str = "",
        base_commit: Optional[str] = None,
    ) -> bool:
        """
        Create a new collaboration branch

        Args:
            branch_name: Name of the new branch
            agent_id: Agent creating the branch
            workspace_id: Workspace ID
            description: Branch description
            base_commit: Base commit for the branch

        Returns:
            bool: True if branch created successfully
        """
        async with self.lock:
            if branch_name in self.branches:
                return False  # Branch already exists

            # Use current branch's head commit as base if not specified
            if not base_commit:
                current_branch = self.branches.get(self.current_branch)
                base_commit = current_branch.head_commit if current_branch else None

            branch = Branch(
                branch_name=branch_name,
                workspace_id=workspace_id,
                created_by=agent_id,
                head_commit=base_commit,
                description=description,
            )

            self.branches[branch_name] = branch
            self._save_branch(branch)

            return True

    async def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch"""
        if branch_name not in self.branches:
            return False

        # Commit any pending changes before switching
        if self.pending_changes:
            await self.commit_changes(
                "system", f"Auto-commit before switching to {branch_name}"
            )

        self.current_branch = branch_name
        return True

    async def get_commit_history(
        self,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Commit]:
        """
        Get commit history with optional filtering

        Args:
            workspace_id: Filter by workspace
            agent_id: Filter by agent
            limit: Maximum number of commits to return

        Returns:
            List of commits in reverse chronological order
        """
        commits = []

        # Load commits from disk
        for commit_file in self.commits_path.glob("*.json"):
            try:
                commit_data = json.loads(commit_file.read_text())

                # Convert datetime and nested objects
                if "timestamp" in commit_data:
                    commit_data["timestamp"] = datetime.fromisoformat(
                        commit_data["timestamp"]
                    )

                if "changes" in commit_data:
                    changes = []
                    for change_data in commit_data["changes"]:
                        if "timestamp" in change_data:
                            change_data["timestamp"] = datetime.fromisoformat(
                                change_data["timestamp"]
                            )
                        changes.append(ChangeEvent(**change_data))
                    commit_data["changes"] = changes

                commit = Commit(**commit_data)

                # Apply filters
                if workspace_id and commit.workspace_id != workspace_id:
                    continue
                if agent_id and commit.agent_id != agent_id:
                    continue

                commits.append(commit)

            except Exception as e:
                print(f"Failed to load commit {commit_file}: {e}")

        # Sort by timestamp (most recent first) and limit
        commits.sort(key=lambda c: c.timestamp, reverse=True)
        return commits[:limit]

    async def get_file_history(
        self, file_path: str, limit: int = 20
    ) -> List[ChangeEvent]:
        """
        Get change history for a specific file

        Args:
            file_path: Path to the file
            limit: Maximum number of events to return

        Returns:
            List of change events for the file
        """
        events = []

        # Load events from disk
        for event_file in self.events_path.glob("*.json"):
            try:
                event_data = json.loads(event_file.read_text())

                # Convert datetime
                if "timestamp" in event_data:
                    event_data["timestamp"] = datetime.fromisoformat(
                        event_data["timestamp"]
                    )

                event = ChangeEvent(**event_data)

                # Filter by file path
                if event.resource_path == file_path:
                    events.append(event)

            except Exception as e:
                print(f"Failed to load event {event_file}: {e}")

        # Sort by timestamp (most recent first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_agent_activity(
        self, agent_id: str, workspace_id: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get activity summary for an agent

        Args:
            agent_id: Agent ID
            workspace_id: Optional workspace filter
            hours: Time window in hours

        Returns:
            Activity summary dictionary
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        commits = await self.get_commit_history(workspace_id, agent_id, 100)
        recent_commits = [c for c in commits if c.timestamp >= cutoff_time]

        # Count events by type
        event_counts = {}
        files_modified = set()

        for commit in recent_commits:
            for event in commit.changes:
                event_type = event.event_type
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

                if event.event_type.startswith("file_"):
                    files_modified.add(event.resource_path)

        return {
            "agent_id": agent_id,
            "time_window_hours": hours,
            "total_commits": len(recent_commits),
            "total_events": sum(event_counts.values()),
            "event_breakdown": event_counts,
            "files_modified": len(files_modified),
            "recent_files": list(files_modified)[:10],  # Top 10 recent files
        }

    async def create_snapshot(
        self,
        workspace_path: Path,
        snapshot_name: str,
        agent_id: str,
        description: str = "",
    ) -> str:
        """
        Create a snapshot of the current workspace state

        Args:
            workspace_path: Path to the workspace
            snapshot_name: Name for the snapshot
            agent_id: Agent creating the snapshot
            description: Snapshot description

        Returns:
            str: Snapshot ID
        """
        snapshot_id = str(uuid.uuid4())
        snapshot_dir = self.snapshots_path / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)

        # Create snapshot metadata
        metadata = {
            "snapshot_id": snapshot_id,
            "name": snapshot_name,
            "created_by": agent_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "workspace_path": str(workspace_path),
            "commit_id": self.branches[self.current_branch].head_commit,
        }

        # Save metadata
        (snapshot_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # Create archive of workspace
        import shutil

        archive_path = snapshot_dir / "workspace_archive"
        shutil.copytree(
            workspace_path, archive_path, ignore=shutil.ignore_patterns(".*")
        )

        return snapshot_id

    async def restore_snapshot(
        self, snapshot_id: str, workspace_path: Path, agent_id: str
    ) -> bool:
        """
        Restore workspace from a snapshot

        Args:
            snapshot_id: ID of the snapshot to restore
            workspace_path: Target workspace path
            agent_id: Agent performing the restore

        Returns:
            bool: True if restore successful
        """
        snapshot_dir = self.snapshots_path / snapshot_id

        if not snapshot_dir.exists():
            return False

        # Load snapshot metadata
        metadata_file = snapshot_dir / "metadata.json"
        if not metadata_file.exists():
            return False

        # Backup current state
        backup_name = f"pre_restore_{int(datetime.now().timestamp())}"
        await self.create_snapshot(
            workspace_path, backup_name, agent_id, "Backup before restore"
        )

        # Restore from archive
        import shutil

        archive_path = snapshot_dir / "workspace_archive"

        if archive_path.exists():
            # Remove current workspace content
            for item in workspace_path.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            # Copy from archive
            for item in archive_path.iterdir():
                dest = workspace_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

            # Track restore event
            await self.track_workspace_event(
                "restored",
                "snapshot_restored",
                {"snapshot_id": snapshot_id, "restored_by": agent_id},
                agent_id,
            )

            return True

        return False

    async def _save_event(self, event: ChangeEvent):
        """Save event to disk"""
        event_file = self.events_path / f"{event.event_id}.json"
        event_dict = asdict(event)
        event_dict["timestamp"] = event.timestamp.isoformat()

        event_file.write_text(json.dumps(event_dict, indent=2))

    async def _save_commit(self, commit: Commit):
        """Save commit to disk"""
        # Ensure commits directory exists
        self.commits_path.mkdir(parents=True, exist_ok=True)

        commit_file = self.commits_path / f"{commit.commit_id}.json"
        commit_dict = asdict(commit)
        commit_dict["timestamp"] = commit.timestamp.isoformat()

        # Convert changes to dict
        changes_dict = []
        for change in commit.changes:
            change_dict = asdict(change)
            change_dict["timestamp"] = change.timestamp.isoformat()
            changes_dict.append(change_dict)
        commit_dict["changes"] = changes_dict

        commit_file.write_text(json.dumps(commit_dict, indent=2))

    def _save_branch(self, branch: Branch):
        """Save branch to disk"""
        branch_file = self.branches_path / f"{branch.branch_name}.json"
        branch_dict = asdict(branch)
        branch_dict["created_at"] = branch.created_at.isoformat()

        branch_file.write_text(json.dumps(branch_dict, indent=2))
