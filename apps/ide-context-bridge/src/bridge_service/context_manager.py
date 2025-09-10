#!/usr/bin/env python3
"""
Context Manager for IDE Context Bridge

Manages IDE context state, persistence, and integration with the unified context system.
"""

import asyncio
import json
import logging

# Import from the project context integration
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import redis.asyncio as redis

project_context_path = (
    Path(__file__).parent.parent.parent.parent / "project-context" / "src"
)
sys.path.insert(0, str(project_context_path))

try:
    from project_context.integrations.context_bridge import IDEContext, context_bridge
except ImportError:
    # Fallback: define IDEContext locally if project-context isn't available
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Any, Dict, List, Optional

    @dataclass
    class IDEContext:
        """Fallback IDEContext definition."""

        active_file: Optional[str] = None
        cursor_position: Optional[Dict[str, int]] = None
        selection: Optional[Dict[str, Any]] = None
        open_files: List[str] = None
        project_root: Optional[str] = None
        workspace_folders: List[str] = None
        language: Optional[str] = None
        git_branch: Optional[str] = None
        last_updated: Optional[datetime] = None

        def __post_init__(self):
            if self.open_files is None:
                self.open_files = []
            if self.workspace_folders is None:
                self.workspace_folders = []
            if self.last_updated is None:
                self.last_updated = datetime.now()

    # Mock context bridge for fallback
    class MockContextBridge:
        async def initialize(self):
            return True

        async def set_context(self, context):
            pass

    context_bridge = MockContextBridge()

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages IDE context capture, persistence, and integration.

    Responsibilities:
    - Capture and validate IDE context from multiple sources
    - Persist context to PostgreSQL and cache in Redis
    - Integrate with unified context system
    - Provide context querying and retrieval
    - Track session state and history
    """

    def __init__(self, postgres_url: str, redis_client: Optional[redis.Redis] = None):
        """Initialize context manager."""
        self.postgres_url = postgres_url
        self.redis_client = redis_client
        self.db_pool: Optional[asyncpg.Pool] = None

        # Context storage
        self.active_contexts: Dict[str, IDEContext] = {}
        self.session_history: Dict[str, List[Dict[str, Any]]] = {}

        # Performance tracking
        self.context_updates = 0
        self.last_cleanup = datetime.now()

    async def initialize(self):
        """Initialize database connections and context bridge."""
        try:
            # Initialize PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                self.postgres_url, min_size=5, max_size=20, command_timeout=60
            )

            # Test connection
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            logger.info("PostgreSQL connection pool initialized")

            # Initialize context bridge integration
            await context_bridge.initialize()
            logger.info("Context bridge integration initialized")

            # Start background tasks
            asyncio.create_task(self._cleanup_task())
            logger.info("Context manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize context manager: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        if self.db_pool:
            await self.db_pool.close()
        logger.info("Context manager cleanup complete")

    async def update_context(
        self, session_id: str, context_data: Dict[str, Any]
    ) -> bool:
        """
        Update IDE context for a session.

        Args:
            session_id: Unique session identifier
            context_data: Context data from IDE

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Parse and validate context data
            ide_context = self._parse_context_data(context_data)

            # Update active contexts
            self.active_contexts[session_id] = ide_context

            # Track in session history
            if session_id not in self.session_history:
                self.session_history[session_id] = []

            self.session_history[session_id].append(
                {
                    "timestamp": datetime.now(),
                    "context": asdict(ide_context),
                    "update_type": context_data.get("type", "context_update"),
                }
            )

            # Persist to database
            await self._persist_context(session_id, ide_context, context_data)

            # Cache in Redis if available
            if self.redis_client:
                await self._cache_context(session_id, ide_context)

            # Integrate with context bridge
            await context_bridge.set_context(ide_context)

            # Update context items table
            await self._update_context_items(session_id, ide_context, context_data)

            self.context_updates += 1
            logger.debug(f"Context updated for session {session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to update context for session {session_id}: {e}")
            return False

    async def get_context(self, session_id: str) -> Optional[IDEContext]:
        """
        Get current IDE context for a session.

        Args:
            session_id: Session identifier

        Returns:
            IDE context or None if not found
        """
        try:
            # Check active contexts first
            if session_id in self.active_contexts:
                return self.active_contexts[session_id]

            # Try Redis cache
            if self.redis_client:
                cached_context = await self._get_cached_context(session_id)
                if cached_context:
                    self.active_contexts[session_id] = cached_context
                    return cached_context

            # Fallback to database
            context = await self._load_context_from_db(session_id)
            if context:
                self.active_contexts[session_id] = context

            return context

        except Exception as e:
            logger.error(f"Failed to get context for session {session_id}: {e}")
            return None

    async def get_session_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get context update history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of history entries

        Returns:
            List of context history entries
        """
        try:
            # Get from memory first
            if session_id in self.session_history:
                history = self.session_history[session_id][-limit:]
                if (
                    len(history) == limit
                    or len(self.session_history[session_id]) < limit
                ):
                    return history

            # Load from database if needed
            db_history = await self._load_session_history(session_id, limit)

            # Merge with memory history
            if session_id in self.session_history:
                memory_history = self.session_history[session_id]
                # Combine and deduplicate
                all_history = db_history + memory_history
                unique_history = []
                seen_timestamps = set()

                for entry in reversed(all_history):
                    timestamp_str = (
                        entry["timestamp"].isoformat()
                        if isinstance(entry["timestamp"], datetime)
                        else entry["timestamp"]
                    )
                    if timestamp_str not in seen_timestamps:
                        seen_timestamps.add(timestamp_str)
                        unique_history.append(entry)

                return list(reversed(unique_history))[-limit:]

            return db_history

        except Exception as e:
            logger.error(f"Failed to get session history for {session_id}: {e}")
            return []

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get information about all active sessions.

        Returns:
            List of active session information
        """
        sessions = []
        current_time = datetime.now()

        for session_id, context in self.active_contexts.items():
            # Calculate session age
            last_update = context.last_updated or current_time
            age_minutes = (current_time - last_update).total_seconds() / 60

            sessions.append(
                {
                    "session_id": session_id,
                    "active_file": context.active_file,
                    "project_root": context.project_root,
                    "language": context.language,
                    "open_files_count": len(context.open_files or []),
                    "last_update": last_update,
                    "age_minutes": age_minutes,
                    "git_branch": context.git_branch,
                }
            )

        return sorted(sessions, key=lambda x: x["last_update"], reverse=True)

    async def search_context_history(
        self,
        query: str,
        session_id: Optional[str] = None,
        file_path: Optional[str] = None,
        time_range: Optional[tuple] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search through context history.

        Args:
            query: Search query
            session_id: Optional session filter
            file_path: Optional file filter
            time_range: Optional (start_time, end_time) filter
            limit: Maximum results

        Returns:
            List of matching context entries
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build dynamic query
                conditions = ["search_vector @@ plainto_tsquery('english', $1)"]
                params = [query]
                param_count = 1

                if session_id:
                    param_count += 1
                    conditions.append(f"session_id = ${param_count}")
                    params.append(session_id)

                if file_path:
                    param_count += 1
                    conditions.append(f"active_file ILIKE ${param_count}")
                    params.append(f"%{file_path}%")

                if time_range:
                    param_count += 1
                    conditions.append(f"timestamp >= ${param_count}")
                    params.append(time_range[0])

                    param_count += 1
                    conditions.append(f"timestamp <= ${param_count}")
                    params.append(time_range[1])

                query_sql = f"""
                    SELECT *,
                           ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
                    FROM ide_context_snapshots
                    WHERE {' AND '.join(conditions)}
                    ORDER BY rank DESC, timestamp DESC
                    LIMIT ${param_count + 1}
                """
                params.append(limit)

                rows = await conn.fetch(query_sql, *params)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Context history search failed: {e}")
            return []

    def _parse_context_data(self, context_data: Dict[str, Any]) -> IDEContext:
        """Parse raw context data into IDEContext object."""
        try:
            # Extract core fields
            active_file = None
            if context_data.get("active_file"):
                active_file = context_data["active_file"]["path"]

            cursor_position = None
            if context_data.get("cursor_position"):
                cursor_position = {
                    "line": context_data["cursor_position"]["line"],
                    "column": context_data["cursor_position"]["column"],
                }

            selection = None
            if context_data.get("selection"):
                selection = {
                    "start": context_data["selection"]["start"],
                    "end": context_data["selection"]["end"],
                    "text": context_data["selection"]["text"],
                }

            # Extract file lists
            open_files = []
            if context_data.get("open_files"):
                open_files = [f["path"] for f in context_data["open_files"]]

            workspace_folders = []
            if context_data.get("workspace"):
                workspace_folders = context_data["workspace"].get("folders", [])

            # Extract other fields
            project_root = None
            if context_data.get("workspace"):
                project_root = context_data["workspace"].get("root_path")

            language = None
            if context_data.get("active_file"):
                language = context_data["active_file"].get("language")

            git_branch = None
            if context_data.get("git_info"):
                git_branch = context_data["git_info"].get("branch")

            return IDEContext(
                active_file=active_file,
                cursor_position=cursor_position,
                selection=selection,
                open_files=open_files,
                project_root=project_root,
                workspace_folders=workspace_folders,
                language=language,
                git_branch=git_branch,
                last_updated=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Failed to parse context data: {e}")
            raise

    async def _persist_context(
        self, session_id: str, ide_context: IDEContext, raw_data: Dict[str, Any]
    ):
        """Persist context to database."""
        try:
            async with self.db_pool.acquire() as conn:
                # Build search vector from context
                search_text_parts = []

                if ide_context.active_file:
                    search_text_parts.append(ide_context.active_file)

                if ide_context.project_root:
                    search_text_parts.append(ide_context.project_root)

                if ide_context.language:
                    search_text_parts.append(ide_context.language)

                if raw_data.get("selection", {}).get("text"):
                    search_text_parts.append(raw_data["selection"]["text"])

                search_text = " ".join(search_text_parts)

                # Extract diagnostics
                error_count = 0
                warning_count = 0
                diagnostics_json = {}

                if raw_data.get("diagnostics"):
                    diagnostics_json = {"diagnostics": raw_data["diagnostics"]}
                    for diag in raw_data["diagnostics"]:
                        if diag["severity"] == "error":
                            error_count += 1
                        elif diag["severity"] == "warning":
                            warning_count += 1

                # Insert into ide_context_snapshots
                await conn.execute(
                    """
                    INSERT INTO ide_context_snapshots (
                        timestamp, active_file, selected_text, cursor_position,
                        error_count, warning_count, diagnostics,
                        project_root, open_files, recent_files, session_id, search_vector
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                        to_tsvector('english', $12)
                    )
                """,
                    datetime.now(),
                    ide_context.active_file,
                    raw_data.get("selection", {}).get("text"),
                    json.dumps(ide_context.cursor_position)
                    if ide_context.cursor_position
                    else None,
                    error_count,
                    warning_count,
                    json.dumps(diagnostics_json) if diagnostics_json else None,
                    ide_context.project_root,
                    ide_context.open_files,
                    ide_context.open_files[:10],  # Recent files (last 10)
                    session_id,
                    search_text,
                )

        except Exception as e:
            logger.error(f"Failed to persist context: {e}")
            raise

    async def _update_context_items(
        self, session_id: str, ide_context: IDEContext, raw_data: Dict[str, Any]
    ):
        """Update context_items table with IDE context."""
        try:
            async with self.db_pool.acquire() as conn:
                # Create context item for this IDE update
                content_parts = []

                if ide_context.active_file:
                    content_parts.append(f"Active file: {ide_context.active_file}")

                if ide_context.language:
                    content_parts.append(f"Language: {ide_context.language}")

                if raw_data.get("selection", {}).get("text"):
                    content_parts.append(
                        f"Selected text: {raw_data['selection']['text'][:200]}..."
                    )

                if raw_data.get("diagnostics"):
                    error_count = sum(
                        1 for d in raw_data["diagnostics"] if d["severity"] == "error"
                    )
                    if error_count > 0:
                        content_parts.append(f"Errors: {error_count}")

                content = " | ".join(content_parts)

                # Prepare metadata
                metadata = {
                    "cursor_position": ide_context.cursor_position,
                    "open_files_count": len(ide_context.open_files or []),
                    "diagnostics_count": len(raw_data.get("diagnostics", [])),
                    "git_branch": ide_context.git_branch,
                    "editor_id": raw_data.get("editor_id"),
                }

                # Insert into context_items
                await conn.execute(
                    """
                    INSERT INTO context_items (
                        source_type, source_id, entity_type,
                        timestamp, title, content,
                        project_id, file_path, actor_id, session_id,
                        metrics, search_vector
                    ) VALUES (
                        'ide', $1, 'context_snapshot',
                        $2, $3, $4,
                        $5, $6, $7, $8,
                        $9, to_tsvector('english', $10)
                    )
                    ON CONFLICT (source_type, source_id)
                    DO UPDATE SET
                        timestamp = EXCLUDED.timestamp,
                        content = EXCLUDED.content,
                        metrics = EXCLUDED.metrics,
                        search_vector = EXCLUDED.search_vector
                """,
                    f"ide_context_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    datetime.now(),
                    f"IDE Context - {ide_context.active_file or 'No active file'}",
                    content,
                    ide_context.project_root,
                    ide_context.active_file,
                    f"ide_session_{session_id}",
                    session_id,
                    json.dumps(metadata),
                    content,
                )

        except Exception as e:
            logger.error(f"Failed to update context_items: {e}")
            # Non-critical error, don't raise

    async def _cache_context(self, session_id: str, ide_context: IDEContext):
        """Cache context in Redis."""
        try:
            if not self.redis_client:
                return

            # Serialize context
            context_dict = asdict(ide_context)
            if context_dict.get("last_updated"):
                context_dict["last_updated"] = context_dict["last_updated"].isoformat()

            # Cache with expiry (1 hour)
            await self.redis_client.setex(
                f"ide_context:{session_id}", 3600, json.dumps(context_dict)
            )

        except Exception as e:
            logger.error(f"Failed to cache context: {e}")

    async def _get_cached_context(self, session_id: str) -> Optional[IDEContext]:
        """Get cached context from Redis."""
        try:
            if not self.redis_client:
                return None

            cached_data = await self.redis_client.get(f"ide_context:{session_id}")
            if not cached_data:
                return None

            context_dict = json.loads(cached_data)

            # Convert timestamp back
            if context_dict.get("last_updated"):
                context_dict["last_updated"] = datetime.fromisoformat(
                    context_dict["last_updated"]
                )

            return IDEContext(**context_dict)

        except Exception as e:
            logger.error(f"Failed to get cached context: {e}")
            return None

    async def _load_context_from_db(self, session_id: str) -> Optional[IDEContext]:
        """Load latest context from database."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM ide_context_snapshots
                    WHERE session_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                """,
                    session_id,
                )

                if not row:
                    return None

                # Convert to IDEContext
                cursor_position = None
                if row["cursor_position"]:
                    cursor_position = json.loads(row["cursor_position"])

                return IDEContext(
                    active_file=row["active_file"],
                    cursor_position=cursor_position,
                    selection=None,  # Not stored in snapshots
                    open_files=row["open_files"] or [],
                    project_root=row["project_root"],
                    workspace_folders=[],  # Not stored in snapshots
                    language=None,  # Could be derived from file extension
                    git_branch=None,  # Not stored in snapshots
                    last_updated=row["timestamp"],
                )

        except Exception as e:
            logger.error(f"Failed to load context from DB: {e}")
            return None

    async def _load_session_history(
        self, session_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Load session history from database."""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM ide_context_snapshots
                    WHERE session_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """,
                    session_id,
                    limit,
                )

                history = []
                for row in rows:
                    history.append(
                        {
                            "timestamp": row["timestamp"],
                            "context": {
                                "active_file": row["active_file"],
                                "project_root": row["project_root"],
                                "cursor_position": json.loads(row["cursor_position"])
                                if row["cursor_position"]
                                else None,
                                "error_count": row["error_count"],
                                "warning_count": row["warning_count"],
                            },
                            "update_type": "context_update",
                        }
                    )

                return list(reversed(history))  # Return chronological order

        except Exception as e:
            logger.error(f"Failed to load session history: {e}")
            return []

    async def _cleanup_task(self):
        """Background task to clean up stale contexts."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.now()
                stale_sessions = []

                # Find stale sessions (no update in last hour)
                for session_id, context in self.active_contexts.items():
                    if context.last_updated:
                        age = current_time - context.last_updated
                        if age > timedelta(hours=1):
                            stale_sessions.append(session_id)

                # Remove stale sessions
                for session_id in stale_sessions:
                    del self.active_contexts[session_id]
                    if session_id in self.session_history:
                        # Keep only recent history entries
                        self.session_history[session_id] = self.session_history[
                            session_id
                        ][-10:]

                if stale_sessions:
                    logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")

                self.last_cleanup = current_time

            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
