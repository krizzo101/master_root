"""
Checkpoint and rollback management for enhanced safety.
Provides state snapshots and recovery capabilities.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Checkpoint:
    """Represents a saved state checkpoint"""

    def __init__(self, checkpoint_id: str, state: Dict[str, Any], metadata: Dict[str, Any]):
        self.id = checkpoint_id
        self.state = state
        self.metadata = metadata
        self.timestamp = datetime.utcnow()
        self.parent_id: Optional[str] = metadata.get("parent_id")

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary"""
        return {
            "id": self.id,
            "state": self.state,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "parent_id": self.parent_id,
        }


class CheckpointManager:
    """Manages checkpoints and rollback operations"""

    def __init__(
        self,
        max_checkpoints: int = 50,
        storage_path: Optional[Path] = None,
        auto_cleanup: bool = True,
    ):
        self.max_checkpoints = max_checkpoints
        self.storage_path = storage_path or Path("/tmp/hecaton_checkpoints")
        self.auto_cleanup = auto_cleanup
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_order: List[str] = []
        self._lock = asyncio.Lock()

        # Create storage directory if needed
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    async def create_checkpoint(
        self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new checkpoint with current state"""
        async with self._lock:
            checkpoint_id = self._generate_checkpoint_id()

            # Add parent reference if checkpoints exist
            if metadata is None:
                metadata = {}
            if self.checkpoint_order:
                metadata["parent_id"] = self.checkpoint_order[-1]

            # Create checkpoint
            checkpoint = Checkpoint(checkpoint_id, state, metadata)

            # Store in memory
            self.checkpoints[checkpoint_id] = checkpoint
            self.checkpoint_order.append(checkpoint_id)

            # Persist to disk if configured
            if self.storage_path:
                await self._persist_checkpoint(checkpoint)

            # Cleanup old checkpoints if needed
            if self.auto_cleanup and len(self.checkpoint_order) > self.max_checkpoints:
                await self._cleanup_old_checkpoints()

            logger.info(f"Created checkpoint: {checkpoint_id}")
            return checkpoint_id

    async def rollback_to_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Rollback to a specific checkpoint"""
        async with self._lock:
            if checkpoint_id not in self.checkpoints:
                # Try loading from disk
                checkpoint = await self._load_checkpoint(checkpoint_id)
                if not checkpoint:
                    raise ValueError(f"Checkpoint not found: {checkpoint_id}")
                self.checkpoints[checkpoint_id] = checkpoint

            checkpoint = self.checkpoints[checkpoint_id]

            # Remove all checkpoints after this one
            idx = self.checkpoint_order.index(checkpoint_id)
            checkpoints_to_remove = self.checkpoint_order[idx + 1 :]

            for ckpt_id in checkpoints_to_remove:
                if ckpt_id in self.checkpoints:
                    del self.checkpoints[ckpt_id]
                # Remove from disk
                if self.storage_path:
                    checkpoint_file = self.storage_path / f"{ckpt_id}.pkl"
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()

            self.checkpoint_order = self.checkpoint_order[: idx + 1]

            logger.info(f"Rolled back to checkpoint: {checkpoint_id}")
            return checkpoint.state

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieve a specific checkpoint"""
        async with self._lock:
            if checkpoint_id in self.checkpoints:
                return self.checkpoints[checkpoint_id]

            # Try loading from disk
            return await self._load_checkpoint(checkpoint_id)

    async def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints"""
        async with self._lock:
            return [self.checkpoints[ckpt_id].to_dict() for ckpt_id in self.checkpoint_order]

    async def prune_checkpoint_branch(self, checkpoint_id: str):
        """Remove a checkpoint and all its descendants"""
        async with self._lock:
            if checkpoint_id not in self.checkpoints:
                raise ValueError(f"Checkpoint not found: {checkpoint_id}")

            # Find all descendants
            descendants = self._find_descendants(checkpoint_id)

            # Remove checkpoint and descendants
            for ckpt_id in [checkpoint_id] + descendants:
                if ckpt_id in self.checkpoints:
                    del self.checkpoints[ckpt_id]
                if ckpt_id in self.checkpoint_order:
                    self.checkpoint_order.remove(ckpt_id)

                # Remove from disk
                if self.storage_path:
                    checkpoint_file = self.storage_path / f"{ckpt_id}.pkl"
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()

            logger.info(f"Pruned checkpoint branch: {checkpoint_id}")

    async def _persist_checkpoint(self, checkpoint: Checkpoint):
        """Persist checkpoint to disk"""
        try:
            checkpoint_file = self.storage_path / f"{checkpoint.id}.pkl"

            # Serialize checkpoint
            serialized = self._serialize_state(checkpoint.to_dict())

            # Write to file
            with open(checkpoint_file, "wb") as f:
                pickle.dump(serialized, f)

        except Exception as e:
            logger.error(f"Failed to persist checkpoint {checkpoint.id}: {e}")

    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from disk"""
        try:
            checkpoint_file = self.storage_path / f"{checkpoint_id}.pkl"

            if not checkpoint_file.exists():
                return None

            # Read from file
            with open(checkpoint_file, "rb") as f:
                serialized = pickle.load(f)

            # Deserialize checkpoint
            data = self._deserialize_state(serialized)

            checkpoint = Checkpoint(
                checkpoint_id=data["id"], state=data["state"], metadata=data["metadata"]
            )
            checkpoint.timestamp = datetime.fromisoformat(data["timestamp"])

            return checkpoint

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    async def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond max limit"""
        while len(self.checkpoint_order) > self.max_checkpoints:
            oldest_id = self.checkpoint_order.pop(0)

            if oldest_id in self.checkpoints:
                del self.checkpoints[oldest_id]

            # Remove from disk
            if self.storage_path:
                checkpoint_file = self.storage_path / f"{oldest_id}.pkl"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()

            logger.debug(f"Removed old checkpoint: {oldest_id}")

    def _find_descendants(self, checkpoint_id: str) -> List[str]:
        """Find all descendant checkpoints"""
        descendants = []

        for ckpt_id, checkpoint in self.checkpoints.items():
            if checkpoint.parent_id == checkpoint_id:
                descendants.append(ckpt_id)
                descendants.extend(self._find_descendants(ckpt_id))

        return descendants

    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize state for storage"""
        # For now, just return as-is
        # Could add compression or custom serialization here
        return state

    def _deserialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize state from storage"""
        return state

    def _generate_checkpoint_id(self) -> str:
        """Generate unique checkpoint ID"""
        import uuid

        return f"ckpt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
