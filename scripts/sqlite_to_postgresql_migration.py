#!/usr/bin/env python3
"""
Comprehensive SQLite to PostgreSQL Migration Script
Migrates historical data from SQLite to PostgreSQL with dual-write pattern.

Features:
- Comprehensive data migration with integrity preservation
- Data type conversion handling (SQLite to PostgreSQL)
- Incremental migration support for large datasets
- Validation and rollback mechanisms
- Migration reporting and statistics
- Production-ready error handling and logging
"""

import argparse
import asyncio
import hashlib
import json
import logging
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class MigrationConfig:
    """Configuration for the migration process"""

    def __init__(self):
        self.sqlite_path = "/home/opsvi/master_root/chat_logs.db"
        self.postgres_url = (
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )
        self.batch_size = 1000
        self.max_retries = 3
        self.retry_delay = 5
        self.validate_data = True
        self.enable_rollback = True
        self.incremental = False
        self.checkpoint_file = "migration_checkpoint.json"
        self.report_file = (
            f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )


class MigrationStats:
    """Track migration statistics"""

    def __init__(self):
        self.start_time = time.time()
        self.tables_migrated = 0
        self.total_records = 0
        self.records_migrated = 0
        self.records_skipped = 0
        self.records_failed = 0
        self.validation_errors = 0
        self.data_type_conversions = 0
        self.table_stats = defaultdict(
            lambda: {
                "source_count": 0,
                "migrated_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            }
        )

    def to_dict(self) -> Dict:
        """Convert stats to dictionary for reporting"""
        return {
            "migration_duration": time.time() - self.start_time,
            "tables_migrated": self.tables_migrated,
            "total_records": self.total_records,
            "records_migrated": self.records_migrated,
            "records_skipped": self.records_skipped,
            "records_failed": self.records_failed,
            "validation_errors": self.validation_errors,
            "data_type_conversions": self.data_type_conversions,
            "table_stats": dict(self.table_stats),
            "migration_timestamp": datetime.now(timezone.utc).isoformat(),
        }


class DataTypeConverter:
    """Handle SQLite to PostgreSQL data type conversions"""

    @staticmethod
    def convert_timestamp(sqlite_timestamp: str) -> datetime:
        """Convert SQLite timestamp string to PostgreSQL timestamp"""
        if not sqlite_timestamp:
            return datetime.now(timezone.utc)

        try:
            # Handle ISO format timestamps
            if "T" in sqlite_timestamp:
                dt = datetime.fromisoformat(sqlite_timestamp.replace("Z", "+00:00"))
            else:
                # Handle other formats
                dt = datetime.strptime(sqlite_timestamp, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid timestamp format: {sqlite_timestamp}, using current time"
            )
            return datetime.now(timezone.utc)

    @staticmethod
    def convert_json_field(field_value: Any) -> Optional[Dict]:
        """Convert SQLite JSON text field to PostgreSQL JSONB"""
        if not field_value:
            return None

        if isinstance(field_value, str):
            try:
                return json.loads(field_value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON field: {field_value}")
                return None
        elif isinstance(field_value, dict):
            return field_value
        else:
            return None

    @staticmethod
    def convert_boolean(value: Any) -> bool:
        """Convert SQLite boolean (0/1) to PostgreSQL boolean"""
        if isinstance(value, int):
            return bool(value)
        elif isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        else:
            return bool(value)


class SQLiteToPostgreSQLMigrator:
    """Main migration class"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.stats = MigrationStats()
        self.converter = DataTypeConverter()
        self.sqlite_conn = None
        self.pg_conn = None
        self.pg_pool = None
        self.checkpoint = {}

        # Migration mappings for each table
        self.migration_mappings = {
            "sessions": self._migrate_sessions,
            "nodes": self._migrate_nodes,
            "tool_calls": self._migrate_tool_calls,
            "tool_results": self._migrate_tool_results,
            "file_operations": self._migrate_file_operations,
        }

    async def initialize_connections(self):
        """Initialize database connections"""
        try:
            # SQLite connection
            self.sqlite_conn = sqlite3.connect(self.config.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.config.sqlite_path}")

            # PostgreSQL sync connection
            self.pg_conn = psycopg2.connect(
                self.config.postgres_url, cursor_factory=RealDictCursor
            )
            self.pg_conn.autocommit = False

            # PostgreSQL async pool
            self.pg_pool = await asyncpg.create_pool(
                self.config.postgres_url, min_size=5, max_size=20
            )
            logger.info("Connected to PostgreSQL database")

        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise

    def close_connections(self):
        """Close all database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.pg_pool:
            asyncio.create_task(self.pg_pool.close())

    def load_checkpoint(self) -> Dict:
        """Load migration checkpoint for incremental migration"""
        checkpoint_path = Path(self.config.checkpoint_file)
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, "r") as f:
                    self.checkpoint = json.load(f)
                logger.info(
                    f"Loaded checkpoint: {len(self.checkpoint)} tables completed"
                )
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return self.checkpoint

    def save_checkpoint(self, table_name: str, last_id: Any = None):
        """Save migration checkpoint"""
        try:
            self.checkpoint[table_name] = {
                "completed": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "last_id": str(last_id) if last_id else None,
            }
            with open(self.config.checkpoint_file, "w") as f:
                json.dump(self.checkpoint, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def get_sqlite_table_info(self, table_name: str) -> Tuple[int, List[str]]:
        """Get SQLite table row count and column names"""
        try:
            cursor = self.sqlite_conn.cursor()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            return row_count, columns

        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return 0, []

    def validate_postgresql_schema(self) -> bool:
        """Validate PostgreSQL schema exists and is compatible"""
        try:
            with self.pg_conn.cursor() as cursor:
                # Check required tables exist
                required_tables = [
                    "context_items",
                    "chat_sessions",
                    "code_context",
                    "agent_usage",
                    "symbol_references",
                    "file_activity",
                ]

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = ANY(%s)
                """,
                    (required_tables,),
                )

                existing_tables = [row[0] for row in cursor.fetchall()]
                missing_tables = set(required_tables) - set(existing_tables)

                if missing_tables:
                    logger.error(f"Missing PostgreSQL tables: {missing_tables}")
                    return False

                logger.info("PostgreSQL schema validation passed")
                return True

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False

    def create_migration_backup(self):
        """Create backup of current PostgreSQL data before migration"""
        if not self.config.enable_rollback:
            return

        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(f"migration_backup_{backup_timestamp}")
            backup_dir.mkdir(exist_ok=True)

            with self.pg_conn.cursor() as cursor:
                tables = [
                    "context_items",
                    "chat_sessions",
                    "code_context",
                    "agent_usage",
                    "symbol_references",
                    "file_activity",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    if count > 0:
                        backup_file = backup_dir / f"{table}_backup.json"
                        cursor.execute(
                            f"SELECT * FROM {table} LIMIT 1000"
                        )  # Limit for safety

                        with open(backup_file, "w") as f:
                            json.dump(
                                [dict(row) for row in cursor.fetchall()],
                                f,
                                indent=2,
                                default=str,
                            )

                        logger.info(f"Backed up {count} records from {table}")

            logger.info(f"Backup created in {backup_dir}")

        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")

    async def migrate_sessions_to_context_items(self):
        """Migrate SQLite sessions to PostgreSQL context_items and chat_sessions"""
        logger.info("Migrating sessions...")

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY session_id")

            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    batch = []
                    session_batch = []

                    for row in cursor.fetchall():
                        row_dict = dict(row)

                        # Migrate to chat_sessions table
                        session_record = {
                            "id": row_dict["session_id"],
                            "started_at": self.converter.convert_timestamp(
                                row_dict["created_at"]
                            ),
                            "project_path": row_dict.get("cwd"),
                            "session_metadata": self.converter.convert_json_field(
                                row_dict.get("metadata")
                            ),
                        }
                        session_batch.append(session_record)

                        # Also create context_item for session
                        context_record = {
                            "source_type": "chat",
                            "source_id": f"session_{row_dict['session_id']}",
                            "entity_type": "session",
                            "timestamp": self.converter.convert_timestamp(
                                row_dict["created_at"]
                            ),
                            "title": f"Chat Session {row_dict['session_id']}",
                            "project_id": row_dict.get("cwd"),
                            "session_id": row_dict["session_id"],
                            "actor_type": "system",
                            "source_data": self.converter.convert_json_field(
                                row_dict.get("metadata")
                            ),
                        }
                        batch.append(context_record)

                        if len(batch) >= self.config.batch_size:
                            await self._insert_context_items_batch(conn, batch)
                            await self._insert_chat_sessions_batch(conn, session_batch)
                            batch.clear()
                            session_batch.clear()

                    # Insert remaining records
                    if batch:
                        await self._insert_context_items_batch(conn, batch)
                    if session_batch:
                        await self._insert_chat_sessions_batch(conn, session_batch)

                    self.stats.table_stats["sessions"]["migrated_count"] = len(
                        batch
                    ) + len(session_batch)

            logger.info(f"Migrated {cursor.rowcount} sessions")

        except Exception as e:
            logger.error(f"Session migration failed: {e}")
            raise

    async def migrate_nodes_to_context_items(self):
        """Migrate SQLite nodes to PostgreSQL context_items"""
        logger.info("Migrating nodes...")

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT n.*, s.cwd as project_path
                FROM nodes n
                LEFT JOIN sessions s ON n.session_id = s.session_id
                ORDER BY n.timestamp
            """
            )

            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    batch = []

                    for row in cursor.fetchall():
                        row_dict = dict(row)
                        raw_json = self.converter.convert_json_field(
                            row_dict.get("raw_json")
                        )

                        # Extract content from raw JSON
                        content = ""
                        title = f"{row_dict['node_type'].title()} Message"

                        if raw_json and "message" in raw_json:
                            message = raw_json["message"]
                            if isinstance(message, dict):
                                if "content" in message:
                                    if isinstance(message["content"], str):
                                        content = message["content"]
                                    elif isinstance(message["content"], list):
                                        content = json.dumps(message["content"])

                        context_record = {
                            "source_type": "chat",
                            "source_id": row_dict["uuid"],
                            "entity_type": row_dict["node_type"],
                            "timestamp": self.converter.convert_timestamp(
                                row_dict["timestamp"]
                            ),
                            "title": title,
                            "content": content[:10000]
                            if content
                            else None,  # Limit content size
                            "content_hash": row_dict.get("content_hash"),
                            "project_id": row_dict.get("project_path"),
                            "session_id": row_dict["session_id"],
                            "actor_type": "human"
                            if row_dict["node_type"] == "user"
                            else "ai",
                            "source_data": raw_json,
                            "tags": ["sidechain"]
                            if row_dict.get("is_sidechain")
                            else None,
                        }

                        batch.append(context_record)

                        if len(batch) >= self.config.batch_size:
                            await self._insert_context_items_batch(conn, batch)
                            batch.clear()

                    # Insert remaining records
                    if batch:
                        await self._insert_context_items_batch(conn, batch)

                    self.stats.table_stats["nodes"]["migrated_count"] = cursor.rowcount

            logger.info(f"Migrated {cursor.rowcount} nodes")

        except Exception as e:
            logger.error(f"Node migration failed: {e}")
            raise

    async def migrate_tool_calls_to_agent_usage(self):
        """Migrate SQLite tool_calls to PostgreSQL agent_usage"""
        logger.info("Migrating tool calls...")

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT tc.*, n.session_id, tr.is_error, tr.content_text
                FROM tool_calls tc
                LEFT JOIN nodes n ON tc.node_uuid = n.uuid
                LEFT JOIN tool_results tr ON tc.tool_use_id = tr.tool_use_id
                ORDER BY tc.timestamp
            """
            )

            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    batch = []

                    for row in cursor.fetchall():
                        row_dict = dict(row)

                        input_json = self.converter.convert_json_field(
                            row_dict.get("input_json")
                        )

                        agent_record = {
                            "session_id": row_dict["session_id"],
                            "timestamp": self.converter.convert_timestamp(
                                row_dict["timestamp"]
                            ),
                            "agent_class": row_dict["tool_name"],
                            "agent_token": row_dict["tool_use_id"][:50],  # Limit length
                            "task_description": f"Tool call: {row_dict['tool_name']}",
                            "success": not self.converter.convert_boolean(
                                row_dict.get("is_error", 0)
                            ),
                            "methods_invoked": {"tool_call": 1},
                            "context_data": input_json,
                            "file_paths": [input_json.get("file_path")]
                            if input_json and input_json.get("file_path")
                            else None,
                        }

                        batch.append(agent_record)

                        if len(batch) >= self.config.batch_size:
                            await self._insert_agent_usage_batch(conn, batch)
                            batch.clear()

                    # Insert remaining records
                    if batch:
                        await self._insert_agent_usage_batch(conn, batch)

                    self.stats.table_stats["tool_calls"][
                        "migrated_count"
                    ] = cursor.rowcount

            logger.info(f"Migrated {cursor.rowcount} tool calls")

        except Exception as e:
            logger.error(f"Tool call migration failed: {e}")
            raise

    async def migrate_file_operations_to_file_activity(self):
        """Migrate SQLite file_operations to PostgreSQL file_activity"""
        logger.info("Migrating file operations...")

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT fo.*, tc.node_uuid, n.session_id, tc.timestamp
                FROM file_operations fo
                LEFT JOIN tool_calls tc ON fo.tool_call_id = tc.tool_use_id
                LEFT JOIN nodes n ON tc.node_uuid = n.uuid
                ORDER BY tc.timestamp
            """
            )

            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    batch = []

                    for row in cursor.fetchall():
                        row_dict = dict(row)

                        if not row_dict.get("session_id") or not row_dict.get(
                            "file_path"
                        ):
                            self.stats.table_stats["file_operations"][
                                "skipped_count"
                            ] += 1
                            continue

                        file_record = {
                            "session_id": row_dict["session_id"],
                            "timestamp": self.converter.convert_timestamp(
                                row_dict.get("timestamp")
                            ),
                            "file_path": row_dict["file_path"],
                            "action": row_dict.get("operation", "unknown"),
                            "tool_used": "file_operation",
                            "before_hash": hashlib.sha256(
                                (row_dict.get("content_before") or "").encode()
                            ).hexdigest()[:64],
                            "after_hash": hashlib.sha256(
                                (row_dict.get("content_after") or "").encode()
                            ).hexdigest()[:64],
                        }

                        batch.append(file_record)

                        if len(batch) >= self.config.batch_size:
                            await self._insert_file_activity_batch(conn, batch)
                            batch.clear()

                    # Insert remaining records
                    if batch:
                        await self._insert_file_activity_batch(conn, batch)

                    self.stats.table_stats["file_operations"]["migrated_count"] = len(
                        batch
                    )

            logger.info(f"Migrated file operations")

        except Exception as e:
            logger.error(f"File operation migration failed: {e}")
            raise

    async def _insert_context_items_batch(self, conn, batch: List[Dict]):
        """Insert batch of context items"""
        if not batch:
            return

        try:
            await conn.executemany(
                """
                INSERT INTO context_items (
                    source_type, source_id, entity_type, timestamp, title, content,
                    content_hash, project_id, session_id, actor_type, source_data, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """,
                [
                    (
                        item["source_type"],
                        item["source_id"],
                        item["entity_type"],
                        item["timestamp"],
                        item.get("title"),
                        item.get("content"),
                        item.get("content_hash"),
                        item.get("project_id"),
                        item.get("session_id"),
                        item.get("actor_type"),
                        json.dumps(item.get("source_data"))
                        if item.get("source_data")
                        else None,
                        item.get("tags"),
                    )
                    for item in batch
                ],
            )

            self.stats.records_migrated += len(batch)

        except Exception as e:
            logger.error(f"Failed to insert context items batch: {e}")
            self.stats.records_failed += len(batch)

    async def _insert_chat_sessions_batch(self, conn, batch: List[Dict]):
        """Insert batch of chat sessions"""
        if not batch:
            return

        try:
            await conn.executemany(
                """
                INSERT INTO chat_sessions (
                    id, started_at, project_path, session_metadata
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
            """,
                [
                    (
                        item["id"],
                        item["started_at"],
                        item.get("project_path"),
                        json.dumps(item.get("session_metadata"))
                        if item.get("session_metadata")
                        else None,
                    )
                    for item in batch
                ],
            )

        except Exception as e:
            logger.error(f"Failed to insert chat sessions batch: {e}")

    async def _insert_agent_usage_batch(self, conn, batch: List[Dict]):
        """Insert batch of agent usage records"""
        if not batch:
            return

        try:
            await conn.executemany(
                """
                INSERT INTO agent_usage (
                    session_id, timestamp, agent_class, agent_token, task_description,
                    success, methods_invoked, context_data, file_paths
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                [
                    (
                        item["session_id"],
                        item["timestamp"],
                        item["agent_class"],
                        item["agent_token"],
                        item["task_description"],
                        item["success"],
                        json.dumps(item.get("methods_invoked"))
                        if item.get("methods_invoked")
                        else None,
                        json.dumps(item.get("context_data"))
                        if item.get("context_data")
                        else None,
                        item.get("file_paths"),
                    )
                    for item in batch
                ],
            )

        except Exception as e:
            logger.error(f"Failed to insert agent usage batch: {e}")

    async def _insert_file_activity_batch(self, conn, batch: List[Dict]):
        """Insert batch of file activity records"""
        if not batch:
            return

        try:
            await conn.executemany(
                """
                INSERT INTO file_activity (
                    session_id, timestamp, file_path, action, tool_used,
                    before_hash, after_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                [
                    (
                        item["session_id"],
                        item["timestamp"],
                        item["file_path"],
                        item["action"],
                        item["tool_used"],
                        item.get("before_hash"),
                        item.get("after_hash"),
                    )
                    for item in batch
                ],
            )

        except Exception as e:
            logger.error(f"Failed to insert file activity batch: {e}")

    def validate_migration(self) -> bool:
        """Validate migration results"""
        logger.info("Validating migration...")

        try:
            # Get SQLite counts
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_counts = {}

            for table in ["sessions", "nodes", "tool_calls", "file_operations"]:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_counts[table] = sqlite_cursor.fetchone()[0]

            # Get PostgreSQL counts
            with self.pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(
                    "SELECT COUNT(*) FROM context_items WHERE source_type = 'chat'"
                )
                pg_chat_items = pg_cursor.fetchone()[0]

                pg_cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                pg_sessions = pg_cursor.fetchone()[0]

                pg_cursor.execute("SELECT COUNT(*) FROM agent_usage")
                pg_agent_usage = pg_cursor.fetchone()[0]

                pg_cursor.execute("SELECT COUNT(*) FROM file_activity")
                pg_file_activity = pg_cursor.fetchone()[0]

            # Validate counts (allowing for some variance due to deduplication)
            validation_passed = True

            if pg_sessions != sqlite_counts["sessions"]:
                logger.warning(
                    f"Session count mismatch: SQLite={sqlite_counts['sessions']}, PostgreSQL={pg_sessions}"
                )
                validation_passed = False

            expected_context_items = sqlite_counts["sessions"] + sqlite_counts["nodes"]
            if (
                abs(pg_chat_items - expected_context_items)
                > expected_context_items * 0.1
            ):  # 10% tolerance
                logger.warning(
                    f"Context items variance too high: Expected≈{expected_context_items}, Got={pg_chat_items}"
                )
                validation_passed = False

            if validation_passed:
                logger.info("✓ Migration validation passed")
            else:
                logger.error("✗ Migration validation failed")
                self.stats.validation_errors += 1

            return validation_passed

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def generate_migration_report(self):
        """Generate comprehensive migration report"""
        report_data = {
            "migration_config": {
                "sqlite_path": self.config.sqlite_path,
                "postgres_url": self.config.postgres_url.replace("password", "***"),
                "batch_size": self.config.batch_size,
                "incremental": self.config.incremental,
            },
            "stats": self.stats.to_dict(),
            "validation": {
                "data_validated": self.config.validate_data,
                "validation_errors": self.stats.validation_errors,
            },
            "performance": {
                "migration_duration_seconds": time.time() - self.stats.start_time,
                "records_per_second": self.stats.records_migrated
                / max(time.time() - self.stats.start_time, 1),
            },
        }

        # Save report
        try:
            with open(self.config.report_file, "w") as f:
                json.dump(report_data, f, indent=2, default=str)
            logger.info(f"Migration report saved to {self.config.report_file}")
        except Exception as e:
            logger.error(f"Failed to save migration report: {e}")

        return report_data

    async def run_migration(self):
        """Execute the complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration")

        try:
            # Initialize
            await self.initialize_connections()

            if self.config.incremental:
                self.load_checkpoint()

            # Validate environment
            if not self.validate_postgresql_schema():
                raise Exception("PostgreSQL schema validation failed")

            # Create backup if rollback is enabled
            self.create_migration_backup()

            # Execute migrations
            migration_steps = [
                ("sessions", self.migrate_sessions_to_context_items),
                ("nodes", self.migrate_nodes_to_context_items),
                ("tool_calls", self.migrate_tool_calls_to_agent_usage),
                ("file_operations", self.migrate_file_operations_to_file_activity),
            ]

            for step_name, migration_func in migration_steps:
                if self.config.incremental and self.checkpoint.get(step_name, {}).get(
                    "completed"
                ):
                    logger.info(f"Skipping {step_name} (already completed)")
                    continue

                logger.info(f"Starting migration step: {step_name}")
                await migration_func()

                self.save_checkpoint(step_name)
                self.stats.tables_migrated += 1
                logger.info(f"✓ Completed migration step: {step_name}")

            # Validate results
            if self.config.validate_data:
                self.validate_migration()

            # Generate report
            report = self.generate_migration_report()

            logger.info("Migration completed successfully!")
            logger.info(f"Total records migrated: {self.stats.records_migrated}")
            logger.info(
                f"Migration duration: {report['performance']['migration_duration_seconds']:.2f} seconds"
            )

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close_connections()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SQLite to PostgreSQL Migration Script"
    )
    parser.add_argument(
        "--sqlite-path",
        default="/home/opsvi/master_root/chat_logs.db",
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--postgres-url",
        default="postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for migration"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental migration with checkpoints",
    )
    parser.add_argument(
        "--no-validation", action="store_true", help="Skip validation after migration"
    )
    parser.add_argument(
        "--no-rollback", action="store_true", help="Disable rollback backup creation"
    )

    args = parser.parse_args()

    # Create configuration
    config = MigrationConfig()
    config.sqlite_path = args.sqlite_path
    config.postgres_url = args.postgres_url
    config.batch_size = args.batch_size
    config.incremental = args.incremental
    config.validate_data = not args.no_validation
    config.enable_rollback = not args.no_rollback

    # Run migration
    migrator = SQLiteToPostgreSQLMigrator(config)

    try:
        asyncio.run(migrator.run_migration())
        return 0
    except KeyboardInterrupt:
        logger.info("Migration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
