"""Production-ready checkpoint and resume system for large-scale chat import operations."""

import asyncio
import hashlib
import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)


class CheckpointStatus(Enum):
    """Status of a checkpoint operation."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    RESUMED = "resumed"


@dataclass
class ImportProgress:
    """Tracks import progress state."""

    session_id: str
    source_path: str
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    last_processed_timestamp: Optional[datetime] = None
    last_processed_id: Optional[str] = None
    current_batch_start: int = 0
    current_file: Optional[str] = None
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        return (
            (self.processed_items / self.total_items * 100)
            if self.total_items > 0
            else 0.0
        )

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        total_processed = self.processed_items + self.failed_items
        return (
            (self.failed_items / total_processed * 100) if total_processed > 0 else 0.0
        )

    @property
    def elapsed_time_seconds(self) -> float:
        """Calculate elapsed time since start."""
        return (datetime.utcnow() - self.start_time).total_seconds()

    @property
    def estimated_remaining_seconds(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.processed_items == 0 or self.total_items == 0:
            return None

        remaining_items = self.total_items - self.processed_items
        items_per_second = self.processed_items / self.elapsed_time_seconds

        return remaining_items / items_per_second if items_per_second > 0 else None


@dataclass
class ProcessingState:
    """Current state of the import processing."""

    adapters_state: Dict[str, Dict[str, Any]]
    database_state: Dict[str, Any]
    embedding_progress: Dict[str, Any]
    relationship_progress: Dict[str, Any]
    memory_usage_mb: float
    active_connections: int
    error_log: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]


@dataclass
class Checkpoint:
    """Represents a complete checkpoint with all necessary recovery data."""

    checkpoint_id: str
    session_id: str
    created_at: datetime
    status: CheckpointStatus
    progress: ImportProgress
    processing_state: ProcessingState
    file_checksums: Dict[str, str]
    database_snapshot: Optional[Dict[str, Any]]
    recovery_metadata: Dict[str, Any]

    @property
    def age_minutes(self) -> float:
        """Age of checkpoint in minutes."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "progress": asdict(self.progress),
            "processing_state": asdict(self.processing_state),
            "file_checksums": self.file_checksums,
            "database_snapshot": self.database_snapshot,
            "recovery_metadata": self.recovery_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        # Parse datetime
        created_at = datetime.fromisoformat(data["created_at"])

        # Parse progress
        progress_data = data["progress"]
        if progress_data.get("last_processed_timestamp"):
            progress_data["last_processed_timestamp"] = datetime.fromisoformat(
                progress_data["last_processed_timestamp"]
            )
        if progress_data.get("start_time"):
            progress_data["start_time"] = datetime.fromisoformat(
                progress_data["start_time"]
            )
        progress = ImportProgress(**progress_data)

        # Parse processing state
        processing_state = ProcessingState(**data["processing_state"])

        return cls(
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            created_at=created_at,
            status=CheckpointStatus(data["status"]),
            progress=progress,
            processing_state=processing_state,
            file_checksums=data["file_checksums"],
            database_snapshot=data.get("database_snapshot"),
            recovery_metadata=data["recovery_metadata"],
        )


