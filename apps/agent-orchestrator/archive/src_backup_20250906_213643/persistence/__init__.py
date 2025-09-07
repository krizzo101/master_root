"""
Collaboration Persistence Layer
Comprehensive data storage, caching, and analytics for agent collaboration

This package provides:
- PostgreSQL-based persistent storage with optimized schema
- Redis caching for real-time performance
- Advanced query engine with full-text search and analytics
- Backup and migration management
- Repository pattern for clean data access

Usage:
    from src.persistence import (
        DatabaseManager, CollaborationCacheManager,
        CollaborationQueryEngine, CollaborationBackupManager,
        AgentRepository, SessionRepository, MessageRepository
    )

    # Initialize persistence layer
    db_manager = await initialize_database()
    cache_manager = CollaborationCacheManager(db_manager.redis_pool)
    query_engine = CollaborationQueryEngine(db_manager, cache_manager)
"""

from .backup import (
    INITIAL_MIGRATION,
    PERFORMANCE_INDEXES_MIGRATION,
    BackupFormat,
    BackupMetadata,
    BackupType,
    CollaborationBackupManager,
    MigrationManager,
    MigrationScript,
    MigrationType,
)
from .cache import (
    CollaborationCache,
    CollaborationCacheManager,
    DistributedLock,
    RealTimeCollaborationCache,
)
from .database import (
    DatabaseConfig,
    DatabaseManager,
    cleanup_database,
    get_database_manager,
    initialize_database,
)
from .models import (  # SQLAlchemy models; Pydantic models for API serialization; Enums
    Agent,
    AgentModel,
    AgentStatus,
    Artifact,
    ArtifactModel,
    Event,
    EventModel,
    EventType,
    Message,
    MessageModel,
    MessageType,
    Metric,
    MetricModel,
    Session,
    SessionModel,
    Workspace,
    WorkspaceModel,
)
from .query_engine import CollaborationQueryEngine, QueryFilter, QueryResult, QueryType
from .repositories import (
    AgentRepository,
    AnalyticsRepository,
    BaseRepository,
    MessageRepository,
    SessionRepository,
    WorkspaceRepository,
)

__all__ = [
    # Database management
    "DatabaseManager",
    "DatabaseConfig",
    "initialize_database",
    "cleanup_database",
    "get_database_manager",
    # Data models
    "Agent",
    "Session",
    "Message",
    "Workspace",
    "Artifact",
    "Event",
    "Metric",
    "AgentModel",
    "SessionModel",
    "MessageModel",
    "WorkspaceModel",
    "ArtifactModel",
    "EventModel",
    "MetricModel",
    "AgentStatus",
    "MessageType",
    "EventType",
    # Data access repositories
    "BaseRepository",
    "AgentRepository",
    "SessionRepository",
    "MessageRepository",
    "WorkspaceRepository",
    "AnalyticsRepository",
    # Caching
    "CollaborationCache",
    "RealTimeCollaborationCache",
    "CollaborationCacheManager",
    "DistributedLock",
    # Query engine
    "CollaborationQueryEngine",
    "QueryType",
    "QueryFilter",
    "QueryResult",
    # Backup and migration
    "CollaborationBackupManager",
    "MigrationManager",
    "BackupType",
    "BackupFormat",
    "MigrationType",
    "BackupMetadata",
    "MigrationScript",
    "INITIAL_MIGRATION",
    "PERFORMANCE_INDEXES_MIGRATION",
]

__version__ = "1.0.0"
