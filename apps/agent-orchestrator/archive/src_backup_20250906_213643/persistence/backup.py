"""
Backup and Migration Systems for Collaboration Data
Comprehensive data protection and schema management
"""

import asyncio
import gzip
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import DatabaseConfig, DatabaseManager
from .models import Base

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


class BackupFormat(str, Enum):
    JSON = "json"
    SQL = "sql"
    BINARY = "binary"


class MigrationType(str, Enum):
    SCHEMA_CHANGE = "schema_change"
    DATA_MIGRATION = "data_migration"
    INDEX_REBUILD = "index_rebuild"
    CONSTRAINT_UPDATE = "constraint_update"


@dataclass
class BackupMetadata:
    """Backup metadata information"""

    backup_id: str
    backup_type: BackupType
    backup_format: BackupFormat
    created_at: datetime
    size_bytes: int
    tables_included: List[str]
    record_counts: Dict[str, int]
    checksum: str
    compressed: bool = True
    retention_days: int = 30


@dataclass
class MigrationScript:
    """Database migration script definition"""

    migration_id: str
    version: str
    migration_type: MigrationType
    description: str
    up_sql: str
    down_sql: str
    dependencies: List[str]
    created_at: datetime


class CollaborationBackupManager:
    """Comprehensive backup management for collaboration data"""

    def __init__(self, db_manager: DatabaseManager, backup_dir: Path):
        self.db = db_manager
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Define table backup order (respecting foreign keys)
        self.table_order = [
            "agents",
            "sessions",
            "workspaces",
            "messages",
            "artifacts",
            "events",
            "metrics",
        ]

    async def create_full_backup(
        self,
        backup_id: Optional[str] = None,
        format_type: BackupFormat = BackupFormat.JSON,
        compress: bool = True,
    ) -> BackupMetadata:
        """Create complete database backup"""
        backup_id = backup_id or f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.backup"

        logger.info(f"Starting full backup: {backup_id}")
        start_time = datetime.utcnow()

        backup_data = {
            "metadata": {
                "backup_id": backup_id,
                "backup_type": BackupType.FULL,
                "created_at": start_time.isoformat(),
                "format": format_type.value,
                "compressed": compress,
            },
            "schema": await self._export_schema(),
            "data": {},
        }

        total_records = 0
        table_counts = {}

        # Backup each table
        for table_name in self.table_order:
            logger.info(f"Backing up table: {table_name}")

            if format_type == BackupFormat.JSON:
                table_data = await self._export_table_json(table_name)
                backup_data["data"][table_name] = table_data["rows"]
                table_counts[table_name] = table_data["count"]
                total_records += table_data["count"]
            elif format_type == BackupFormat.SQL:
                # For SQL format, generate INSERT statements
                sql_data = await self._export_table_sql(table_name)
                backup_data["data"][table_name] = sql_data["statements"]
                table_counts[table_name] = sql_data["count"]
                total_records += sql_data["count"]

        # Write backup file
        backup_content = json.dumps(backup_data, default=str, indent=2)

        if compress:
            with gzip.open(f"{backup_path}.gz", "wt", encoding="utf-8") as f:
                f.write(backup_content)
            backup_path = Path(f"{backup_path}.gz")
        else:
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(backup_content)

        # Calculate checksum
        import hashlib

        with open(backup_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            backup_format=format_type,
            created_at=start_time,
            size_bytes=backup_path.stat().st_size,
            tables_included=list(self.table_order),
            record_counts=table_counts,
            checksum=checksum,
            compressed=compress,
        )

        # Save metadata
        await self._save_backup_metadata(metadata)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Full backup completed: {backup_id} ({total_records} records, {duration:.2f}s)"
        )

        return metadata

    async def create_incremental_backup(
        self, since_timestamp: datetime, backup_id: Optional[str] = None
    ) -> BackupMetadata:
        """Create incremental backup since timestamp"""
        backup_id = backup_id or f"incr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.backup.gz"

        logger.info(f"Starting incremental backup since: {since_timestamp}")
        start_time = datetime.utcnow()

        backup_data = {
            "metadata": {
                "backup_id": backup_id,
                "backup_type": BackupType.INCREMENTAL,
                "created_at": start_time.isoformat(),
                "since_timestamp": since_timestamp.isoformat(),
                "format": BackupFormat.JSON.value,
                "compressed": True,
            },
            "data": {},
        }

        total_records = 0
        table_counts = {}

        # Export changed data from each table
        async with self.db.get_pg_connection() as conn:
            for table_name in self.table_order:
                # Get timestamp column for each table
                timestamp_col = self._get_timestamp_column(table_name)
                if not timestamp_col:
                    continue

                query = f"""
                    SELECT * FROM {table_name}
                    WHERE {timestamp_col} >= $1
                    ORDER BY {timestamp_col}
                """

                rows = await conn.fetch(query, since_timestamp)
                if rows:
                    backup_data["data"][table_name] = [dict(row) for row in rows]
                    table_counts[table_name] = len(rows)
                    total_records += len(rows)
                    logger.info(f"Incremental backup {table_name}: {len(rows)} records")

        # Write compressed backup
        with gzip.open(backup_path, "wt", encoding="utf-8") as f:
            json.dump(backup_data, f, default=str, indent=2)

        # Calculate checksum
        import hashlib

        with open(backup_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.INCREMENTAL,
            backup_format=BackupFormat.JSON,
            created_at=start_time,
            size_bytes=backup_path.stat().st_size,
            tables_included=list(table_counts.keys()),
            record_counts=table_counts,
            checksum=checksum,
            compressed=True,
        )

        await self._save_backup_metadata(metadata)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Incremental backup completed: {backup_id} ({total_records} records, {duration:.2f}s)"
        )

        return metadata

    async def restore_backup(
        self,
        backup_id: str,
        target_tables: Optional[List[str]] = None,
        verify_checksums: bool = True,
    ) -> Dict[str, Any]:
        """Restore database from backup"""
        logger.info(f"Starting restore from backup: {backup_id}")

        # Load backup metadata
        metadata = await self._load_backup_metadata(backup_id)
        if not metadata:
            raise ValueError(f"Backup metadata not found: {backup_id}")

        backup_path = self._get_backup_path(backup_id, metadata.compressed)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Verify checksum
        if verify_checksums:
            import hashlib

            with open(backup_path, "rb") as f:
                file_checksum = hashlib.sha256(f.read()).hexdigest()

            if file_checksum != metadata.checksum:
                raise ValueError(f"Backup checksum mismatch: {backup_id}")

        # Load backup data
        if metadata.compressed:
            with gzip.open(backup_path, "rt", encoding="utf-8") as f:
                backup_data = json.load(f)
        else:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

        # Filter tables if specified
        if target_tables:
            data_to_restore = {
                table: data
                for table, data in backup_data["data"].items()
                if table in target_tables
            }
        else:
            data_to_restore = backup_data["data"]

        # Restore data
        restore_results = {}
        total_restored = 0

        async with self.db.get_async_session() as session:
            for table_name in self.table_order:
                if table_name not in data_to_restore:
                    continue

                table_data = data_to_restore[table_name]
                if not table_data:
                    continue

                logger.info(f"Restoring table {table_name}: {len(table_data)} records")

                try:
                    # Clear existing data (if full restore)
                    if metadata.backup_type == BackupType.FULL:
                        await session.execute(
                            text(f"TRUNCATE TABLE {table_name} CASCADE")
                        )

                    # Insert data
                    inserted = await self._insert_table_data(
                        session, table_name, table_data
                    )
                    restore_results[table_name] = {
                        "records_restored": inserted,
                        "status": "success",
                    }
                    total_restored += inserted

                except Exception as e:
                    logger.error(f"Failed to restore table {table_name}: {e}")
                    restore_results[table_name] = {
                        "records_restored": 0,
                        "status": "failed",
                        "error": str(e),
                    }
                    await session.rollback()
                    raise

        logger.info(
            f"Restore completed: {backup_id} ({total_restored} records restored)"
        )

        return {
            "backup_id": backup_id,
            "backup_type": metadata.backup_type,
            "total_records_restored": total_restored,
            "table_results": restore_results,
            "restore_timestamp": datetime.utcnow(),
        }

    async def list_backups(self) -> List[BackupMetadata]:
        """List all available backups"""
        backups = []
        metadata_files = list(self.backup_dir.glob("*.metadata.json"))

        for metadata_file in metadata_files:
            try:
                with open(metadata_file, "r") as f:
                    metadata_dict = json.load(f)

                metadata = BackupMetadata(
                    backup_id=metadata_dict["backup_id"],
                    backup_type=BackupType(metadata_dict["backup_type"]),
                    backup_format=BackupFormat(metadata_dict["backup_format"]),
                    created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                    size_bytes=metadata_dict["size_bytes"],
                    tables_included=metadata_dict["tables_included"],
                    record_counts=metadata_dict["record_counts"],
                    checksum=metadata_dict["checksum"],
                    compressed=metadata_dict.get("compressed", True),
                    retention_days=metadata_dict.get("retention_days", 30),
                )
                backups.append(metadata)

            except Exception as e:
                logger.warning(f"Failed to load backup metadata {metadata_file}: {e}")

        return sorted(backups, key=lambda x: x.created_at, reverse=True)

    async def cleanup_old_backups(self, retention_days: int = 30) -> List[str]:
        """Remove backups older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        backups = await self.list_backups()

        deleted_backups = []

        for backup in backups:
            if backup.created_at < cutoff_date:
                try:
                    # Remove backup file
                    backup_path = self._get_backup_path(
                        backup.backup_id, backup.compressed
                    )
                    if backup_path.exists():
                        backup_path.unlink()

                    # Remove metadata file
                    metadata_path = (
                        self.backup_dir / f"{backup.backup_id}.metadata.json"
                    )
                    if metadata_path.exists():
                        metadata_path.unlink()

                    deleted_backups.append(backup.backup_id)
                    logger.info(f"Deleted old backup: {backup.backup_id}")

                except Exception as e:
                    logger.error(f"Failed to delete backup {backup.backup_id}: {e}")

        return deleted_backups

    async def _export_schema(self) -> Dict[str, Any]:
        """Export database schema"""
        async with self.db.get_pg_connection() as conn:
            # Get table schemas
            schema_info = {}

            for table_name in self.table_order:
                # Get column information
                columns = await conn.fetch(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """,
                    table_name,
                )

                # Get constraints
                constraints = await conn.fetch(
                    """
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = $1
                """,
                    table_name,
                )

                # Get indexes
                indexes = await conn.fetch(
                    """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = $1
                """,
                    table_name,
                )

                schema_info[table_name] = {
                    "columns": [dict(col) for col in columns],
                    "constraints": [dict(const) for const in constraints],
                    "indexes": [dict(idx) for idx in indexes],
                }

            return schema_info

    async def _export_table_json(self, table_name: str) -> Dict[str, Any]:
        """Export table data as JSON"""
        async with self.db.get_pg_connection() as conn:
            rows = await conn.fetch(f"SELECT * FROM {table_name}")
            return {"rows": [dict(row) for row in rows], "count": len(rows)}

    async def _export_table_sql(self, table_name: str) -> Dict[str, Any]:
        """Export table data as SQL INSERT statements"""
        async with self.db.get_pg_connection() as conn:
            rows = await conn.fetch(f"SELECT * FROM {table_name}")

            statements = []
            for row in rows:
                columns = list(row.keys())
                values = list(row.values())

                # Format SQL INSERT
                col_str = ", ".join(columns)
                val_str = ", ".join([f"${i+1}" for i in range(len(values))])
                statement = f"INSERT INTO {table_name} ({col_str}) VALUES ({val_str})"
                statements.append({"sql": statement, "values": values})

            return {"statements": statements, "count": len(statements)}

    async def _insert_table_data(
        self, session: AsyncSession, table_name: str, data: List[Dict]
    ) -> int:
        """Insert data into table"""
        if not data:
            return 0

        # Build INSERT query
        columns = list(data[0].keys())
        col_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])

        query = text(f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})")

        # Execute batch insert
        await session.execute(query, data)
        return len(data)

    def _get_timestamp_column(self, table_name: str) -> Optional[str]:
        """Get timestamp column for incremental backups"""
        timestamp_columns = {
            "agents": "updated_at",
            "sessions": "updated_at",
            "messages": "sent_at",
            "workspaces": "updated_at",
            "artifacts": "updated_at",
            "events": "timestamp",
            "metrics": "timestamp",
        }
        return timestamp_columns.get(table_name)

    def _get_backup_path(self, backup_id: str, compressed: bool = True) -> Path:
        """Get backup file path"""
        suffix = ".backup.gz" if compressed else ".backup"
        return self.backup_dir / f"{backup_id}{suffix}"

    async def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file"""
        metadata_path = self.backup_dir / f"{metadata.backup_id}.metadata.json"

        metadata_dict = {
            "backup_id": metadata.backup_id,
            "backup_type": metadata.backup_type.value,
            "backup_format": metadata.backup_format.value,
            "created_at": metadata.created_at.isoformat(),
            "size_bytes": metadata.size_bytes,
            "tables_included": metadata.tables_included,
            "record_counts": metadata.record_counts,
            "checksum": metadata.checksum,
            "compressed": metadata.compressed,
            "retention_days": metadata.retention_days,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata_dict, f, indent=2)

    async def _load_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata from file"""
        metadata_path = self.backup_dir / f"{backup_id}.metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata_dict = json.load(f)

            return BackupMetadata(
                backup_id=metadata_dict["backup_id"],
                backup_type=BackupType(metadata_dict["backup_type"]),
                backup_format=BackupFormat(metadata_dict["backup_format"]),
                created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                size_bytes=metadata_dict["size_bytes"],
                tables_included=metadata_dict["tables_included"],
                record_counts=metadata_dict["record_counts"],
                checksum=metadata_dict["checksum"],
                compressed=metadata_dict.get("compressed", True),
                retention_days=metadata_dict.get("retention_days", 30),
            )
        except Exception:
            return None