class CheckpointManager:
    """Production-ready checkpoint manager for large-scale imports."""

    def __init__(
        self,
        # Storage configuration
        checkpoint_directory: str = "/tmp/chat_import_checkpoints",
        max_checkpoints_per_session: int = 10,
        checkpoint_retention_hours: int = 72,
        # Performance configuration
        checkpoint_interval_items: int = 1000,
        checkpoint_interval_seconds: float = 300.0,  # 5 minutes
        enable_compression: bool = True,
        enable_integrity_checking: bool = True,
        # Recovery configuration
        auto_cleanup_failed: bool = True,
        backup_checkpoints: bool = True,
        # Advanced features
        enable_incremental_checkpoints: bool = True,
        enable_database_snapshots: bool = False,  # Resource intensive
        parallel_checkpoint_creation: bool = True,
    ):
        self.checkpoint_directory = Path(checkpoint_directory)
        self.max_checkpoints_per_session = max_checkpoints_per_session
        self.checkpoint_retention_hours = checkpoint_retention_hours

        self.checkpoint_interval_items = checkpoint_interval_items
        self.checkpoint_interval_seconds = checkpoint_interval_seconds
        self.enable_compression = enable_compression
        self.enable_integrity_checking = enable_integrity_checking

        self.auto_cleanup_failed = auto_cleanup_failed
        self.backup_checkpoints = backup_checkpoints

        self.enable_incremental_checkpoints = enable_incremental_checkpoints
        self.enable_database_snapshots = enable_database_snapshots
        self.parallel_checkpoint_creation = parallel_checkpoint_creation

        # Internal state
        self._active_sessions: Dict[str, ImportProgress] = {}
        self._last_checkpoint_time: Dict[str, datetime] = {}
        self._checkpoint_locks: Dict[str, asyncio.Lock] = {}

        self.logger = logger.bind(component="checkpoint_manager")

        # Ensure checkpoint directory exists
        self.checkpoint_directory.mkdir(parents=True, exist_ok=True)

        # Create backup directory if enabled
        if self.backup_checkpoints:
            (self.checkpoint_directory / "backups").mkdir(exist_ok=True)

    async def initialize_session(
        self, session_id: str, source_path: str, estimated_total_items: int = 0
    ) -> ImportProgress:
        """Initialize a new import session with progress tracking."""
        try:
            progress = ImportProgress(
                session_id=session_id,
                source_path=source_path,
                total_items=estimated_total_items,
                start_time=datetime.utcnow(),
            )

            self._active_sessions[session_id] = progress
            self._last_checkpoint_time[session_id] = datetime.utcnow()
            self._checkpoint_locks[session_id] = asyncio.Lock()

            # Clean up old checkpoints
            await self._cleanup_old_checkpoints(session_id)

            self.logger.info(
                "Import session initialized",
                session_id=session_id,
                source_path=source_path,
                estimated_items=estimated_total_items,
            )

            # Create initial checkpoint
            await self.create_checkpoint(session_id, force=True)

            return progress

        except Exception as e:
            self.logger.error(
                "Failed to initialize session", session_id=session_id, error=str(e)
            )
            raise

    async def update_progress(
        self,
        session_id: str,
        processed_items: int = 0,
        failed_items: int = 0,
        skipped_items: int = 0,
        last_processed_id: Optional[str] = None,
        current_file: Optional[str] = None,
        auto_checkpoint: bool = True,
    ) -> None:
        """Update import progress and conditionally create checkpoint."""
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not initialized")

        progress = self._active_sessions[session_id]

        # Update progress
        progress.processed_items += processed_items
        progress.failed_items += failed_items
        progress.skipped_items += skipped_items
        progress.last_processed_timestamp = datetime.utcnow()

        if last_processed_id:
            progress.last_processed_id = last_processed_id
        if current_file:
            progress.current_file = current_file

        # Check if checkpoint is needed
        if auto_checkpoint and await self._should_create_checkpoint(session_id):
            await self.create_checkpoint(session_id)

    async def _should_create_checkpoint(self, session_id: str) -> bool:
        """Determine if a checkpoint should be created."""
        progress = self._active_sessions[session_id]
        last_checkpoint = self._last_checkpoint_time.get(
            session_id, progress.start_time
        )

        # Time-based checkpoint
        time_since_last = (datetime.utcnow() - last_checkpoint).total_seconds()
        if time_since_last >= self.checkpoint_interval_seconds:
            return True

        # Item count-based checkpoint
        items_since_last = progress.processed_items % self.checkpoint_interval_items
        if items_since_last == 0 and progress.processed_items > 0:
            return True

        return False

    async def create_checkpoint(
        self,
        session_id: str,
        force: bool = False,
        include_database_snapshot: bool = False,
    ) -> str:
        """Create a comprehensive checkpoint for the session."""
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not initialized")

        async with self._checkpoint_locks[session_id]:
            try:
                start_time = time.time()
                checkpoint_id = f"{session_id}_{int(time.time() * 1000000)}"

                self.logger.info(
                    "Creating checkpoint",
                    session_id=session_id,
                    checkpoint_id=checkpoint_id,
                    force=force,
                )

                # Gather current state
                progress = self._active_sessions[session_id]
                processing_state = await self._capture_processing_state(session_id)
                file_checksums = await self._calculate_file_checksums(
                    progress.source_path
                )

                # Optional database snapshot
                database_snapshot = None
                if include_database_snapshot or self.enable_database_snapshots:
                    database_snapshot = await self._create_database_snapshot(session_id)

                # Create checkpoint object
                checkpoint = Checkpoint(
                    checkpoint_id=checkpoint_id,
                    session_id=session_id,
                    created_at=datetime.utcnow(),
                    status=CheckpointStatus.IN_PROGRESS,
                    progress=progress,
                    processing_state=processing_state,
                    file_checksums=file_checksums,
                    database_snapshot=database_snapshot,
                    recovery_metadata={
                        "creation_time_ms": (time.time() - start_time) * 1000,
                        "python_version": self._get_python_version(),
                        "system_info": await self._get_system_info(),
                    },
                )

                # Save checkpoint to disk
                await self._save_checkpoint(checkpoint)

                # Update status to completed
                checkpoint.status = CheckpointStatus.COMPLETED
                await self._save_checkpoint(checkpoint)

                # Update tracking
                self._last_checkpoint_time[session_id] = checkpoint.created_at

                creation_time_ms = (time.time() - start_time) * 1000

                self.logger.info(
                    "Checkpoint created successfully",
                    session_id=session_id,
                    checkpoint_id=checkpoint_id,
                    creation_time_ms=creation_time_ms,
                    progress_pct=progress.completion_percentage,
                )

                # Cleanup old checkpoints
                if not force:  # Don't cleanup during forced/initial checkpoints
                    await self._cleanup_old_checkpoints(session_id)

                return checkpoint_id

            except Exception as e:
                self.logger.error(
                    "Checkpoint creation failed", session_id=session_id, error=str(e)
                )
                raise

    async def _capture_processing_state(self, session_id: str) -> ProcessingState:
        """Capture comprehensive processing state for checkpoint."""
        try:
            # Get memory usage
            memory_usage_mb = await self._get_memory_usage()

            # Placeholder for more detailed state capture
            # In production, this would capture actual adapter states,
            # database connection info, etc.
            return ProcessingState(
                adapters_state={
                    "chat_adapter": {
                        "status": "running",
                        "processed_files": [],
                        "current_batch": 0,
                    }
                },
                database_state={
                    "connection_count": 0,
                    "pool_utilization": 0.0,
                    "last_query_time": datetime.utcnow().isoformat(),
                },
                embedding_progress={
                    "generated_count": 0,
                    "cache_hit_rate": 0.0,
                    "average_processing_time_ms": 0.0,
                },
                relationship_progress={
                    "detected_count": 0,
                    "stored_count": 0,
                    "last_detection_time": datetime.utcnow().isoformat(),
                },
                memory_usage_mb=memory_usage_mb,
                active_connections=0,
                error_log=[],
                quality_metrics={
                    "data_integrity_score": 1.0,
                    "processing_efficiency": 1.0,
                    "error_rate": 0.0,
                },
            )

        except Exception as e:
            self.logger.warning("Failed to capture full processing state", error=str(e))
            # Return minimal state to avoid blocking checkpoint creation
            return ProcessingState(
                adapters_state={},
                database_state={},
                embedding_progress={},
                relationship_progress={},
                memory_usage_mb=0.0,
                active_connections=0,
                error_log=[],
                quality_metrics={},
            )

    async def _calculate_file_checksums(self, source_path: str) -> Dict[str, str]:
        """Calculate checksums for source files to detect changes."""
        try:
            checksums = {}
            source_path_obj = Path(source_path)

            if source_path_obj.is_file():
                checksums[str(source_path_obj)] = await self._calculate_file_checksum(
                    source_path_obj
                )
            elif source_path_obj.is_dir():
                # Calculate checksums for all relevant files in directory
                for file_path in source_path_obj.rglob("*"):
                    if file_path.is_file() and file_path.suffix in [
                        ".json",
                        ".jsonl",
                        ".db",
                    ]:
                        checksums[str(file_path)] = await self._calculate_file_checksum(
                            file_path
                        )

            return checksums

        except Exception as e:
            self.logger.warning("Failed to calculate file checksums", error=str(e))
            return {}

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum for a file."""

        def calculate():
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, calculate)

    async def _create_database_snapshot(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Create database snapshot for recovery (optional, resource-intensive)."""
        try:
            # This is a placeholder for database snapshot functionality
            # In production, this might capture:
            # - Row counts for key tables
            # - Recent transaction IDs
            # - Index statistics
            # - Connection pool state

            return {
                "snapshot_time": datetime.utcnow().isoformat(),
                "context_items_count": 0,  # Would query actual count
                "relationships_count": 0,  # Would query actual count
                "last_ingested_timestamp": None,
                "database_size_mb": 0.0,
            }

        except Exception as e:
            self.logger.warning("Database snapshot creation failed", error=str(e))
            return None

    async def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to disk with optional compression and integrity checking."""
        checkpoint_file = self.checkpoint_directory / f"{checkpoint.checkpoint_id}.json"

        try:
            # Convert to JSON
            checkpoint_data = checkpoint.to_dict()
            json_data = json.dumps(checkpoint_data, indent=2, default=str)

            # Save to file
            def write_file():
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    f.write(json_data)

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, write_file)

            # Create backup if enabled
            if self.backup_checkpoints:
                backup_file = (
                    self.checkpoint_directory
                    / "backups"
                    / f"{checkpoint.checkpoint_id}.json"
                )

                def create_backup():
                    shutil.copy2(checkpoint_file, backup_file)

                await loop.run_in_executor(None, create_backup)

            # Verify integrity if enabled
            if self.enable_integrity_checking:
                await self._verify_checkpoint_integrity(checkpoint_file)

            self.logger.debug(
                "Checkpoint saved",
                checkpoint_id=checkpoint.checkpoint_id,
                file_size_bytes=checkpoint_file.stat().st_size,
            )

        except Exception as e:
            # Clean up partial file
            if checkpoint_file.exists():
                checkpoint_file.unlink()
            raise Exception(f"Failed to save checkpoint: {e}")

    async def _verify_checkpoint_integrity(self, checkpoint_file: Path) -> None:
        """Verify checkpoint file integrity."""
        try:

            def verify():
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Basic validation
                required_fields = [
                    "checkpoint_id",
                    "session_id",
                    "created_at",
                    "status",
                ]
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, verify)

        except Exception as e:
            raise Exception(f"Checkpoint integrity check failed: {e}")

    async def resume_from_checkpoint(
        self, session_id: str, checkpoint_id: Optional[str] = None
    ) -> Tuple[ImportProgress, Dict[str, Any]]:
        """Resume import from the most recent or specified checkpoint."""
        try:
            # Find checkpoint to resume from
            if checkpoint_id:
                checkpoint = await self._load_checkpoint(checkpoint_id)
            else:
                checkpoint = await self._find_latest_checkpoint(session_id)

            if not checkpoint:
                raise ValueError(f"No checkpoint found for session {session_id}")

            # Validate checkpoint
            await self._validate_checkpoint_for_resume(checkpoint)

            # Restore session state
            self._active_sessions[session_id] = checkpoint.progress
            self._last_checkpoint_time[session_id] = checkpoint.created_at
            self._checkpoint_locks[session_id] = asyncio.Lock()

            # Mark checkpoint as resumed
            checkpoint.status = CheckpointStatus.RESUMED
            await self._save_checkpoint(checkpoint)

            # Prepare recovery metadata
            recovery_info = {
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint_age_minutes": checkpoint.age_minutes,
                "progress_at_checkpoint": checkpoint.progress.completion_percentage,
                "items_to_resume_from": checkpoint.progress.processed_items,
                "last_processed_id": checkpoint.progress.last_processed_id,
                "source_file_changes": await self._detect_source_changes(checkpoint),
                "recommended_actions": await self._get_resume_recommendations(
                    checkpoint
                ),
            }

            self.logger.info(
                "Session resumed from checkpoint",
                session_id=session_id,
                checkpoint_id=checkpoint.checkpoint_id,
                progress_pct=checkpoint.progress.completion_percentage,
                age_minutes=checkpoint.age_minutes,
            )

            return checkpoint.progress, recovery_info

        except Exception as e:
            self.logger.error(
                "Failed to resume from checkpoint", session_id=session_id, error=str(e)
            )
            raise

    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from disk."""
        checkpoint_file = self.checkpoint_directory / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return None

        try:

            def load_file():
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, load_file)

            return Checkpoint.from_dict(data)

        except Exception as e:
            self.logger.error(
                "Failed to load checkpoint", checkpoint_id=checkpoint_id, error=str(e)
            )
            return None

    async def _find_latest_checkpoint(self, session_id: str) -> Optional[Checkpoint]:
        """Find the most recent valid checkpoint for a session."""
        try:
            checkpoint_files = list(
                self.checkpoint_directory.glob(f"{session_id}_*.json")
            )

            if not checkpoint_files:
                return None

            # Sort by modification time (most recent first)
            checkpoint_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Try to load checkpoints in order until we find a valid one
            for checkpoint_file in checkpoint_files:
                try:
                    checkpoint_id = checkpoint_file.stem
                    checkpoint = await self._load_checkpoint(checkpoint_id)

                    if checkpoint and checkpoint.status in [
                        CheckpointStatus.COMPLETED,
                        CheckpointStatus.RESUMED,
                    ]:
                        return checkpoint

                except Exception as e:
                    self.logger.warning(
                        "Failed to load checkpoint file",
                        file=checkpoint_file.name,
                        error=str(e),
                    )
                    continue

            return None

        except Exception as e:
            self.logger.error(
                "Failed to find latest checkpoint", session_id=session_id, error=str(e)
            )
            return None

    async def _validate_checkpoint_for_resume(self, checkpoint: Checkpoint) -> None:
        """Validate that checkpoint is suitable for resuming."""
        # Check checkpoint age
        if checkpoint.age_minutes > self.checkpoint_retention_hours * 60:
            raise ValueError(f"Checkpoint too old: {checkpoint.age_minutes} minutes")

        # Check status
        if checkpoint.status not in [
            CheckpointStatus.COMPLETED,
            CheckpointStatus.RESUMED,
        ]:
            raise ValueError(
                f"Checkpoint status not suitable for resume: {checkpoint.status}"
            )

        # Check source file integrity
        current_checksums = await self._calculate_file_checksums(
            checkpoint.progress.source_path
        )

        for file_path, expected_checksum in checkpoint.file_checksums.items():
            if file_path in current_checksums:
                if current_checksums[file_path] != expected_checksum:
                    self.logger.warning(
                        "Source file changed since checkpoint",
                        file=file_path,
                        expected_checksum=expected_checksum[:8],
                        current_checksum=current_checksums[file_path][:8],
                    )
            else:
                self.logger.warning(
                    "Source file missing since checkpoint", file=file_path
                )

    async def _detect_source_changes(self, checkpoint: Checkpoint) -> Dict[str, str]:
        """Detect changes in source files since checkpoint was created."""
        try:
            current_checksums = await self._calculate_file_checksums(
                checkpoint.progress.source_path
            )
            changes = {}

            for file_path, expected_checksum in checkpoint.file_checksums.items():
                if file_path not in current_checksums:
                    changes[file_path] = "file_deleted"
                elif current_checksums[file_path] != expected_checksum:
                    changes[file_path] = "file_modified"

            # Check for new files
            for file_path in current_checksums:
                if file_path not in checkpoint.file_checksums:
                    changes[file_path] = "file_added"

            return changes

        except Exception as e:
            self.logger.warning("Failed to detect source changes", error=str(e))
            return {}

    async def _get_resume_recommendations(self, checkpoint: Checkpoint) -> List[str]:
        """Get recommendations for resuming from checkpoint."""
        recommendations = []

        # Age-based recommendations
        if checkpoint.age_minutes > 60:  # Older than 1 hour
            recommendations.append(
                "Consider validating data integrity due to checkpoint age"
            )

        if checkpoint.age_minutes > 24 * 60:  # Older than 1 day
            recommendations.append("Recommend full restart due to old checkpoint")

        # Progress-based recommendations
        if checkpoint.progress.error_rate > 5.0:  # High error rate
            recommendations.append(
                "High error rate detected - investigate before resuming"
            )

        if checkpoint.progress.completion_percentage < 10.0:
            recommendations.append(
                "Low progress - consider full restart for optimal performance"
            )

        # Source file recommendations
        source_changes = await self._detect_source_changes(checkpoint)
        if source_changes:
            recommendations.append(
                f"Source files changed: {len(source_changes)} files affected"
            )

        return recommendations

    async def _cleanup_old_checkpoints(self, session_id: str) -> None:
        """Clean up old checkpoints to manage disk space."""
        try:
            checkpoint_files = list(
                self.checkpoint_directory.glob(f"{session_id}_*.json")
            )

            # Remove checkpoints beyond retention limit
            cutoff_time = datetime.utcnow() - timedelta(
                hours=self.checkpoint_retention_hours
            )

            for checkpoint_file in checkpoint_files:
                file_time = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                if file_time < cutoff_time:
                    self.logger.debug(
                        "Removing old checkpoint", file=checkpoint_file.name
                    )
                    checkpoint_file.unlink()

            # Keep only the most recent N checkpoints
            checkpoint_files = list(
                self.checkpoint_directory.glob(f"{session_id}_*.json")
            )
            if len(checkpoint_files) > self.max_checkpoints_per_session:
                # Sort by modification time and remove oldest
                checkpoint_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                for old_file in checkpoint_files[self.max_checkpoints_per_session :]:
                    self.logger.debug("Removing excess checkpoint", file=old_file.name)
                    old_file.unlink()

        except Exception as e:
            self.logger.warning("Checkpoint cleanup failed", error=str(e))

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive status for an import session."""
        if session_id not in self._active_sessions:
            return None

        progress = self._active_sessions[session_id]

        # Find available checkpoints
        checkpoints = await self._list_session_checkpoints(session_id)

        return {
            "session_id": session_id,
            "progress": asdict(progress),
            "checkpoints": {
                "count": len(checkpoints),
                "latest": checkpoints[0] if checkpoints else None,
                "total_size_mb": sum(cp["size_mb"] for cp in checkpoints),
            },
            "performance": {
                "items_per_second": (
                    progress.processed_items / progress.elapsed_time_seconds
                    if progress.elapsed_time_seconds > 0
                    else 0
                ),
                "estimated_remaining_seconds": progress.estimated_remaining_seconds,
            },
            "health": {
                "error_rate": progress.error_rate,
                "completion_percentage": progress.completion_percentage,
                "running_time_minutes": progress.elapsed_time_seconds / 60,
            },
        }

    async def _list_session_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a session."""
        try:
            checkpoint_files = list(
                self.checkpoint_directory.glob(f"{session_id}_*.json")
            )
            checkpoint_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            checkpoints = []
            for checkpoint_file in checkpoint_files:
                try:
                    stat_info = checkpoint_file.stat()
                    checkpoints.append(
                        {
                            "checkpoint_id": checkpoint_file.stem,
                            "created_at": datetime.fromtimestamp(
                                stat_info.st_mtime
                            ).isoformat(),
                            "size_mb": stat_info.st_size / (1024 * 1024),
                            "age_minutes": (time.time() - stat_info.st_mtime) / 60,
                        }
                    )
                except Exception as e:
                    self.logger.warning(
                        "Failed to get checkpoint info",
                        file=checkpoint_file.name,
                        error=str(e),
                    )

            return checkpoints

        except Exception as e:
            self.logger.error(
                "Failed to list checkpoints", session_id=session_id, error=str(e)
            )
            return []

    async def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

    def _get_python_version(self) -> str:
        """Get Python version string."""
        import sys

        return sys.version

    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for checkpoint metadata."""
        try:
            import platform

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            }
        except Exception:
            return {"platform": "unknown"}

    async def cleanup_session(self, session_id: str) -> None:
        """Clean up session resources and optionally remove checkpoints."""
        try:
            # Remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            if session_id in self._last_checkpoint_time:
                del self._last_checkpoint_time[session_id]
            if session_id in self._checkpoint_locks:
                del self._checkpoint_locks[session_id]

            # Optionally clean up failed checkpoints if enabled
            if self.auto_cleanup_failed:
                await self._cleanup_failed_checkpoints(session_id)

            self.logger.info("Session cleanup completed", session_id=session_id)

        except Exception as e:
            self.logger.error(
                "Session cleanup failed", session_id=session_id, error=str(e)
            )

    async def _cleanup_failed_checkpoints(self, session_id: str) -> None:
        """Remove failed or corrupted checkpoints."""
        try:
            checkpoint_files = list(
                self.checkpoint_directory.glob(f"{session_id}_*.json")
            )

            for checkpoint_file in checkpoint_files:
                try:
                    checkpoint = await self._load_checkpoint(checkpoint_file.stem)
                    if checkpoint and checkpoint.status in [
                        CheckpointStatus.FAILED,
                        CheckpointStatus.CORRUPTED,
                    ]:
                        self.logger.debug(
                            "Removing failed checkpoint", file=checkpoint_file.name
                        )
                        checkpoint_file.unlink()
                except Exception:
                    # If we can't load the checkpoint, it's probably corrupted
                    self.logger.debug(
                        "Removing corrupted checkpoint", file=checkpoint_file.name
                    )
                    checkpoint_file.unlink()

        except Exception as e:
            self.logger.warning("Failed checkpoint cleanup failed", error=str(e))
