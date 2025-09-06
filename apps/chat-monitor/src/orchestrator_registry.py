"""
Orchestrator Run Registry

Tracks active orchestrator runs and their agent swarms for selective monitoring.
Enables chat-monitor to focus on specific runs rather than all system agents.
"""

import fcntl
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentInfo:
    """Information about an agent in an orchestrator run."""

    session_id: str
    role: str
    location: str
    log_path: str
    start_time: str
    status: str = "active"


@dataclass
class OrchestratorRun:
    """Complete information about an orchestrator run."""

    run_id: str
    title: str
    orchestrator_session: str
    start_time: str
    status: str = "active"
    agent_sessions: List[AgentInfo] = field(default_factory=list)
    log_directories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class OrchestratorRegistry:
    """
    Registry for tracking active orchestrator runs and their agent swarms.

    Features:
    - Auto-registration by orchestrators
    - Agent tracking across worktrees
    - Thread-safe concurrent access
    - Easy discovery by chat-monitor
    - Cleanup of stale runs
    """

    def __init__(self, registry_dir: Optional[str] = None):
        self.registry_dir = Path(registry_dir or "/tmp/claude-orchestrator-runs")
        self.active_dir = self.registry_dir / "active"
        self.completed_dir = self.registry_dir / "completed"
        self.lock_file = self.registry_dir / "registry.lock"

        # Ensure directories exist
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self, timeout: float = 10.0):
        """Acquire exclusive lock for registry operations."""
        lock_fd = os.open(str(self.lock_file), os.O_CREAT | os.O_WRONLY)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
            except BlockingIOError:
                time.sleep(0.1)

        os.close(lock_fd)
        raise TimeoutError("Could not acquire registry lock")

    def _release_lock(self, lock_fd: int):
        """Release registry lock."""
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        except:
            pass

    def register_run(
        self,
        title: str,
        orchestrator_session: str,
        orchestrator_location: Optional[str] = None,
        worktrees: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        **metadata,
    ) -> str:
        """
        Register a new orchestrator run.

        Args:
            title: Human-readable title for the run
            orchestrator_session: Session ID of the orchestrator
            orchestrator_location: Working directory of orchestrator
            worktrees: List of worktree names being used
            focus_areas: List of focus areas for this run
            **metadata: Additional metadata

        Returns:
            Generated run ID
        """
        current_time = datetime.now(timezone.utc)
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")

        # Generate unique run ID
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        run_id = f"run_{timestamp}_{title_hash}"

        # Auto-detect orchestrator location and log path
        if not orchestrator_location:
            orchestrator_location = str(Path.cwd())

        orchestrator_log_path = self._infer_log_path(
            orchestrator_session, orchestrator_location
        )

        # Create run object
        run = OrchestratorRun(
            run_id=run_id,
            title=title,
            orchestrator_session=orchestrator_session,
            start_time=current_time.isoformat(),
            status="active",
        )

        # Add orchestrator as first agent
        orchestrator_info = AgentInfo(
            session_id=orchestrator_session,
            role="orchestrator",
            location=orchestrator_location,
            log_path=orchestrator_log_path,
            start_time=current_time.isoformat(),
        )
        run.agent_sessions.append(orchestrator_info)

        # Determine log directories
        log_dir = Path(orchestrator_log_path).parent
        run.log_directories = [str(log_dir)]

        # Add worktree log directories if specified
        if worktrees:
            base_name = Path(orchestrator_location).name
            for worktree in worktrees:
                worktree_log_dir = (
                    log_dir.parent / f"-home-opsvi-{base_name}-{worktree}"
                )
                if worktree_log_dir.exists():
                    run.log_directories.append(str(worktree_log_dir))

        # Add metadata
        run.metadata = {
            "orchestrator_location": orchestrator_location,
            "worktrees": worktrees or [],
            "focus_areas": focus_areas or [],
            **metadata,
        }

        # Save to registry
        self._save_run(run)

        return run_id

    def add_agent(
        self,
        run_id: str,
        agent_session_id: str,
        role: str = "agent",
        location: Optional[str] = None,
        **agent_metadata,
    ) -> bool:
        """
        Add an agent to an existing run.

        Args:
            run_id: ID of the run to add agent to
            agent_session_id: Session ID of the agent
            role: Role of the agent (e.g., "research_specialist")
            location: Working directory of the agent
            **agent_metadata: Additional agent metadata

        Returns:
            True if agent was added successfully
        """
        try:
            run = self.get_run_details(run_id)
            if not run:
                return False

            # Auto-detect agent location
            if not location:
                location = str(Path.cwd())

            # Infer log path
            agent_log_path = self._infer_log_path(agent_session_id, location)

            # Create agent info
            agent_info = AgentInfo(
                session_id=agent_session_id,
                role=role,
                location=location,
                log_path=agent_log_path,
                start_time=datetime.now(timezone.utc).isoformat(),
            )

            # Add to run
            run.agent_sessions.append(agent_info)

            # Update log directories if needed
            agent_log_dir = str(Path(agent_log_path).parent)
            if agent_log_dir not in run.log_directories:
                run.log_directories.append(agent_log_dir)

            # Update last modified
            run.last_updated = datetime.now(timezone.utc).isoformat()

            # Save updated run
            self._save_run(run)

            return True

        except Exception as e:
            print(f"Error adding agent to run {run_id}: {e}")
            return False

    def complete_run(self, run_id: str, completion_reason: str = "completed") -> bool:
        """
        Mark a run as completed and move to completed directory.

        Args:
            run_id: ID of run to complete
            completion_reason: Reason for completion

        Returns:
            True if run was completed successfully
        """
        try:
            run = self.get_run_details(run_id)
            if not run:
                return False

            # Update status
            run.status = "completed"
            run.last_updated = datetime.now(timezone.utc).isoformat()
            run.metadata["completion_reason"] = completion_reason
            run.metadata["completed_at"] = run.last_updated

            # Move from active to completed
            active_file = self.active_dir / f"{run_id}.json"
            completed_file = self.completed_dir / f"{run_id}.json"

            lock_fd = self._acquire_lock()
            try:
                # Save to completed directory
                with open(completed_file, "w") as f:
                    json.dump(asdict(run), f, indent=2)

                # Remove from active directory
                if active_file.exists():
                    active_file.unlink()

            finally:
                self._release_lock(lock_fd)

            return True

        except Exception as e:
            print(f"Error completing run {run_id}: {e}")
            return False

    def list_active_runs(self) -> List[OrchestratorRun]:
        """Get all active orchestrator runs."""
        runs = []

        try:
            for run_file in self.active_dir.glob("*.json"):
                try:
                    with open(run_file, "r") as f:
                        run_data = json.load(f)

                    # Convert agent_sessions back to AgentInfo objects
                    agent_sessions = [
                        AgentInfo(**agent)
                        for agent in run_data.get("agent_sessions", [])
                    ]
                    run_data["agent_sessions"] = agent_sessions

                    runs.append(OrchestratorRun(**run_data))

                except Exception as e:
                    print(f"Error loading run file {run_file}: {e}")
                    continue

        except Exception as e:
            print(f"Error listing active runs: {e}")

        # Sort by start time (newest first)
        runs.sort(key=lambda r: r.start_time, reverse=True)
        return runs

    def list_completed_runs(self, limit: int = 10) -> List[OrchestratorRun]:
        """Get recent completed runs."""
        runs = []

        try:
            run_files = sorted(
                self.completed_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            for run_file in run_files[:limit]:
                try:
                    with open(run_file, "r") as f:
                        run_data = json.load(f)

                    agent_sessions = [
                        AgentInfo(**agent)
                        for agent in run_data.get("agent_sessions", [])
                    ]
                    run_data["agent_sessions"] = agent_sessions

                    runs.append(OrchestratorRun(**run_data))

                except Exception as e:
                    print(f"Error loading completed run file {run_file}: {e}")
                    continue

        except Exception as e:
            print(f"Error listing completed runs: {e}")

        return runs

    def get_run_details(self, run_id: str) -> Optional[OrchestratorRun]:
        """Get detailed information about a specific run."""
        # Try active runs first
        active_file = self.active_dir / f"{run_id}.json"
        if active_file.exists():
            try:
                with open(active_file, "r") as f:
                    run_data = json.load(f)

                agent_sessions = [
                    AgentInfo(**agent) for agent in run_data.get("agent_sessions", [])
                ]
                run_data["agent_sessions"] = agent_sessions

                return OrchestratorRun(**run_data)

            except Exception as e:
                print(f"Error loading run {run_id}: {e}")

        # Try completed runs
        completed_file = self.completed_dir / f"{run_id}.json"
        if completed_file.exists():
            try:
                with open(completed_file, "r") as f:
                    run_data = json.load(f)

                agent_sessions = [
                    AgentInfo(**agent) for agent in run_data.get("agent_sessions", [])
                ]
                run_data["agent_sessions"] = agent_sessions

                return OrchestratorRun(**run_data)

            except Exception as e:
                print(f"Error loading completed run {run_id}: {e}")

        return None

    def find_runs_by_pattern(self, pattern: str) -> List[OrchestratorRun]:
        """Find runs matching a title pattern."""
        import re

        all_runs = self.list_active_runs() + self.list_completed_runs()
        pattern_re = re.compile(pattern, re.IGNORECASE)

        return [run for run in all_runs if pattern_re.search(run.title)]

    def cleanup_stale_runs(self, max_age_hours: int = 24):
        """Remove stale runs that haven't been updated recently."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

        for run_file in self.active_dir.glob("*.json"):
            try:
                if run_file.stat().st_mtime < cutoff_time:
                    # Check if run is actually stale by looking at last_updated
                    with open(run_file, "r") as f:
                        run_data = json.load(f)

                    last_updated = datetime.fromisoformat(
                        run_data.get("last_updated", "1970-01-01T00:00:00+00:00")
                    ).timestamp()

                    if last_updated < cutoff_time:
                        print(f"Removing stale run: {run_file.stem}")
                        run_file.unlink()

            except Exception as e:
                print(f"Error checking run file {run_file}: {e}")

    def _save_run(self, run: OrchestratorRun):
        """Save run to active directory with locking."""
        run_file = self.active_dir / f"{run.run_id}.json"

        lock_fd = self._acquire_lock()
        try:
            with open(run_file, "w") as f:
                json.dump(asdict(run), f, indent=2)
        finally:
            self._release_lock(lock_fd)

    def _infer_log_path(self, session_id: str, location: str) -> str:
        """
        Infer the log path for a session based on its location.

        Follows Claude Code's convention:
        ~/.claude/projects/-home-opsvi-{project_name}/session_id.jsonl
        """
        location_path = Path(location)

        # Extract project name from location
        # e.g., /home/opsvi/master_root/worktree_research -> master_root-worktree_research
        if location_path.name.startswith("worktree_"):
            # Worktree case: parent-worktree_name
            parent_name = location_path.parent.name
            worktree_name = location_path.name
            project_name = f"{parent_name}-{worktree_name}"
        else:
            # Regular case: just use directory name
            project_name = location_path.name

        # Construct log directory path
        log_dir = Path.home() / ".claude" / "projects" / f"-home-opsvi-{project_name}"
        log_file = log_dir / f"{session_id}.jsonl"

        return str(log_file)
