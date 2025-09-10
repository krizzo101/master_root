#!/usr/bin/env python3
"""
Auto-Resume Manager for Agent Orchestrator
Automatically detects and resumes previous workflow runs
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AutoResumeManager:
    """Manages automatic workflow resumption"""

    def __init__(self, output_base: Path = Path("output")):
        self.output_base = output_base
        self.workflow_registry = output_base / ".workflow_registry.json"
        self._ensure_registry()

    def _ensure_registry(self):
        """Ensure workflow registry exists"""
        if not self.workflow_registry.exists():
            self.workflow_registry.write_text(json.dumps({}, indent=2))

    def _get_workflow_hash(self, tasks_file: Path) -> str:
        """Generate unique hash for workflow file"""
        content = tasks_file.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def register_workflow(self, tasks_file: Path, workflow_id: str, output_dir: Path):
        """Register a new workflow run"""
        registry = json.loads(self.workflow_registry.read_text())
        workflow_hash = self._get_workflow_hash(tasks_file)

        if workflow_hash not in registry:
            registry[workflow_hash] = []

        registry[workflow_hash].append(
            {
                "workflow_id": workflow_id,
                "output_dir": str(output_dir),
                "tasks_file": str(tasks_file),
                "started_at": datetime.now().isoformat(),
                "status": "running",
            }
        )

        self.workflow_registry.write_text(json.dumps(registry, indent=2))
        logger.info(f"Registered workflow {workflow_id} for {tasks_file.name}")

    def find_existing_run(self, tasks_file: Path) -> Optional[Dict[str, Any]]:
        """Find most recent incomplete run for given tasks file"""
        registry = json.loads(self.workflow_registry.read_text())
        workflow_hash = self._get_workflow_hash(tasks_file)

        if workflow_hash not in registry:
            return None

        # Find most recent run
        runs = registry[workflow_hash]
        for run in reversed(runs):  # Most recent first
            output_dir = Path(run["output_dir"])

            # Check if checkpoint exists
            checkpoint_dir = output_dir / "checkpoints"
            if checkpoint_dir.exists():
                checkpoints = list(checkpoint_dir.glob("checkpoint_*.json"))
                if checkpoints:
                    # Find latest checkpoint
                    latest_checkpoint = max(
                        checkpoints, key=lambda p: p.stat().st_mtime
                    )

                    # Check if workflow is complete
                    completion_file = (
                        output_dir / "deliverables" / "workflow_completion_report.json"
                    )
                    if completion_file.exists():
                        completion = json.loads(completion_file.read_text())
                        if completion.get("tasks_completed", 0) == completion.get(
                            "tasks_total", 0
                        ):
                            logger.info(
                                f"Workflow {run['workflow_id']} already complete"
                            )
                            continue

                    # Found incomplete run with checkpoint
                    return {
                        "workflow_id": run["workflow_id"],
                        "output_dir": output_dir,
                        "checkpoint": latest_checkpoint,
                        "started_at": run["started_at"],
                    }

        return None

    def get_resume_info(self, tasks_file: Path) -> Optional[Dict[str, Any]]:
        """Get resume information if available"""
        existing = self.find_existing_run(tasks_file)

        if existing:
            # Load checkpoint to get progress
            checkpoint_data = json.loads(existing["checkpoint"].read_text())
            completed_tasks = [
                t["task_id"] for t in checkpoint_data.get("completed_tasks", [])
            ]
            total_tasks = len(checkpoint_data.get("all_tasks", []))

            return {
                "should_resume": True,
                "checkpoint_file": existing["checkpoint"],
                "output_dir": existing["output_dir"],
                "workflow_id": existing["workflow_id"],
                "progress": {
                    "completed": len(completed_tasks),
                    "total": total_tasks,
                    "percentage": (len(completed_tasks) / total_tasks * 100)
                    if total_tasks > 0
                    else 0,
                    "completed_task_ids": completed_tasks,
                },
                "original_start": existing["started_at"],
            }

        return None

    def mark_complete(self, workflow_id: str):
        """Mark workflow as complete"""
        registry = json.loads(self.workflow_registry.read_text())

        for workflow_hash, runs in registry.items():
            for run in runs:
                if run["workflow_id"] == workflow_id:
                    run["status"] = "completed"
                    run["completed_at"] = datetime.now().isoformat()
                    break

        self.workflow_registry.write_text(json.dumps(registry, indent=2))
        logger.info(f"Marked workflow {workflow_id} as complete")


# Integration function for main.py
async def check_and_resume(tasks_file: Path, output_dir: Path = None) -> Dict[str, Any]:
    """Check if workflow should resume from checkpoint"""
    manager = AutoResumeManager()
    resume_info = manager.get_resume_info(tasks_file)

    if resume_info:
        print(f"\n🔄 PREVIOUS RUN DETECTED")
        print(f"   Workflow: {resume_info['workflow_id']}")
        print(
            f"   Progress: {resume_info['progress']['completed']}/{resume_info['progress']['total']} tasks ({resume_info['progress']['percentage']:.1f}%)"
        )
        print(f"   Started: {resume_info['original_start']}")
        print(f"   Checkpoint: {resume_info['checkpoint_file'].name}")

        # Auto-resume by default
        response = input("\n   Resume from checkpoint? [Y/n]: ").strip().lower()
        if response != "n":
            print(f"\n✅ Resuming from checkpoint...")
            return {
                "action": "resume",
                "checkpoint": resume_info["checkpoint_file"],
                "output_dir": resume_info["output_dir"],
            }

    # New run
    if output_dir is None:
        output_dir = Path(
            f"output/{tasks_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    workflow_id = (
        f"workflow_{tasks_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    manager.register_workflow(tasks_file, workflow_id, output_dir)

    return {"action": "new", "workflow_id": workflow_id, "output_dir": output_dir}
