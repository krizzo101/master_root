"""
Dual-write adapter for migrating from SQLite to PostgreSQL.
Writes to both databases during migration period.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import psycopg2
from psycopg2.extras import Json


class DualWriteAdapter:
    """Adapter that writes to both SQLite and PostgreSQL during migration."""

    def __init__(
        self,
        sqlite_path: str = "/home/opsvi/master_root/chat_logs.db",
        postgres_url: str = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
    ):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url

        # SQLite connection
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        # PostgreSQL sync connection (for immediate use)
        self.pg_conn = psycopg2.connect(postgres_url)
        self.pg_conn.autocommit = True

        # Async pool for high-performance writes
        self.pg_pool = None

    async def init_async(self):
        """Initialize async PostgreSQL pool."""
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_url, min_size=5, max_size=20
        )

    def close(self):
        """Close all connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()

    async def close_async(self):
        """Close async connections."""
        if self.pg_pool:
            await self.pg_pool.close()

    # ============================================
    # Code Context Methods
    # ============================================

    def write_code_context(
        self,
        session_id: str,
        file_path: Optional[str],
        symbols: Dict[str, List[str]],
        content_hash: Optional[str] = None,
        change_type: Optional[str] = None,
        relevance_score: Optional[float] = None,
    ) -> int:
        """Write code context to both databases."""

        timestamp = datetime.now()

        # Write to SQLite (existing table structure)
        # Note: SQLite version might have different schema
        try:
            self.sqlite_conn.execute(
                """
                INSERT INTO code_context
                (session_id, timestamp, file_path, symbols, content_hash, change_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    timestamp.isoformat(),
                    file_path,
                    json.dumps(symbols),  # SQLite stores as TEXT
                    content_hash,
                    change_type,
                ),
            )
            self.sqlite_conn.commit()
        except sqlite3.OperationalError as e:
            print(f"SQLite write failed (table may not exist): {e}")

        # Write to PostgreSQL
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO code_context
                (session_id, timestamp, file_path, symbols, content_hash,
                 change_type, relevance_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    session_id,
                    timestamp,
                    file_path,
                    Json(symbols),  # PostgreSQL JSONB
                    content_hash,
                    change_type,
                    relevance_score,
                ),
            )
            pg_id = cursor.fetchone()[0]

        return pg_id

    # ============================================
    # Agent Usage Methods
    # ============================================

    def write_agent_usage(
        self,
        session_id: str,
        agent_class: str,
        agent_token: Optional[str],
        task_description: str,
        execution_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        success: bool = True,
        file_paths: Optional[List[str]] = None,
        methods_invoked: Optional[Dict] = None,
        context_data: Optional[Dict] = None,
    ) -> int:
        """Write agent usage to both databases."""

        timestamp = datetime.now()

        # Write to SQLite
        try:
            self.sqlite_conn.execute(
                """
                INSERT INTO agent_usage
                (session_id, timestamp, agent_class, agent_token, task_description,
                 execution_time_ms, tokens_used, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    timestamp.isoformat(),
                    agent_class,
                    agent_token,
                    task_description,
                    execution_time_ms,
                    tokens_used,
                    success,
                ),
            )
            self.sqlite_conn.commit()
        except sqlite3.OperationalError as e:
            print(f"SQLite write failed: {e}")

        # Write to PostgreSQL with full JSONB support
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agent_usage
                (session_id, timestamp, agent_class, agent_token, task_description,
                 execution_time_ms, tokens_used, success, file_paths,
                 methods_invoked, context_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    session_id,
                    timestamp,
                    agent_class,
                    agent_token,
                    task_description,
                    execution_time_ms,
                    tokens_used,
                    success,
                    file_paths,  # PostgreSQL array
                    Json(methods_invoked) if methods_invoked else None,
                    Json(context_data) if context_data else None,
                ),
            )
            pg_id = cursor.fetchone()[0]

        return pg_id

    # ============================================
    # Symbol References Methods
    # ============================================

    def write_symbol_reference(
        self,
        message_id: str,
        session_id: str,
        symbol_name: str,
        symbol_type: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        reference_type: str = "mentioned",
    ) -> int:
        """Write symbol reference to both databases."""

        timestamp = datetime.now()

        # Write to SQLite
        try:
            self.sqlite_conn.execute(
                """
                INSERT INTO symbol_references
                (message_id, session_id, symbol_name, symbol_type,
                 file_path, line_number, reference_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    session_id,
                    symbol_name,
                    symbol_type,
                    file_path,
                    line_number,
                    reference_type,
                ),
            )
            self.sqlite_conn.commit()
        except sqlite3.OperationalError as e:
            print(f"SQLite write failed: {e}")

        # Write to PostgreSQL
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO symbol_references
                (message_id, session_id, symbol_name, symbol_type,
                 file_path, line_number, reference_type, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    message_id,
                    session_id,
                    symbol_name,
                    symbol_type,
                    file_path,
                    line_number,
                    reference_type,
                    timestamp,
                ),
            )
            pg_id = cursor.fetchone()[0]

        return pg_id

    # ============================================
    # File Activity Methods
    # ============================================

    def write_file_activity(
        self,
        session_id: str,
        file_path: str,
        action: str,
        tool_used: str,
        functions_affected: Optional[List[str]] = None,
        classes_affected: Optional[List[str]] = None,
        before_hash: Optional[str] = None,
        after_hash: Optional[str] = None,
    ) -> int:
        """Write file activity to both databases."""

        timestamp = datetime.now()

        # Write to SQLite
        try:
            self.sqlite_conn.execute(
                """
                INSERT INTO file_activity
                (session_id, timestamp, file_path, action, tool_used,
                 functions_affected, classes_affected, before_hash, after_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    timestamp.isoformat(),
                    file_path,
                    action,
                    tool_used,
                    json.dumps(functions_affected) if functions_affected else None,
                    json.dumps(classes_affected) if classes_affected else None,
                    before_hash,
                    after_hash,
                ),
            )
            self.sqlite_conn.commit()
        except sqlite3.OperationalError as e:
            print(f"SQLite write failed: {e}")

        # Write to PostgreSQL
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO file_activity
                (session_id, timestamp, file_path, action, tool_used,
                 functions_affected, classes_affected, before_hash, after_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    session_id,
                    timestamp,
                    file_path,
                    action,
                    tool_used,
                    Json(functions_affected) if functions_affected else None,
                    Json(classes_affected) if classes_affected else None,
                    before_hash,
                    after_hash,
                ),
            )
            pg_id = cursor.fetchone()[0]

        return pg_id

    # ============================================
    # Async Batch Operations (High Performance)
    # ============================================

    async def batch_write_context_items(self, items: List[Dict[str, Any]]):
        """Batch write context items to PostgreSQL (async for performance)."""
        if not self.pg_pool:
            await self.init_async()

        async with self.pg_pool.acquire() as conn:
            # Use COPY for fastest insertion
            await conn.copy_records_to_table(
                "context_items",
                records=[
                    (
                        item["source_type"],
                        item["source_id"],
                        item["entity_type"],
                        item["timestamp"],
                        item.get("content"),
                        item.get("session_id"),
                        item.get("file_path"),
                        json.dumps(item.get("metrics", {})),
                        json.dumps(item.get("source_data", {})),
                    )
                    for item in items
                ],
                columns=[
                    "source_type",
                    "source_id",
                    "entity_type",
                    "timestamp",
                    "content",
                    "session_id",
                    "file_path",
                    "metrics",
                    "source_data",
                ],
            )

    # ============================================
    # Query Methods (Read from PostgreSQL)
    # ============================================

    def query_code_context(self, session_id: str) -> List[Dict]:
        """Query code context from PostgreSQL."""
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    cc.*,
                    ce.element_name,
                    ce.element_type as code_element_type
                FROM code_context cc
                LEFT JOIN code_elements ce ON cc.code_element_id = ce.id
                WHERE cc.session_id = %s
                ORDER BY cc.timestamp DESC
            """,
                (session_id,),
            )

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def query_hot_symbols(self, days: int = 7) -> List[Dict]:
        """Query hot symbols using PostgreSQL's superior aggregation."""
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    symbol_name,
                    symbol_type,
                    COUNT(*) as reference_count,
                    COUNT(DISTINCT session_id) as session_count,
                    COUNT(DISTINCT file_path) as file_count,
                    array_agg(DISTINCT reference_type) as reference_types
                FROM symbol_references
                WHERE timestamp > NOW() - INTERVAL '%s days'
                GROUP BY symbol_name, symbol_type
                ORDER BY reference_count DESC
                LIMIT 50
            """,
                (days,),
            )

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def query_with_jsonb(self, session_id: str) -> List[Dict]:
        """Example of PostgreSQL JSONB querying capabilities."""
        with self.pg_conn.cursor() as cursor:
            # Find all contexts where specific functions were discussed
            cursor.execute(
                """
                SELECT *
                FROM code_context
                WHERE session_id = %s
                  AND symbols @> '{"functions": ["process_data"]}'::jsonb
            """,
                (session_id,),
            )

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


# ============================================
# Test the dual-write adapter
# ============================================


def test_dual_write():
    """Test the dual-write functionality."""
    adapter = DualWriteAdapter()

    try:
        # Test writing code context
        context_id = adapter.write_code_context(
            session_id="test_session_001",
            file_path="/test/file.py",
            symbols={
                "functions": ["process_data", "validate_input"],
                "classes": ["DataProcessor"],
                "imports": ["pandas", "numpy"],
            },
            change_type="modify",
            relevance_score=0.85,
        )
        print(f"✓ Code context written with ID: {context_id}")

        # Test writing agent usage
        agent_id = adapter.write_agent_usage(
            session_id="test_session_001",
            agent_class="CodeAnalyzer",
            agent_token="analyzer_001",
            task_description="Analyze code complexity",
            execution_time_ms=1500,
            tokens_used=250,
            success=True,
            file_paths=["/test/file.py", "/test/utils.py"],
            methods_invoked={"analyze": 1, "report": 1},
            context_data={"complexity": "medium", "lines": 150},
        )
        print(f"✓ Agent usage written with ID: {agent_id}")

        # Test writing symbol reference
        symbol_id = adapter.write_symbol_reference(
            message_id="msg_001",
            session_id="test_session_001",
            symbol_name="DataProcessor",
            symbol_type="class",
            file_path="/test/file.py",
            line_number=45,
            reference_type="modified",
        )
        print(f"✓ Symbol reference written with ID: {symbol_id}")

        # Test writing file activity
        activity_id = adapter.write_file_activity(
            session_id="test_session_001",
            file_path="/test/file.py",
            action="modify",
            tool_used="Edit",
            functions_affected=["process_data"],
            classes_affected=["DataProcessor"],
            before_hash="abc123",
            after_hash="def456",
        )
        print(f"✓ File activity written with ID: {activity_id}")

        # Test querying
        contexts = adapter.query_code_context("test_session_001")
        print(f"✓ Found {len(contexts)} code contexts")

        hot_symbols = adapter.query_hot_symbols(days=30)
        print(f"✓ Found {len(hot_symbols)} hot symbols")

        print("\n✅ All dual-write tests passed!")

    finally:
        adapter.close()


if __name__ == "__main__":
    test_dual_write()
