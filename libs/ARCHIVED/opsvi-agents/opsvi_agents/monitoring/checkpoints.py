"""Checkpoint management for agent execution."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Checkpoint:
    """Execution checkpoint."""

    checkpoint_id: str
    task_id: str
    operation_count: int
    state: Dict[str, Any]
    next_actions: List[str]
    rollback_point: Optional[str]
    timestamp: str


class CheckpointManager:
    """Manage execution checkpoints."""

    def __init__(self, checkpoint_dir: str = ".proj-intel/checkpoints"):
        """Initialize checkpoint manager."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger.bind(component="CheckpointManager")
        self.active_checkpoints: Dict[str, Checkpoint] = {}

    def create(
        self,
        task_id: str,
        operation_count: int,
        state: Dict[str, Any],
        next_actions: List[str] = None,
        rollback_point: str = None,
    ) -> str:
        """Create a new checkpoint."""
        timestamp = datetime.now()
        checkpoint_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{task_id}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            operation_count=operation_count,
            state=state,
            next_actions=next_actions or [],
            rollback_point=rollback_point,
            timestamp=timestamp.isoformat(),
        )

        # Save to disk
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(asdict(checkpoint), f, indent=2)

        # Track active checkpoint
        self.active_checkpoints[task_id] = checkpoint

        self._logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load a checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            self._logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None

        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
                return Checkpoint(**data)
        except Exception as e:
            self._logger.error(f"Failed to load checkpoint: {e}")
            return None

    def get_latest(self, task_id: str) -> Optional[Checkpoint]:
        """Get latest checkpoint for task."""
        # Check active checkpoints first
        if task_id in self.active_checkpoints:
            return self.active_checkpoints[task_id]

        # Search on disk
        pattern = f"*_{task_id}.json"
        checkpoint_files = sorted(self.checkpoint_dir.glob(pattern))

        if checkpoint_files:
            return self.load(checkpoint_files[-1].stem)

        return None

    def list_checkpoints(self, task_id: str = None) -> List[str]:
        """List available checkpoints."""
        if task_id:
            pattern = f"*_{task_id}.json"
        else:
            pattern = "*.json"

        checkpoint_files = self.checkpoint_dir.glob(pattern)
        return [f.stem for f in checkpoint_files]

    def restore(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore from checkpoint."""
        checkpoint = self.load(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Cannot restore: checkpoint {checkpoint_id} not found")

        self._logger.info(f"Restoring from checkpoint: {checkpoint_id}")

        return {
            "task_id": checkpoint.task_id,
            "state": checkpoint.state,
            "next_actions": checkpoint.next_actions,
            "rollback_point": checkpoint.rollback_point,
        }

    def cleanup(self, days: int = 7) -> int:
        """Clean up old checkpoints."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = 0

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, "r") as f:
                    data = json.load(f)
                    timestamp = datetime.fromisoformat(data["timestamp"]).timestamp()

                    if timestamp < cutoff:
                        checkpoint_file.unlink()
                        removed += 1
            except Exception as e:
                self._logger.error(f"Error cleaning checkpoint {checkpoint_file}: {e}")

        if removed > 0:
            self._logger.info(f"Removed {removed} old checkpoints")

        return removed

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if checkpoint_file.exists():
            checkpoint_file.unlink()

            # Remove from active if present
            for task_id, checkpoint in list(self.active_checkpoints.items()):
                if checkpoint.checkpoint_id == checkpoint_id:
                    del self.active_checkpoints[task_id]

            self._logger.info(f"Deleted checkpoint: {checkpoint_id}")
            return True

        return False


# Global checkpoint manager
manager = CheckpointManager()
