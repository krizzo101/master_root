#!/usr/bin/env python3
"""
Chat Log Taxonomy Parser and Storage System
Based on UNIFIED_CONTEXT_SYSTEM.md taxonomy specification
"""

import hashlib
import json
import re
import uuid as uuid_lib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "chat_logs",
    "user": "postgres",
    "password": "postgres",
}


@dataclass
class Session:
    session_id: str
    cwd: str
    git_branch: str
    created_at: datetime
    metadata: Dict = None


@dataclass
class Node:
    uuid: str
    session_id: str
    parent_uuid: Optional[str]
    node_type: str  # 'user', 'assistant', 'system', 'summary'
    timestamp: datetime
    content_hash: str
    is_sidechain: bool = False
    raw_json: Dict = None


@dataclass
class ToolCall:
    node_uuid: str
    tool_use_id: str
    tool_name: str
    input_json: Dict
    timestamp: datetime


@dataclass
class ToolResult:
    tool_use_id: str
    node_uuid: str
    is_error: bool
    content_text: str
    content_json: Dict
    timestamp: datetime


@dataclass
class FileOperation:
    tool_call_id: str
    operation: str  # 'read', 'write', 'edit'
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content_before: Optional[str] = None
    content_after: Optional[str] = None


class ChatLogParser:
    """Parse Claude JSONL logs according to the defined taxonomy"""

    def __init__(self):
        self.sessions = {}
        self.nodes = []
        self.tool_calls = []
        self.tool_results = []
        self.file_operations = []

        # Tool categorization patterns
        self.tool_patterns = {
            "file_ops": ["Read", "Write", "Edit", "MultiEdit"],
            "shell_ops": ["Bash", "Grep", "LS", "Glob"],
            "web_ops": ["WebSearch", "WebFetch", "brave_web_search"],
            "knowledge": ["knowledge_store", "knowledge_query"],
            "mcp_tools": re.compile(r"mcp__(\w+)__(\w+)"),
        }

    def hash_content(self, content: str) -> str:
        """Generate SHA256 hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def parse_jsonl_file(self, file_path: Path) -> None:
        """Parse a single JSONL file"""
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    self._process_record(record)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}")
                except Exception as e:
                    print(f"Error processing record at line {line_num}: {e}")

    def _process_record(self, record: Dict) -> None:
        """Process a single JSONL record based on its type"""
        record_type = record.get("type")

        # Extract session information
        if "sessionId" in record:
            self._extract_session(record)

        # Process based on type
        if record_type == "user":
            self._process_user_message(record)
        elif record_type == "assistant":
            self._process_assistant_message(record)
        elif record_type == "system":
            self._process_system_event(record)
        elif record_type == "summary":
            self._process_summary(record)

    def _extract_session(self, record: Dict) -> None:
        """Extract session information"""
        session_id = record.get("sessionId")
        if session_id and session_id not in self.sessions:
            self.sessions[session_id] = Session(
                session_id=session_id,
                cwd=record.get("cwd", ""),
                git_branch=record.get("git_branch", ""),
                created_at=datetime.fromisoformat(
                    record.get("timestamp", datetime.now().isoformat())
                ),
                metadata=record.get("metadata", {}),
            )

    def _process_user_message(self, record: Dict) -> None:
        """Process user message"""
        node = Node(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=record.get("sessionId"),
            parent_uuid=record.get("parentUuid"),
            node_type="user",
            timestamp=datetime.fromisoformat(
                record.get("timestamp", datetime.now().isoformat())
            ),
            content_hash=self.hash_content(
                record.get("message", {}).get("content", "")
            ),
            is_sidechain=record.get("isSidechain", False),
            raw_json=record,
        )
        self.nodes.append(node)

    def _process_assistant_message(self, record: Dict) -> None:
        """Process assistant message with tool calls and results"""
        node = Node(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=record.get("sessionId"),
            parent_uuid=record.get("parentUuid"),
            node_type="assistant",
            timestamp=datetime.fromisoformat(
                record.get("timestamp", datetime.now().isoformat())
            ),
            content_hash=self.hash_content(str(record.get("message", {}))),
            is_sidechain=record.get("isSidechain", False),
            raw_json=record,
        )
        self.nodes.append(node)

        # Process content array for tool uses and results
        content = record.get("message", {}).get("content", [])
        if isinstance(content, list):
            for item in content:
                item_type = item.get("type")

                if item_type == "tool_use":
                    self._process_tool_use(item, node.uuid)
                elif item_type == "tool_result":
                    self._process_tool_result(item, node.uuid)
                elif item_type == "thinking":
                    # Only store hash, never raw thinking
                    item["thinking_hash"] = self.hash_content(item.get("thinking", ""))
                    item["thinking"] = None  # Redact

    def _process_tool_use(self, item: Dict, node_uuid: str) -> None:
        """Process tool use"""
        tool_call = ToolCall(
            node_uuid=node_uuid,
            tool_use_id=item.get("id", str(uuid_lib.uuid4())),
            tool_name=item.get("name"),
            input_json=item.get("input", {}),
            timestamp=datetime.now(),
        )
        self.tool_calls.append(tool_call)

        # Extract file operations
        if tool_call.tool_name in self.tool_patterns["file_ops"]:
            self._extract_file_operation(tool_call)

    def _process_tool_result(self, item: Dict, node_uuid: str) -> None:
        """Process tool result"""
        tool_result = ToolResult(
            tool_use_id=item.get("tool_use_id"),
            node_uuid=node_uuid,
            is_error=item.get("is_error", False),
            content_text=str(item.get("content", "")),
            content_json=item if isinstance(item.get("content"), dict) else {},
            timestamp=datetime.now(),
        )
        self.tool_results.append(tool_result)

    def _extract_file_operation(self, tool_call: ToolCall) -> None:
        """Extract file operation details"""
        input_data = tool_call.input_json

        operation_map = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "MultiEdit": "edit",
        }

        file_op = FileOperation(
            tool_call_id=tool_call.tool_use_id,
            operation=operation_map.get(tool_call.tool_name, "unknown"),
            file_path=input_data.get("file_path", "") or input_data.get("path", ""),
            line_start=input_data.get("offset"),
            line_end=input_data.get("limit"),
            content_before=input_data.get("old_string"),
            content_after=input_data.get("new_string"),
        )
        self.file_operations.append(file_op)

    def _process_system_event(self, record: Dict) -> None:
        """Process system event"""
        node = Node(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=record.get("sessionId"),
            parent_uuid=record.get("parentUuid"),
            node_type="system",
            timestamp=datetime.fromisoformat(
                record.get("timestamp", datetime.now().isoformat())
            ),
            content_hash=self.hash_content(str(record)),
            raw_json=record,
        )
        self.nodes.append(node)

    def _process_summary(self, record: Dict) -> None:
        """Process summary"""
        node = Node(
            uuid=record.get("uuid", str(uuid_lib.uuid4())),
            session_id=record.get("sessionId"),
            parent_uuid=record.get("leafUuid"),  # Link to leaf node
            node_type="summary",
            timestamp=datetime.fromisoformat(
                record.get("timestamp", datetime.now().isoformat())
            ),
            content_hash=self.hash_content(record.get("content", "")),
            raw_json=record,
        )
        self.nodes.append(node)


class ChatLogStorage:
    """Store parsed chat logs in PostgreSQL"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL"""
        self.conn = psycopg2.connect(**self.db_config)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def create_schema(self):
        """Create database schema"""
        schema_sql = """
        -- Sessions table
        CREATE TABLE IF NOT EXISTS sessions (
            session_id UUID PRIMARY KEY,
            cwd TEXT,
            git_branch TEXT,
            created_at TIMESTAMPTZ,
            metadata JSONB
        );

        -- Nodes table
        CREATE TABLE IF NOT EXISTS nodes (
            uuid UUID PRIMARY KEY,
            session_id UUID REFERENCES sessions,
            parent_uuid UUID,
            node_type TEXT,
            timestamp TIMESTAMPTZ,
            content_hash TEXT,
            is_sidechain BOOLEAN DEFAULT FALSE,
            raw_json JSONB
        );

        -- Tool calls table
        CREATE TABLE IF NOT EXISTS tool_calls (
            id SERIAL PRIMARY KEY,
            node_uuid UUID REFERENCES nodes,
            tool_use_id TEXT UNIQUE,
            tool_name TEXT,
            input_json JSONB,
            timestamp TIMESTAMPTZ
        );

        -- Tool results table
        CREATE TABLE IF NOT EXISTS tool_results (
            id SERIAL PRIMARY KEY,
            tool_use_id TEXT,
            node_uuid UUID REFERENCES nodes,
            is_error BOOLEAN,
            content_text TEXT,
            content_json JSONB,
            timestamp TIMESTAMPTZ
        );

        -- File operations table
        CREATE TABLE IF NOT EXISTS file_operations (
            id SERIAL PRIMARY KEY,
            tool_call_id TEXT,
            operation TEXT,
            file_path TEXT,
            line_start INT,
            line_end INT,
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

        with self.conn.cursor() as cur:
            cur.execute(schema_sql)
            self.conn.commit()

    def store_parsed_data(self, parser: ChatLogParser):
        """Store all parsed data"""
        with self.conn.cursor() as cur:
            # Store sessions
            for session in parser.sessions.values():
                self._upsert_session(cur, session)

            # Store nodes
            for node in parser.nodes:
                self._upsert_node(cur, node)

            # Store tool calls
            for tool_call in parser.tool_calls:
                self._upsert_tool_call(cur, tool_call)

            # Store tool results
            for tool_result in parser.tool_results:
                self._upsert_tool_result(cur, tool_result)

            # Store file operations
            for file_op in parser.file_operations:
                self._upsert_file_operation(cur, file_op)

            self.conn.commit()

    def _upsert_session(self, cur, session: Session):
        """Upsert session record"""
        sql = """
        INSERT INTO sessions (session_id, cwd, git_branch, created_at, metadata)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (session_id) DO UPDATE
        SET cwd = EXCLUDED.cwd,
            git_branch = EXCLUDED.git_branch,
            metadata = EXCLUDED.metadata
        """
        cur.execute(
            sql,
            (
                session.session_id,
                session.cwd,
                session.git_branch,
                session.created_at,
                Json(session.metadata),
            ),
        )

    def _upsert_node(self, cur, node: Node):
        """Upsert node record"""
        sql = """
        INSERT INTO nodes (uuid, session_id, parent_uuid, node_type, timestamp, content_hash, is_sidechain, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (uuid) DO NOTHING
        """
        cur.execute(
            sql,
            (
                node.uuid,
                node.session_id,
                node.parent_uuid,
                node.node_type,
                node.timestamp,
                node.content_hash,
                node.is_sidechain,
                Json(node.raw_json),
            ),
        )

    def _upsert_tool_call(self, cur, tool_call: ToolCall):
        """Upsert tool call record"""
        sql = """
        INSERT INTO tool_calls (node_uuid, tool_use_id, tool_name, input_json, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tool_use_id) DO NOTHING
        """
        cur.execute(
            sql,
            (
                tool_call.node_uuid,
                tool_call.tool_use_id,
                tool_call.tool_name,
                Json(tool_call.input_json),
                tool_call.timestamp,
            ),
        )

    def _upsert_tool_result(self, cur, tool_result: ToolResult):
        """Upsert tool result record"""
        sql = """
        INSERT INTO tool_results (tool_use_id, node_uuid, is_error, content_text, content_json, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql,
            (
                tool_result.tool_use_id,
                tool_result.node_uuid,
                tool_result.is_error,
                tool_result.content_text,
                Json(tool_result.content_json),
                tool_result.timestamp,
            ),
        )

    def _upsert_file_operation(self, cur, file_op: FileOperation):
        """Upsert file operation record"""
        sql = """
        INSERT INTO file_operations (tool_call_id, operation, file_path, line_start, line_end, content_before, content_after)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql,
            (
                file_op.tool_call_id,
                file_op.operation,
                file_op.file_path,
                file_op.line_start,
                file_op.line_end,
                file_op.content_before,
                file_op.content_after,
            ),
        )


class ChatLogQuery:
    """Query interface for chat logs"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config

    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary statistics for a session"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                SELECT
                    s.session_id,
                    s.cwd,
                    s.git_branch,
                    s.created_at,
                    COUNT(DISTINCT n.uuid) as total_nodes,
                    COUNT(DISTINCT CASE WHEN n.node_type = 'user' THEN n.uuid END) as user_messages,
                    COUNT(DISTINCT CASE WHEN n.node_type = 'assistant' THEN n.uuid END) as assistant_messages,
                    COUNT(DISTINCT tc.tool_use_id) as total_tool_calls,
                    COUNT(DISTINCT fo.file_path) as files_touched
                FROM sessions s
                LEFT JOIN nodes n ON s.session_id = n.session_id
                LEFT JOIN tool_calls tc ON n.uuid = tc.node_uuid
                LEFT JOIN file_operations fo ON tc.tool_use_id = fo.tool_call_id
                WHERE s.session_id = %s
                GROUP BY s.session_id, s.cwd, s.git_branch, s.created_at
                """
                cur.execute(sql, (session_id,))
                return cur.fetchone()

    def get_file_history(self, file_path: str) -> List[Dict]:
        """Get all operations on a specific file"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                SELECT
                    fo.*,
                    tc.tool_name,
                    tc.timestamp,
                    n.session_id
                FROM file_operations fo
                JOIN tool_calls tc ON fo.tool_call_id = tc.tool_use_id
                JOIN nodes n ON tc.node_uuid = n.uuid
                WHERE fo.file_path = %s
                ORDER BY tc.timestamp DESC
                """
                cur.execute(sql, (file_path,))
                return cur.fetchall()

    def get_tool_usage_report(self, session_id: Optional[str] = None) -> List[Dict]:
        """Get tool usage statistics"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                SELECT
                    tc.tool_name,
                    COUNT(*) as usage_count,
                    COUNT(DISTINCT n.session_id) as sessions_used,
                    AVG(CASE WHEN tr.is_error THEN 1 ELSE 0 END) * 100 as error_rate
                FROM tool_calls tc
                JOIN nodes n ON tc.node_uuid = n.uuid
                LEFT JOIN tool_results tr ON tc.tool_use_id = tr.tool_use_id
                """

                if session_id:
                    sql += " WHERE n.session_id = %s"

                sql += " GROUP BY tc.tool_name ORDER BY usage_count DESC"

                if session_id:
                    cur.execute(sql, (session_id,))
                else:
                    cur.execute(sql)

                return cur.fetchall()

    def search_content(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Full-text search across messages and tool results"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                SELECT
                    n.uuid,
                    n.session_id,
                    n.node_type,
                    n.timestamp,
                    n.raw_json
                FROM nodes n
                WHERE n.raw_json::text ILIKE %s
                ORDER BY n.timestamp DESC
                LIMIT %s
                """
                cur.execute(sql, (f"%{search_term}%", limit))
                return cur.fetchall()


def main():
    """Example usage"""
    # Parse logs
    parser = ChatLogParser()

    # Parse all JSONL files in session exports
    session_exports = Path("/home/opsvi/master_root/.claude/session-exports")
    if session_exports.exists():
        for jsonl_file in session_exports.glob("*.jsonl"):
            print(f"Parsing {jsonl_file}")
            parser.parse_jsonl_file(jsonl_file)

    # Store in database
    storage = ChatLogStorage(DB_CONFIG)
    storage.connect()
    storage.create_schema()
    storage.store_parsed_data(parser)
    storage.close()

    # Query examples
    query = ChatLogQuery(DB_CONFIG)

    # Get session summary
    if parser.sessions:
        session_id = list(parser.sessions.keys())[0]
        summary = query.get_session_summary(session_id)
        print(f"Session Summary: {summary}")

    # Get tool usage report
    tool_report = query.get_tool_usage_report()
    print(f"Tool Usage: {tool_report}")


if __name__ == "__main__":
    main()
