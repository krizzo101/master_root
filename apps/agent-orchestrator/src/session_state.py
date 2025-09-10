"""
Orchestrator Resume Functionality
Smart session state tracking to avoid duplicate work
"""
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class TaskState:
    """Individual task execution state"""

    task_id: str
    status: str  # pending, running, completed, failed
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    output_file: Optional[str] = None
    checksum: Optional[str] = None
    agent_type: Optional[str] = None
    dependencies_met: bool = False
    retry_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskState":
        return cls(**data)


@dataclass
class SessionState:
    """Complete orchestrator session state"""

    session_id: str
    started_at: float
    updated_at: float
    output_dir: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    config_checksum: str
    tasks: Dict[str, TaskState]
    resume_count: int = 0

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionState":
        tasks = {k: TaskState.from_dict(v) for k, v in data["tasks"].items()}
        data["tasks"] = tasks
        return cls(**data)


class SessionManager:
    """Manages orchestrator session state and resume functionality"""

    def __init__(self, output_base_dir: Path = None):
        self.output_base_dir = output_base_dir or Path("outputs/analysis")
        self.state_file_name = "session_state.json"
        self.current_session: Optional[SessionState] = None

    def generate_session_id(self, config: Dict) -> str:
        """Generate deterministic session ID based on config"""
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
        return f"session_{config_hash}"

    def calculate_config_checksum(self, config: Dict) -> str:
        """Calculate checksum of task configuration"""
        # Extract just the task definitions for checksum
        tasks_only = {
            "tasks": config.get("tasks", []),
            "max_parallel": config.get("agent_execution_config", {})
            .get("agent_requirements", {})
            .get("max_parallel_agents", 10),
        }
        config_str = json.dumps(tasks_only, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def find_resumable_session(self, config: Dict) -> Optional[SessionState]:
        """Find existing session that can be resumed"""
        config_checksum = self.calculate_config_checksum(config)

        # Look for recent sessions with matching config
        for session_dir in sorted(
            self.output_base_dir.glob("system_analysis_*"), reverse=True
        ):
            state_file = session_dir / self.state_file_name
            if not state_file.exists():
                continue

            try:
                with open(state_file) as f:
                    state_data = json.load(f)

                session_state = SessionState.from_dict(state_data)

                # Check if config matches and session is recent (within 24 hours)
                if (
                    session_state.config_checksum == config_checksum
                    and time.time() - session_state.started_at < 86400
                ):
                    return session_state

            except Exception as e:
                print(f"Warning: Could not load session state from {state_file}: {e}")

        return None

    def create_new_session(self, config: Dict, output_dir: Path) -> SessionState:
        """Create new session state"""
        session_id = self.generate_session_id(config)
        config_checksum = self.calculate_config_checksum(config)

        tasks = {}
        for task_config in config.get("tasks", []):
            task_state = TaskState(
                task_id=task_config["task_id"],
                status="pending",
                agent_type=task_config.get("task_type"),
                dependencies_met=len(task_config.get("dependencies", [])) == 0,
            )
            tasks[task_state.task_id] = task_state

        session_state = SessionState(
            session_id=session_id,
            started_at=time.time(),
            updated_at=time.time(),
            output_dir=str(output_dir),
            total_tasks=len(tasks),
            completed_tasks=0,
            failed_tasks=0,
            config_checksum=config_checksum,
            tasks=tasks,
        )

        self.current_session = session_state
        self.save_session_state()
        return session_state

    def resume_session(
        self, session_state: SessionState, new_output_dir: Path
    ) -> SessionState:
        """Resume existing session in new output directory"""
        # Update session for resume
        session_state.resume_count += 1
        session_state.updated_at = time.time()

        # Copy existing artifacts to new directory if they don't exist
        old_output_dir = Path(session_state.output_dir)
        if old_output_dir.exists() and old_output_dir != new_output_dir:
            self._copy_session_artifacts(old_output_dir, new_output_dir)

        # Update output directory
        session_state.output_dir = str(new_output_dir)

        self.current_session = session_state
        self.save_session_state()

        print(
            f"🔄 Resuming session {session_state.session_id} (resume #{session_state.resume_count})"
        )
        print(f"📂 Copied artifacts from {old_output_dir} to {new_output_dir}")

        return session_state

    def _copy_session_artifacts(self, source_dir: Path, dest_dir: Path):
        """Copy existing session artifacts to new directory"""
        import shutil

        # Ensure destination exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy task results
        source_tasks = source_dir / "tasks"
        dest_tasks = dest_dir / "tasks"
        if source_tasks.exists():
            dest_tasks.mkdir(exist_ok=True)
            for task_file in source_tasks.glob("*.json"):
                dest_file = dest_tasks / task_file.name
                if not dest_file.exists():
                    shutil.copy2(task_file, dest_file)

        # Copy other important artifacts
        for artifact_name in ["logs", "checkpoints", "metrics"]:
            source_artifact = source_dir / artifact_name
            dest_artifact = dest_dir / artifact_name
            if source_artifact.exists() and not dest_artifact.exists():
                if source_artifact.is_dir():
                    shutil.copytree(source_artifact, dest_artifact)
                else:
                    shutil.copy2(source_artifact, dest_artifact)

    def update_task_status(self, task_id: str, status: str, output_file: str = None):
        """Update task status and save session state"""
        if not self.current_session:
            return

        task_state = self.current_session.tasks.get(task_id)
        if not task_state:
            return

        old_status = task_state.status
        task_state.status = status
        task_state.updated_at = time.time()

        if status == "running" and old_status == "pending":
            task_state.started_at = time.time()
        elif status == "completed":
            task_state.completed_at = time.time()
            if output_file:
                task_state.output_file = output_file
                # Calculate checksum of output file for integrity
                try:
                    output_path = (
                        Path(self.current_session.output_dir)
                        / "tasks"
                        / f"{task_id}.json"
                    )
                    if output_path.exists():
                        with open(output_path, "rb") as f:
                            task_state.checksum = hashlib.md5(f.read()).hexdigest()
                except Exception:
                    pass
        elif status == "failed":
            task_state.retry_count += 1

        # Update session counters
        self._update_session_counters()

        # Update dependencies for other tasks
        self._update_dependencies()

        self.save_session_state()

    def _update_session_counters(self):
        """Update session-level counters"""
        if not self.current_session:
            return

        completed = sum(
            1
            for task in self.current_session.tasks.values()
            if task.status == "completed"
        )
        failed = sum(
            1 for task in self.current_session.tasks.values() if task.status == "failed"
        )

        self.current_session.completed_tasks = completed
        self.current_session.failed_tasks = failed
        self.current_session.updated_at = time.time()

    def _update_dependencies(self):
        """Update dependency status for pending tasks"""
        # This would need access to the original config to determine dependencies
        # For now, we'll implement a simple approach
        pass

    def save_session_state(self):
        """Save current session state to file"""
        if not self.current_session:
            return

        state_file = Path(self.current_session.output_dir) / self.state_file_name
        state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(state_file, "w") as f:
            json.dump(self.current_session.to_dict(), f, indent=2)

    def get_resumable_tasks(self) -> List[str]:
        """Get list of tasks that can be resumed (pending or failed)"""
        if not self.current_session:
            return []

        return [
            task_id
            for task_id, task_state in self.current_session.tasks.items()
            if task_state.status in ["pending", "failed"]
            and task_state.dependencies_met
        ]

    def get_completed_tasks(self) -> List[str]:
        """Get list of completed task IDs"""
        if not self.current_session:
            return []

        return [
            task_id
            for task_id, task_state in self.current_session.tasks.items()
            if task_state.status == "completed"
        ]

    def print_session_summary(self):
        """Print session status summary"""
        if not self.current_session:
            print("No active session")
            return

        session = self.current_session
        elapsed = time.time() - session.started_at

        print(f"📊 Session {session.session_id} (Resume #{session.resume_count})")
        print(f"⏱️  Runtime: {elapsed/60:.1f} minutes")
        print(f"✅ Completed: {session.completed_tasks}/{session.total_tasks}")
        print(f"❌ Failed: {session.failed_tasks}/{session.total_tasks}")
        print(f"📂 Output: {session.output_dir}")

        # Show task status breakdown
        status_counts = {}
        for task in session.tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

        print("📋 Task Status:")
        for status, count in sorted(status_counts.items()):
            print(f"   {status}: {count}")

        resumable = self.get_resumable_tasks()
        if resumable:
            print(f"🔄 Resumable tasks: {len(resumable)}")
