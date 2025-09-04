"""Common data models for the Unified Context System."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID


@dataclass
class ContextItem:
    """Core data model for context items in the unified system.

    Represents a single piece of contextual information that can be ingested
    from various sources (chat, code, git, errors, etc.) and stored in the
    temporal knowledge graph.
    """

    # Core identification
    source_type: str  # 'chat', 'code', 'git', 'error', 'monitor'
    source_id: str  # Original ID from source system
    entity_type: str  # 'message', 'file', 'commit', 'function', etc.

    # Temporal context
    timestamp: datetime
    timestamp_end: Optional[datetime] = None  # For duration events
    ingested_at: Optional[datetime] = None

    # Content
    title: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None  # SHA256 for deduplication
    summary: Optional[str] = None  # AI-generated summary

    # Location context
    project_id: Optional[str] = None
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None

    # Actor information
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # 'human', 'ai', 'system'
    session_id: Optional[str] = None

    # Classification
    severity: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)

    # Flexible data storage
    metrics: Optional[Dict[str, Any]] = field(default_factory=dict)
    source_data: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Search optimization
    embedding: Optional[List[float]] = None
    search_text: Optional[str] = None  # For full-text search

    # Database fields (set after storage)
    id: Optional[UUID] = field(default_factory=uuid.uuid4)
    neo4j_node_id: Optional[str] = None

    def __post_init__(self):
        """Post-initialization processing."""
        # Ensure ingested_at is set
        if not self.ingested_at:
            self.ingested_at = datetime.utcnow()

        # Initialize collections if None
        if self.tags is None:
            self.tags = []
        if self.metrics is None:
            self.metrics = {}
        if self.source_data is None:
            self.source_data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id) if self.id else None,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timestamp_end": self.timestamp_end.isoformat()
            if self.timestamp_end
            else None,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "title": self.title,
            "content": self.content,
            "content_hash": self.content_hash,
            "summary": self.summary,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "session_id": self.session_id,
            "severity": self.severity,
            "tags": self.tags,
            "metrics": self.metrics,
            "source_data": self.source_data,
            "embedding": self.embedding,
            "search_text": self.search_text,
            "neo4j_node_id": self.neo4j_node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextItem":
        """Create ContextItem from dictionary."""
        # Convert timestamp strings back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("timestamp_end"), str):
            data["timestamp_end"] = datetime.fromisoformat(data["timestamp_end"])
        if isinstance(data.get("ingested_at"), str):
            data["ingested_at"] = datetime.fromisoformat(data["ingested_at"])

        # Convert id string back to UUID
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])

        return cls(**data)


@dataclass
class ContextRelationship:
    """Represents a relationship between two context items."""

    source_id: UUID
    target_id: UUID
    relationship_type: str  # 'causes', 'references', 'contains', 'follows', 'resolves'
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"  # 'system', 'ai', 'human'

    # Temporal context
    temporal_context: Optional[str] = None  # 'before', 'during', 'after', 'concurrent'
    time_delta_seconds: Optional[int] = None

    # Validation
    validation_status: str = "pending"  # 'pending', 'validated', 'rejected'
    validation_score: Optional[float] = None

    # Database fields
    id: Optional[UUID] = field(default_factory=uuid.uuid4)
    neo4j_relationship_id: Optional[str] = None

    def __post_init__(self):
        """Validate confidence score."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Ensure metadata is initialized
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id) if self.id else None,
            "source_id": str(self.source_id),
            "target_id": str(self.target_id),
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "temporal_context": self.temporal_context,
            "time_delta_seconds": self.time_delta_seconds,
            "validation_status": self.validation_status,
            "validation_score": self.validation_score,
            "neo4j_relationship_id": self.neo4j_relationship_id,
        }


@dataclass
class BatchProcessingResult:
    """Result of batch processing operation."""

    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    duplicate_items: int = 0

    processing_time_seconds: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Relationship detection results
    relationships_detected: int = 0
    relationships_created: int = 0

    # Performance metrics
    items_per_second: float = 0.0
    memory_usage_mb: float = 0.0

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.processing_time_seconds > 0:
            self.items_per_second = self.processed_items / self.processing_time_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "duplicate_items": self.duplicate_items,
            "processing_time_seconds": self.processing_time_seconds,
            "errors": self.errors,
            "warnings": self.warnings,
            "relationships_detected": self.relationships_detected,
            "relationships_created": self.relationships_created,
            "items_per_second": self.items_per_second,
            "memory_usage_mb": self.memory_usage_mb,
        }


@dataclass
class PipelineStatus:
    """Overall pipeline status information."""

    running: bool = False
    uptime_seconds: float = 0.0

    # Adapter status
    adapters_total: int = 0
    adapters_running: int = 0
    adapters_failed: int = 0
    adapters_paused: int = 0

    # Processing metrics
    total_items_processed: int = 0
    total_items_failed: int = 0
    current_throughput: float = 0.0
    average_throughput: float = 0.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Health metrics
    health_score: float = 1.0  # 0.0 to 1.0
    last_error: Optional[str] = None
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "running": self.running,
            "uptime_seconds": self.uptime_seconds,
            "adapters_total": self.adapters_total,
            "adapters_running": self.adapters_running,
            "adapters_failed": self.adapters_failed,
            "adapters_paused": self.adapters_paused,
            "total_items_processed": self.total_items_processed,
            "total_items_failed": self.total_items_failed,
            "current_throughput": self.current_throughput,
            "average_throughput": self.average_throughput,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "health_score": self.health_score,
            "last_error": self.last_error,
            "last_activity": self.last_activity.isoformat()
            if self.last_activity
            else None,
        }
