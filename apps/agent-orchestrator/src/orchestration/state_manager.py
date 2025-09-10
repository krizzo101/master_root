#!/usr/bin/env python3
"""
State Manager Component
Handles workflow state persistence, recovery, and metadata management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages workflow state, metadata, and persistence
    Extracted from GenericOrchestrator
    """

    def __init__(
        self,
        output_dir: Path,
        workflow_id: str,
        workflow_name: str,
        workflow_source: str,
        enable_dashboard_reporting: bool = False,
        dashboard_state_callback: Optional[Callable] = None,
    ):
        self.output_dir = output_dir.resolve()
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.workflow_source = workflow_source
        self.workflow_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Dashboard integration
        self.enable_dashboard_reporting = enable_dashboard_reporting
        self.dashboard_state_callback = dashboard_state_callback

        # Create state directories
        self.metadata_dir = self.output_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.state_dir = self.output_dir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.workflow_state = {
            "status": "initialized",
            "started_at": None,
            "completed_at": None,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "current_phase": "initialization",
        }

        # Metadata
        self.metadata = self._initialize_metadata()
        self._save_metadata()

        logger.info(f"StateManager initialized for workflow: {workflow_id}")

    def _initialize_metadata(self) -> Dict[str, Any]:
        """Initialize workflow metadata"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_source": self.workflow_source,
            "timestamp": self.workflow_timestamp,
            "created_at": datetime.now().isoformat(),
            "output_dir": str(self.output_dir),
            "status": "initialized",
            "configuration": {
                "dashboard_enabled": self.enable_dashboard_reporting,
            },
            "execution": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "phases": [],
            },
        }

    def _save_metadata(self):
        """Save metadata to file"""
        metadata_file = self.metadata_dir / "metadata.json"
        metadata_file.write_text(json.dumps(self.metadata, indent=2))
        logger.debug(f"Saved metadata to {metadata_file}")

    def update_metadata(self, updates: Dict[str, Any]):
        """Update workflow metadata"""
        for key, value in updates.items():
            if "." in key:
                # Handle nested keys like "execution.total_tasks"
                keys = key.split(".")
                target = self.metadata
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                target[keys[-1]] = value
            else:
                self.metadata[key] = value

        self.metadata["updated_at"] = datetime.now().isoformat()
        self._save_metadata()

    def set_workflow_status(self, status: str):
        """Set workflow status"""
        self.workflow_state["status"] = status
        self.metadata["status"] = status

        if status == "running" and not self.workflow_state["started_at"]:
            self.workflow_state["started_at"] = datetime.now().isoformat()
            self.metadata["started_at"] = self.workflow_state["started_at"]
        elif status == "completed":
            self.workflow_state["completed_at"] = datetime.now().isoformat()
            self.metadata["completed_at"] = self.workflow_state["completed_at"]

        self._save_state()
        self._save_metadata()

        # Report to dashboard if enabled
        if self.enable_dashboard_reporting:
            self._report_state_change(status)

    def set_current_phase(self, phase: str):
        """Set current execution phase"""
        self.workflow_state["current_phase"] = phase

        if "phases" not in self.metadata["execution"]:
            self.metadata["execution"]["phases"] = []

        self.metadata["execution"]["phases"].append(
            {"phase": phase, "started_at": datetime.now().isoformat()}
        )

        self._save_state()
        self._save_metadata()

    def update_task_counts(
        self,
        total: Optional[int] = None,
        completed: Optional[int] = None,
        failed: Optional[int] = None,
    ):
        """Update task count statistics"""
        if total is not None:
            self.workflow_state["total_tasks"] = total
            self.metadata["execution"]["total_tasks"] = total

        if completed is not None:
            self.workflow_state["completed_tasks"] = completed
            self.metadata["execution"]["completed_tasks"] = completed

        if failed is not None:
            self.workflow_state["failed_tasks"] = failed
            self.metadata["execution"]["failed_tasks"] = failed

        self._save_state()
        self._save_metadata()

    def save_checkpoint(self, checkpoint_name: str, data: Dict[str, Any]):
        """Save a named checkpoint"""
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_name}.json"

        checkpoint_data = {
            "checkpoint_name": checkpoint_name,
            "workflow_id": self.workflow_id,
            "timestamp": datetime.now().isoformat(),
            "workflow_state": self.workflow_state.copy(),
            "data": data,
        }

        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        logger.info(f"Saved checkpoint: {checkpoint_name}")

        return checkpoint_file

    def load_checkpoint(self, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """Load a named checkpoint"""
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_name}.json"

        if not checkpoint_file.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_name}")
            return None

        checkpoint_data = json.loads(checkpoint_file.read_text())

        # Restore workflow state
        self.workflow_state = checkpoint_data["workflow_state"]
        self._save_state()

        logger.info(f"Loaded checkpoint: {checkpoint_name}")
        return checkpoint_data["data"]

    def list_checkpoints(self) -> List[str]:
        """List available checkpoints"""
        checkpoints = []
        for checkpoint_file in self.state_dir.glob("checkpoint_*.json"):
            name = checkpoint_file.stem.replace("checkpoint_", "")
            checkpoints.append(name)
        return sorted(checkpoints)

    def _save_state(self):
        """Save current workflow state"""
        state_file = self.state_dir / "workflow_state.json"
        state_file.write_text(json.dumps(self.workflow_state, indent=2))

    def load_state(self) -> Dict[str, Any]:
        """Load workflow state from file"""
        state_file = self.state_dir / "workflow_state.json"

        if state_file.exists():
            self.workflow_state = json.loads(state_file.read_text())
            logger.info("Loaded existing workflow state")

        return self.workflow_state

    def save_task_state(self, task_id: str, state: Dict[str, Any]):
        """Save individual task state"""
        task_file = self.state_dir / f"task_{task_id}.json"

        task_state = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "state": state,
        }

        task_file.write_text(json.dumps(task_state, indent=2))

    def load_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load individual task state"""
        task_file = self.state_dir / f"task_{task_id}.json"

        if not task_file.exists():
            return None

        task_state = json.loads(task_file.read_text())
        return task_state["state"]

    def get_all_task_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all saved task states"""
        task_states = {}

        for task_file in self.state_dir.glob("task_*.json"):
            task_id = task_file.stem.replace("task_", "")
            task_state = json.loads(task_file.read_text())
            task_states[task_id] = task_state["state"]

        return task_states

    def _report_state_change(self, status: str):
        """Report state change to dashboard"""
        if not self.dashboard_state_callback:
            return

        try:
            self.dashboard_state_callback(
                {
                    "workflow_id": self.workflow_id,
                    "status": status,
                    "state": self.workflow_state,
                    "metadata": self.metadata,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to report state to dashboard: {e}")

    def report_workflow_started(self):
        """Report workflow start"""
        self.set_workflow_status("running")

        if self.enable_dashboard_reporting:
            logger.info(f"Reported workflow start: {self.workflow_id}")

    def report_workflow_progress(
        self,
        completed_tasks: int,
        total_tasks: int,
        current_task: Optional[str] = None,
        eta_seconds: Optional[int] = None,
    ):
        """Report workflow progress"""
        self.update_task_counts(total=total_tasks, completed=completed_tasks)

        if self.enable_dashboard_reporting and self.dashboard_state_callback:
            progress_data = {
                "workflow_id": self.workflow_id,
                "type": "progress",
                "completed": completed_tasks,
                "total": total_tasks,
                "progress_percent": (completed_tasks / total_tasks * 100)
                if total_tasks > 0
                else 0,
                "current_task": current_task,
                "eta_seconds": eta_seconds,
                "timestamp": datetime.now().isoformat(),
            }

            try:
                self.dashboard_state_callback(progress_data)
            except Exception as e:
                logger.warning(f"Failed to report progress: {e}")

    def report_task_activity(
        self, task_id: str, activity_type: str, details: Optional[Dict[str, Any]] = None
    ):
        """Report task activity"""
        if not self.enable_dashboard_reporting or not self.dashboard_state_callback:
            return

        activity_data = {
            "workflow_id": self.workflow_id,
            "type": "task_activity",
            "task_id": task_id,
            "activity": activity_type,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            self.dashboard_state_callback(activity_data)
        except Exception as e:
            logger.warning(f"Failed to report task activity: {e}")

    def report_workflow_completed(self, metrics: Dict[str, Any]):
        """Report workflow completion"""
        self.set_workflow_status("completed")

        if self.enable_dashboard_reporting and self.dashboard_state_callback:
            completion_data = {
                "workflow_id": self.workflow_id,
                "type": "completion",
                "metrics": metrics,
                "state": self.workflow_state,
                "timestamp": datetime.now().isoformat(),
            }

            try:
                self.dashboard_state_callback(completion_data)
                logger.info(f"Reported workflow completion: {self.workflow_id}")
            except Exception as e:
                logger.warning(f"Failed to report completion: {e}")

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get workflow summary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_source": self.workflow_source,
            "status": self.workflow_state["status"],
            "current_phase": self.workflow_state["current_phase"],
            "total_tasks": self.workflow_state["total_tasks"],
            "completed_tasks": self.workflow_state["completed_tasks"],
            "failed_tasks": self.workflow_state["failed_tasks"],
            "started_at": self.workflow_state["started_at"],
            "completed_at": self.workflow_state["completed_at"],
            "output_dir": str(self.output_dir),
        }

    def cleanup_old_states(self, keep_last: int = 5):
        """Clean up old state files, keeping only the most recent"""
        # Get all checkpoint files
        checkpoints = sorted(
            self.state_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Remove old checkpoints
        for checkpoint in checkpoints[keep_last:]:
            try:
                checkpoint.unlink()
                logger.debug(f"Removed old checkpoint: {checkpoint}")
            except Exception as e:
                logger.warning(f"Failed to remove checkpoint {checkpoint}: {e}")

        # Clean up old task states
        task_states = sorted(
            self.state_dir.glob("task_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Keep more task states
        for task_state in task_states[keep_last * 10 :]:
            try:
                task_state.unlink()
                logger.debug(f"Removed old task state: {task_state}")
            except Exception as e:
                logger.warning(f"Failed to remove task state {task_state}: {e}")
