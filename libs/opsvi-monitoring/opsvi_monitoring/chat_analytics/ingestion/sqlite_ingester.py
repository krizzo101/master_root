#!/usr/bin/env python3
"""
Ingestion script for Claude chat logs using SQLite
Parses and stores all JSONL files from the master_root project
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = Path("/home/opsvi/master_root/chat_logs.db")


class ChatLogParserSQLite:
    """Parse and store Claude JSONL logs in SQLite"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.sessions_buffer = {}
        self.nodes_buffer = []
        self.tool_calls_buffer = []
        self.tool_results_buffer = []
        self.file_operations_buffer = []

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def create_schema(self):
        """Create database schema"""
        schema_sql = """
        -- Sessions table
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            cwd TEXT,
            git_branch TEXT,
            created_at TEXT,
            metadata TEXT
        );

        -- Nodes table
        CREATE TABLE IF NOT EXISTS nodes (
            uuid TEXT PRIMARY KEY,
            session_id TEXT,
            parent_uuid TEXT,
            node_type TEXT,
            timestamp TEXT,
            content_hash TEXT,
            is_sidechain INTEGER DEFAULT 0,
            raw_json TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- Tool calls table
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_uuid TEXT,
            tool_use_id TEXT UNIQUE,
            tool_name TEXT,
            input_json TEXT,
            timestamp TEXT,
            FOREIGN KEY (node_uuid) REFERENCES nodes(uuid)
        );

        -- Tool results table
        CREATE TABLE IF NOT EXISTS tool_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_use_id TEXT,
            node_uuid TEXT,
            is_error INTEGER,
            content_text TEXT,
            content_json TEXT,
            timestamp TEXT,
            FOREIGN KEY (node_uuid) REFERENCES nodes(uuid)
        );

        -- File operations table
        CREATE TABLE IF NOT EXISTS file_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_call_id TEXT,
            operation TEXT,
            file_path TEXT,
            line_start INTEGER,
            line_end INTEGER,
            content_before TEXT,
            content_after TEXT
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_nodes_session ON nodes(session_id);
        CREATE INDEX IF NOT EXISTS idx_nodes_timestamp ON nodes(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tool_calls_name ON tool_calls(tool_name);
        CREATE INDEX IF NOT EXISTS idx_file_ops_path ON file_operations(file_path);
        CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
        """

        cursor = self.conn.cursor()
        cursor.executescript(schema_sql)
        self.conn.commit()

    def hash_content(self, content: str) -> str:
        """Generate SHA256 hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def parse_jsonl_file(self, file_path: Path):
        """Parse a single JSONL file"""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    self._process_record(record)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
                except Exception as e:
                    logger.debug(
                        f"Error processing line {line_num} in {file_path.name}: {e}"
                    )
                    continue

    def _process_record(self, record: dict):
        """Process a single JSONL record"""
        record_type = record.get("type")

        # Extract session information
        if "sessionId" in record:
            session_id = record["sessionId"]
            if session_id and session_id not in self.sessions_buffer:
                self.sessions_buffer[session_id] = {
                    "session_id": session_id,
                    "cwd": record.get("cwd", ""),
                    "git_branch": record.get("git_branch", ""),
                    "created_at": record.get("timestamp", datetime.now().isoformat()),
                    "metadata": json.dumps(record.get("metadata", {})),
                }

        # Process based on type
        if record_type == "user":
            self._process_user_message(record)
        elif record_type == "assistant":
            self._process_assistant_message(record)
        elif record_type == "system":
            self._process_system_event(record)
        elif record_type == "summary":
            self._process_summary(record)

    def _process_user_message(self, record: dict):
        """Process user message"""
        node = {
            "uuid": record.get("uuid", str(uuid_lib.uuid4())),
            "session_id": record.get("sessionId"),
            "parent_uuid": record.get("parentUuid"),
            "node_type": "user",
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "content_hash": self.hash_content(
                record.get("message", {}).get("content", "")
            ),
            "is_sidechain": 1 if record.get("isSidechain") else 0,
            "raw_json": json.dumps(record),
        }
        self.nodes_buffer.append(node)

    def _process_assistant_message(self, record: dict):
        """Process assistant message"""
        node = {
            "uuid": record.get("uuid", str(uuid_lib.uuid4())),
            "session_id": record.get("sessionId"),
            "parent_uuid": record.get("parentUuid"),
            "node_type": "assistant",
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "content_hash": self.hash_content(str(record.get("message", {}))),
            "is_sidechain": 1 if record.get("isSidechain") else 0,
            "raw_json": json.dumps(record),
        }
        self.nodes_buffer.append(node)

        # Process content array for tool uses and results
        content = record.get("message", {}).get("content", [])
        if isinstance(content, list):
            for item in content:
                item_type = item.get("type")

                if item_type == "tool_use":
                    self._process_tool_use(item, node["uuid"])
                elif item_type == "tool_result":
                    self._process_tool_result(item, node["uuid"])
                elif item_type == "thinking":
                    # Only store hash, never raw thinking
                    if "thinking" in item:
                        item["thinking_hash"] = self.hash_content(
                            item.get("thinking", "")
                        )
                        item["thinking"] = None  # Redact

    def _process_tool_use(self, item: dict, node_uuid: str):
        """Process tool use"""
        tool_call = {
            "node_uuid": node_uuid,
            "tool_use_id": item.get("id", str(uuid_lib.uuid4())),
            "tool_name": item.get("name"),
            "input_json": json.dumps(item.get("input", {})),
            "timestamp": datetime.now().isoformat(),
        }
        self.tool_calls_buffer.append(tool_call)

        # Extract file operations
        tool_name = item.get("name")
        if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
            self._extract_file_operation(
                tool_call["tool_use_id"], tool_name, item.get("input", {})
            )

    def _process_tool_result(self, item: dict, node_uuid: str):
        """Process tool result"""
        tool_result = {
            "tool_use_id": item.get("tool_use_id"),
            "node_uuid": node_uuid,
            "is_error": 1 if item.get("is_error") else 0,
            "content_text": str(item.get("content", ""))[:10000],  # Limit content size
            "content_json": json.dumps(item)
            if isinstance(item.get("content"), dict)
            else "{}",
            "timestamp": datetime.now().isoformat(),
        }
        self.tool_results_buffer.append(tool_result)

    def _extract_file_operation(
        self, tool_use_id: str, tool_name: str, input_data: dict
    ):
        """Extract file operation details"""
        operation_map = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "MultiEdit": "edit",
        }

        file_op = {
            "tool_call_id": tool_use_id,
            "operation": operation_map.get(tool_name, "unknown"),
            "file_path": input_data.get("file_path", "") or input_data.get("path", ""),
            "line_start": input_data.get("offset"),
            "line_end": input_data.get("limit"),
            "content_before": (input_data.get("old_string", "") or "")[:1000],
            "content_after": (input_data.get("new_string", "") or "")[:1000],
        }
        self.file_operations_buffer.append(file_op)

    def _process_system_event(self, record: dict):
        """Process system event"""
        node = {
            "uuid": record.get("uuid", str(uuid_lib.uuid4())),
            "session_id": record.get("sessionId"),
            "parent_uuid": record.get("parentUuid"),
            "node_type": "system",
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "content_hash": self.hash_content(str(record)),
            "is_sidechain": 0,
            "raw_json": json.dumps(record),
        }
        self.nodes_buffer.append(node)

    def _process_summary(self, record: dict):
        """Process summary"""
        node = {
            "uuid": record.get("uuid", str(uuid_lib.uuid4())),
            "session_id": record.get("sessionId"),
            "parent_uuid": record.get("leafUuid"),
            "node_type": "summary",
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "content_hash": self.hash_content(record.get("content", "")),
            "is_sidechain": 0,
            "raw_json": json.dumps(record),
        }
        self.nodes_buffer.append(node)

    def flush_buffers(self):
        """Flush all buffers to database"""
        cursor = self.conn.cursor()

        # Insert sessions
        for session in self.sessions_buffer.values():
            cursor.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, cwd, git_branch, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    session["session_id"],
                    session["cwd"],
                    session["git_branch"],
                    session["created_at"],
                    session["metadata"],
                ),
            )

        # Insert nodes
        for node in self.nodes_buffer:
            cursor.execute(
                """
                INSERT OR IGNORE INTO nodes (uuid, session_id, parent_uuid, node_type,
                                            timestamp, content_hash, is_sidechain, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    node["uuid"],
                    node["session_id"],
                    node["parent_uuid"],
                    node["node_type"],
                    node["timestamp"],
                    node["content_hash"],
                    node["is_sidechain"],
                    node["raw_json"],
                ),
            )

        # Insert tool calls
        for tool_call in self.tool_calls_buffer:
            cursor.execute(
                """
                INSERT OR IGNORE INTO tool_calls (node_uuid, tool_use_id, tool_name, input_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    tool_call["node_uuid"],
                    tool_call["tool_use_id"],
                    tool_call["tool_name"],
                    tool_call["input_json"],
                    tool_call["timestamp"],
                ),
            )

        # Insert tool results
        for tool_result in self.tool_results_buffer:
            cursor.execute(
                """
                INSERT INTO tool_results (tool_use_id, node_uuid, is_error, content_text, content_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    tool_result["tool_use_id"],
                    tool_result["node_uuid"],
                    tool_result["is_error"],
                    tool_result["content_text"],
                    tool_result["content_json"],
                    tool_result["timestamp"],
                ),
            )

        # Insert file operations
        for file_op in self.file_operations_buffer:
            cursor.execute(
                """
                INSERT INTO file_operations (tool_call_id, operation, file_path, line_start, line_end,
                                           content_before, content_after)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_op["tool_call_id"],
                    file_op["operation"],
                    file_op["file_path"],
                    file_op["line_start"],
                    file_op["line_end"],
                    file_op["content_before"],
                    file_op["content_after"],
                ),
            )

        self.conn.commit()

        # Clear buffers
        self.sessions_buffer.clear()
        self.nodes_buffer.clear()
        self.tool_calls_buffer.clear()
        self.tool_results_buffer.clear()
        self.file_operations_buffer.clear()


def main():
    """Main ingestion process"""
    logger.info("Starting chat log ingestion to SQLite")

    # Get all JSONL files
    project_dir = Path.home() / ".claude" / "projects" / "-home-opsvi-master-root"
    if not project_dir.exists():
        logger.error(f"Project directory not found: {project_dir}")
        return 1

    jsonl_files = sorted(project_dir.glob("*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} JSONL files")

    if not jsonl_files:
        logger.error("No JSONL files found")
        return 1

    # Create parser and database
    parser = ChatLogParserSQLite(DB_PATH)
    parser.connect()
    parser.create_schema()

    # Process files in batches
    batch_size = 10
    total_files = len(jsonl_files)

    with tqdm(total=total_files, desc="Processing files") as pbar:
        for i in range(0, total_files, batch_size):
            batch = jsonl_files[i : i + batch_size]

            for file_path in batch:
                try:
                    parser.parse_jsonl_file(file_path)
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {e}")
                    pbar.update(1)
                    continue

            # Flush buffers after each batch
            parser.flush_buffers()
            logger.info(
                f"Processed batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}"
            )

    # Generate summary
    generate_summary(parser.conn)

    parser.close()
    logger.info(f"Ingestion complete. Database saved to {DB_PATH}")

    return 0


def generate_summary(conn):
    """Generate summary statistics"""
    cursor = conn.cursor()

    # Overall statistics
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT session_id) as sessions,
            COUNT(*) as nodes,
            COUNT(CASE WHEN node_type = 'user' THEN 1 END) as user_msgs,
            COUNT(CASE WHEN node_type = 'assistant' THEN 1 END) as assistant_msgs
        FROM nodes
    """
    )
    stats = cursor.fetchone()

    # Tool usage
    cursor.execute(
        """
        SELECT tool_name, COUNT(*) as count
        FROM tool_calls
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT 10
    """
    )
    tools = cursor.fetchall()

    # File operations
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT file_path) as unique_files,
            COUNT(*) as total_ops
        FROM file_operations
    """
    )
    file_stats = cursor.fetchone()

    print("\n" + "=" * 60)
    print("CHAT LOG INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total Sessions:     {stats[0]:,}")
    print(f"Total Nodes:        {stats[1]:,}")
    print(f"User Messages:      {stats[2]:,}")
    print(f"Assistant Messages: {stats[3]:,}")
    print(f"\nTOP TOOLS:")
    for tool_name, count in tools:
        print(f"  {tool_name:30} {count:,}")
    print(f"\nFILE OPERATIONS:")
    print(f"  Unique Files:     {file_stats[0]:,}")
    print(f"  Total Operations: {file_stats[1]:,}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