class MigrationManager:
    """Database schema migration management"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.migrations: List[MigrationScript] = []

        # Initialize migration tracking table
        asyncio.create_task(self._ensure_migration_table())

    async def _ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            async with self.db.get_pg_connection() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        migration_id VARCHAR(255) PRIMARY KEY,
                        version VARCHAR(50) NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        rollback_sql TEXT
                    )
                """
                )
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")

    def add_migration(self, migration: MigrationScript):
        """Add migration script"""
        self.migrations.append(migration)
        logger.info(f"Added migration: {migration.migration_id}")

    async def apply_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Apply pending migrations"""
        applied_migrations = await self._get_applied_migrations()
        pending_migrations = [
            m for m in self.migrations if m.migration_id not in applied_migrations
        ]

        if target_version:
            pending_migrations = [
                m for m in pending_migrations if m.version <= target_version
            ]

        # Sort by version/dependencies
        pending_migrations.sort(key=lambda x: x.version)

        applied = []

        for migration in pending_migrations:
            try:
                logger.info(f"Applying migration: {migration.migration_id}")

                async with self.db.get_pg_connection() as conn:
                    async with conn.transaction():
                        # Execute migration SQL
                        await conn.execute(migration.up_sql)

                        # Record migration
                        await conn.execute(
                            """
                            INSERT INTO schema_migrations (migration_id, version, rollback_sql)
                            VALUES ($1, $2, $3)
                        """,
                            migration.migration_id,
                            migration.version,
                            migration.down_sql,
                        )

                applied.append(migration.migration_id)
                logger.info(f"Applied migration: {migration.migration_id}")

            except Exception as e:
                logger.error(f"Failed to apply migration {migration.migration_id}: {e}")
                break

        return applied

    async def rollback_migration(self, migration_id: str) -> bool:
        """Rollback specific migration"""
        try:
            async with self.db.get_pg_connection() as conn:
                # Get rollback SQL
                rollback_sql = await conn.fetchval(
                    """
                    SELECT rollback_sql FROM schema_migrations
                    WHERE migration_id = $1
                """,
                    migration_id,
                )

                if not rollback_sql:
                    raise ValueError(f"Migration not found: {migration_id}")

                async with conn.transaction():
                    # Execute rollback
                    await conn.execute(rollback_sql)

                    # Remove migration record
                    await conn.execute(
                        """
                        DELETE FROM schema_migrations
                        WHERE migration_id = $1
                    """,
                        migration_id,
                    )

                logger.info(f"Rolled back migration: {migration_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to rollback migration {migration_id}: {e}")
            return False

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        applied_migrations = await self._get_applied_migrations()

        status = {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied_migrations),
            "pending_count": len(self.migrations) - len(applied_migrations),
            "applied_migrations": applied_migrations,
            "pending_migrations": [
                m.migration_id
                for m in self.migrations
                if m.migration_id not in applied_migrations
            ],
        }

        return status

    async def _get_applied_migrations(self) -> Set[str]:
        """Get set of applied migration IDs"""
        try:
            async with self.db.get_pg_connection() as conn:
                rows = await conn.fetch("SELECT migration_id FROM schema_migrations")
                return {row["migration_id"] for row in rows}
        except Exception:
            return set()


# Example migration scripts
INITIAL_MIGRATION = MigrationScript(
    migration_id="001_initial_schema",
    version="1.0.0",
    migration_type=MigrationType.SCHEMA_CHANGE,
    description="Initial collaboration schema",
    up_sql="""
        -- This migration is handled by SQLAlchemy Base.metadata.create_all()
        SELECT 1;
    """,
    down_sql="""
        -- Drop all tables
        DROP TABLE IF EXISTS metrics CASCADE;
        DROP TABLE IF EXISTS events CASCADE;
        DROP TABLE IF EXISTS artifacts CASCADE;
        DROP TABLE IF EXISTS workspaces CASCADE;
        DROP TABLE IF EXISTS messages CASCADE;
        DROP TABLE IF EXISTS agent_sessions CASCADE;
        DROP TABLE IF EXISTS sessions CASCADE;
        DROP TABLE IF EXISTS agents CASCADE;
    """,
    dependencies=[],
    created_at=datetime.utcnow(),
)

PERFORMANCE_INDEXES_MIGRATION = MigrationScript(
    migration_id="002_performance_indexes",
    version="1.1.0",
    migration_type=MigrationType.INDEX_REBUILD,
    description="Add performance optimization indexes",
    up_sql="""
        -- Additional indexes for query performance
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_content_search
        ON messages USING gin(to_tsvector('english', content));

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_correlation_type
        ON events (correlation_id, event_type, timestamp);

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_composite
        ON metrics (metric_name, timestamp, agent_id);
    """,
    down_sql="""
        DROP INDEX IF EXISTS idx_messages_content_search;
        DROP INDEX IF EXISTS idx_events_correlation_type;
        DROP INDEX IF EXISTS idx_metrics_composite;
    """,
    dependencies=["001_initial_schema"],
    created_at=datetime.utcnow(),
)
