#!/usr/bin/env python3
"""
PostgreSQL Real-time Chat Log Ingester
Extends the existing chat log parsing to write to PostgreSQL with TimescaleDB optimization.
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

# Add the root libs directory to the path
sys.path.append("/home/opsvi/master_root/libs")

try:
    from chat_report_generator import SessionAnalyzer
    from chat_taxonomy_parser import ChatLogParser, ToolCall
except ImportError:
    # Fallback for testing - create minimal implementations
    class ChatLogParser:
        def parse_jsonl_file(self, file_path):
            """Parse JSONL file and return session data."""
            session_data = {"id": "unknown", "nodes": []}

            try:
                with open(file_path, "r") as f:
                    # Handle different JSONL formats
                    content = f.read().strip()

                    if content.startswith("{") and not content.startswith("["):
                        # Single JSON object (some Claude exports)
                        data = json.loads(content)
                        if "messages" in data:
                            session_data["nodes"] = data["messages"]
                            session_data["id"] = data.get("id", Path(file_path).stem)
                        else:
                            session_data["nodes"] = [data]
                            session_data["id"] = data.get(
                                "conversation_id", Path(file_path).stem
                            )
                    else:
                        # Line-by-line JSONL
                        for line in content.split("\n"):
                            if line.strip():
                                node_data = json.loads(line)
                                session_data["nodes"].append(node_data)
                                if "conversation_id" in node_data:
                                    session_data["id"] = node_data["conversation_id"]
                                elif (
                                    "id" not in session_data
                                    or session_data["id"] == "unknown"
                                ):
                                    session_data["id"] = Path(file_path).stem

            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                return None

            return session_data

    class SessionAnalyzer:
        def __init__(self):
            pass


logger = logging.getLogger(__name__)


class PostgresChatIngester:
    """Real-time chat log ingester for PostgreSQL with TimescaleDB."""

    def __init__(self, postgres_url: str = None):
        self.postgres_url = postgres_url or (
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.parser = ChatLogParser()
        self.analyzer = SessionAnalyzer()

        # Track processed files to avoid duplicates
        self.processed_files = set()

        # Batch processing for performance
        self.batch_size = 100
        self.batch_items = []

    async def connect(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={"jit": "off"},  # Disable JIT for faster simple queries
            )
            logger.info("Connected to PostgreSQL with connection pool")

            # Test the connection
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT NOW()")
                logger.info(f"Database connection verified: {result}")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        """Close PostgreSQL connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("PostgreSQL connection pool closed")

    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA256 hash for content deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _extract_file_context(self, node_data: Dict) -> Dict:
        """Extract file path context from Claude session exports."""
        file_paths = set()

        # Handle Claude session export format
        if node_data.get("tool_calls"):
            for tool_call in node_data["tool_calls"]:
                tool_name = tool_call.get("function", {}).get("name", "")
                args = tool_call.get("function", {}).get("arguments", {})

                # File operation tools
                if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                    if "file_path" in args:
                        file_paths.add(args["file_path"])

                # Bash commands that reference files
                elif tool_name == "Bash":
                    command = args.get("command", "")
                    # Simple file path extraction from common commands
                    for part in command.split():
                        if "/" in part and not part.startswith("-") and len(part) > 3:
                            file_paths.add(part)

        # Also check content for file references
        content = node_data.get("content", "")
        if content and isinstance(content, str):
            # Look for file paths in content
            import re

            file_matches = re.findall(r"/[\w/./-]+\.\w+", content)
            file_paths.update(file_matches)

        return {
            "file_paths": list(file_paths),
            "primary_file": list(file_paths)[0] if file_paths else None,
        }

    def _extract_session_metadata(self, session_data: Dict) -> Dict:
        """Extract session-level metadata."""
        return {
            "total_nodes": len(session_data.get("nodes", [])),
            "total_messages": len(
                [n for n in session_data.get("nodes", []) if n.get("type") == "message"]
            ),
            "total_tools": len(
                [
                    n
                    for n in session_data.get("nodes", [])
                    if n.get("type") == "tool_call"
                ]
            ),
            "unique_files": len(
                set(
                    file_path
                    for node in session_data.get("nodes", [])
                    for file_path in self._extract_file_context(node).get(
                        "file_paths", []
                    )
                )
            ),
            "session_duration_minutes": session_data.get("summary", {}).get(
                "duration_minutes", 0
            ),
        }

    async def _ingest_context_item(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        node_data: Dict,
        session_metadata: Dict,
    ) -> Optional[str]:
        """Ingest a single context item into PostgreSQL."""
        try:
            # Determine context item properties based on Claude session export format
            role = node_data.get("role", "unknown")

            if role == "user":
                source_type = "chat"
                entity_type = "message"
                actor_type = "human"
                title = f"User message"
                content = node_data.get("content", "")

            elif role == "assistant":
                source_type = "chat"
                entity_type = "message"
                actor_type = "ai"
                title = f"Assistant message"
                content = node_data.get("content", "")

                # If this has tool calls, also process those
                if node_data.get("tool_calls"):
                    # Process tool calls separately
                    for tool_call in node_data["tool_calls"]:
                        await self._ingest_tool_call(
                            conn, session_id, tool_call, session_metadata
                        )

            else:
                # Skip unknown roles
                return None

            # Extract file context
            file_context = self._extract_file_context(node_data)
            primary_file = file_context.get("primary_file")

            # Generate content hash for deduplication
            content_hash = self._generate_content_hash(content)

            # Create timestamp from node data or use current time
            timestamp = datetime.fromisoformat(
                node_data.get("timestamp", datetime.now().isoformat())
            )

            # Prepare metrics
            metrics = {
                "node_id": node_data.get("id"),
                "session_total_nodes": session_metadata.get("total_nodes", 0),
                "file_paths_count": len(file_context.get("file_paths", [])),
                "content_length": len(content),
                "tool_name": node_data.get("data", {}).get("tool")
                if node_data.get("type") == "tool_call"
                else None,
            }

            # Insert into context_items table
            context_item_id = await conn.fetchval(
                """
                INSERT INTO context_items (
                    source_type, source_id, entity_type, timestamp, ingested_at,
                    title, content, content_hash, file_path, actor_type, session_id,
                    metrics, source_data
                ) VALUES ($1, $2, $3, $4, NOW(), $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (source_type, source_id) DO NOTHING
                RETURNING id
            """,
                source_type,  # $1: source_type
                f"{session_id}:{node_data.get('id')}",  # $2: source_id
                entity_type,  # $3: entity_type
                timestamp,  # $4: timestamp
                title,  # $5: title
                content[:10000],  # $6: content (truncated for performance)
                content_hash,  # $7: content_hash
                primary_file,  # $8: file_path
                actor_type,  # $9: actor_type
                session_id,  # $10: session_id
                json.dumps(metrics),  # $11: metrics
                json.dumps(node_data),  # $12: source_data
            )

            # Also insert file activity if this relates to files
            if file_context.get("file_paths") and node_data.get("type") == "tool_call":
                tool_name = node_data.get("data", {}).get("tool", "")
                change_type = (
                    "read"
                    if tool_name == "Read"
                    else "write"
                    if tool_name in ["Write", "Edit"]
                    else "execute"
                )

                for file_path in file_context["file_paths"]:
                    await conn.execute(
                        """
                        INSERT INTO file_activity (
                            session_id, timestamp, file_path, change_type,
                            tool_used, context_data
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (session_id, timestamp, file_path, change_type) DO NOTHING
                    """,
                        session_id,  # $1: session_id
                        timestamp,  # $2: timestamp
                        file_path,  # $3: file_path
                        change_type,  # $4: change_type
                        tool_name,  # $5: tool_used
                        json.dumps(node_data),  # $6: context_data
                    )

            return str(context_item_id) if context_item_id else None

        except Exception as e:
            logger.error(
                f"Failed to ingest context item {node_data.get('id', 'unknown')}: {e}"
            )
            return None

    async def _ingest_tool_call(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        tool_call: Dict,
        session_metadata: Dict,
    ) -> Optional[str]:
        """Ingest a tool call as a separate context item."""
        try:
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            tool_args = tool_call.get("function", {}).get("arguments", {})

            source_type = "chat"
            entity_type = "tool_call"
            actor_type = "ai"
            title = f"Tool call: {tool_name}"
            content = json.dumps(tool_call)

            # Generate content hash
            content_hash = self._generate_content_hash(content)

            # Create timestamp (use current time for tool calls)
            timestamp = datetime.now()

            # Prepare metrics
            metrics = {
                "tool_name": tool_name,
                "tool_call_id": tool_call.get("id"),
                "session_total_nodes": session_metadata.get("total_nodes", 0),
                "content_length": len(content),
            }

            # Insert tool call as context item
            tool_call_id = await conn.fetchval(
                """
                INSERT INTO context_items (
                    source_type, source_id, entity_type, timestamp, ingested_at,
                    title, content, content_hash, actor_type, session_id,
                    metrics, source_data
                ) VALUES ($1, $2, $3, $4, NOW(), $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (source_type, source_id) DO NOTHING
                RETURNING id
            """,
                source_type,  # $1
                f"{session_id}:tool:{tool_call.get('id', 'unknown')}",  # $2
                entity_type,  # $3
                timestamp,  # $4
                title,  # $5
                content[:10000],  # $6
                content_hash,  # $7
                actor_type,  # $8
                session_id,  # $9
                json.dumps(metrics),  # $10
                json.dumps(tool_call),  # $11
            )

            return str(tool_call_id) if tool_call_id else None

        except Exception as e:
            logger.error(
                f"Failed to ingest tool call {tool_call.get('id', 'unknown')}: {e}"
            )
            return None

    async def _update_session_record(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        session_data: Dict,
        session_metadata: Dict,
    ):
        """Insert or update chat session record."""
        try:
            await conn.execute(
                """
                INSERT INTO chat_sessions (
                    id, session_name, started_at, ended_at,
                    total_messages, total_tokens, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    ended_at = EXCLUDED.ended_at,
                    total_messages = EXCLUDED.total_messages,
                    total_tokens = EXCLUDED.total_tokens,
                    metadata = EXCLUDED.metadata
            """,
                session_id,  # $1: id
                session_data.get("summary", {}).get(
                    "title", f"Session {session_id[:8]}"
                ),  # $2: session_name
                datetime.fromisoformat(
                    session_data.get("created_at", datetime.now().isoformat())
                ),  # $3: started_at
                datetime.fromisoformat(
                    session_data.get("updated_at", datetime.now().isoformat())
                ),  # $4: ended_at
                session_metadata.get("total_messages", 0),  # $5: total_messages
                session_data.get("summary", {}).get(
                    "total_tokens", 0
                ),  # $6: total_tokens
                json.dumps(session_metadata),  # $7: metadata
            )

        except Exception as e:
            logger.error(f"Failed to update session record {session_id}: {e}")

    async def ingest_chat_session(self, session_data: Dict) -> bool:
        """Ingest a complete chat session into PostgreSQL."""
        if not self.connection_pool:
            await self.connect()

        session_id = session_data.get("id", "unknown")
        logger.info(f"Ingesting chat session: {session_id}")

        try:
            async with self.connection_pool.acquire() as conn:
                async with conn.transaction():
                    # Extract session metadata
                    session_metadata = self._extract_session_metadata(session_data)

                    # Update session record
                    await self._update_session_record(
                        conn, session_id, session_data, session_metadata
                    )

                    # Process all nodes in the session
                    ingested_count = 0
                    for node in session_data.get("nodes", []):
                        context_item_id = await self._ingest_context_item(
                            conn, session_id, node, session_metadata
                        )
                        if context_item_id:
                            ingested_count += 1

                    logger.info(
                        f"Successfully ingested {ingested_count} items for session {session_id}"
                    )
                    return True

        except Exception as e:
            logger.error(f"Failed to ingest session {session_id}: {e}")
            return False

    async def ingest_chat_file(self, file_path: str) -> bool:
        """Ingest a single chat log JSONL file."""
        if file_path in self.processed_files:
            logger.debug(f"File already processed: {file_path}")
            return True

        logger.info(f"Processing chat file: {file_path}")

        try:
            # Parse the JSONL file
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = self.parser.parse_jsonl_file(file_path)

            if not session_data:
                logger.warning(f"No session data found in {file_path}")
                return False

            # Ingest to PostgreSQL
            success = await self.ingest_chat_session(session_data)

            if success:
                self.processed_files.add(file_path)
                logger.info(f"Successfully processed {file_path}")

            return success

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return False

    async def process_file_queue(self, file_queue: asyncio.Queue):
        """Process files from a queue for real-time ingestion."""
        while True:
            try:
                # Wait for file from queue
                file_info = await file_queue.get()

                if file_info is None:  # Shutdown signal
                    break

                file_path = file_info.get("path")
                event_type = file_info.get("event_type", "unknown")

                logger.info(f"Processing {event_type} file: {file_path}")

                # Ingest the file
                await self.ingest_chat_file(file_path)

                file_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing file from queue: {e}")
                file_queue.task_done()

    async def batch_ingest_existing_files(
        self, directory: str, pattern: str = "*.jsonl"
    ):
        """Batch ingest all existing chat log files in a directory."""
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return

        jsonl_files = list(directory_path.rglob(pattern))
        logger.info(f"Found {len(jsonl_files)} JSONL files in {directory}")

        success_count = 0
        for file_path in jsonl_files:
            if await self.ingest_chat_file(str(file_path)):
                success_count += 1

        logger.info(f"Successfully ingested {success_count}/{len(jsonl_files)} files")

    async def get_ingestion_stats(self) -> Dict:
        """Get current ingestion statistics from PostgreSQL."""
        if not self.connection_pool:
            return {}

        try:
            async with self.connection_pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_items,
                        COUNT(DISTINCT session_id) as total_sessions,
                        COUNT(*) FILTER (WHERE source_type = 'chat') as chat_items,
                        COUNT(*) FILTER (WHERE entity_type = 'message') as messages,
                        COUNT(*) FILTER (WHERE entity_type = 'tool_call') as tool_calls,
                        COUNT(DISTINCT file_path) FILTER (WHERE file_path IS NOT NULL) as unique_files,
                        MIN(timestamp) as earliest_item,
                        MAX(timestamp) as latest_item
                    FROM context_items
                """
                )

                return dict(stats) if stats else {}

        except Exception as e:
            logger.error(f"Failed to get ingestion stats: {e}")
            return {}


# Service management
class PostgresChatIngestionService:
    """Service wrapper for running the PostgreSQL ingestion pipeline."""

    def __init__(self):
        self.ingester = PostgresChatIngester()
        self.file_queue = asyncio.Queue(maxsize=1000)
        self.running = False

    async def start(self, watch_directories: List[str] = None):
        """Start the ingestion service."""
        if watch_directories is None:
            watch_directories = [
                "/home/opsvi/master_root",
                "/home/opsvi/.claude/session-exports",
            ]

        logger.info(f"Starting PostgreSQL chat ingestion service")

        # Connect to PostgreSQL
        await self.ingester.connect()

        # Start file processor
        self.running = True
        processor_task = asyncio.create_task(
            self.ingester.process_file_queue(self.file_queue)
        )

        # Batch process existing files
        for directory in watch_directories:
            await self.ingester.batch_ingest_existing_files(directory)

        # Print stats
        stats = await self.ingester.get_ingestion_stats()
        logger.info(f"Ingestion complete. Stats: {stats}")

        return processor_task

    async def add_file(self, file_path: str, event_type: str = "manual"):
        """Add a file to the processing queue."""
        file_info = {
            "path": file_path,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
        }
        await self.file_queue.put(file_info)

    async def stop(self):
        """Stop the ingestion service."""
        logger.info("Stopping PostgreSQL chat ingestion service")
        self.running = False

        # Send shutdown signal
        await self.file_queue.put(None)

        # Disconnect
        await self.ingester.disconnect()


if __name__ == "__main__":
    # Test the ingestion service
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def test_ingestion():
        service = PostgresChatIngestionService()

        try:
            task = await service.start(["/home/opsvi/.claude/session-exports"])

            # Let it run for a bit
            await asyncio.sleep(2)

            # Stop the service
            await service.stop()

        except KeyboardInterrupt:
            await service.stop()

    # Run the test
    asyncio.run(test_ingestion())
