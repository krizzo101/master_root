"""
Main correlation engine for project intelligence and chat analytics.
"""

import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, "/home/opsvi/master_root")

from opsvi_monitoring.chat_analytics.intelligence.dual_write_adapter import (
    DualWriteAdapter,
)

from scripts.proj_intel_reader import ProjectIntelReader


class ProjectIntelligenceCorrelator:
    """Correlates chat activity with project intelligence data."""

    def __init__(self, db_path: str = "/home/opsvi/master_root/chat_logs.db"):
        """Initialize the correlator with dual-write adapter and intelligence reader."""
        self.db_path = db_path
        self.reader = ProjectIntelReader("/home/opsvi/master_root/.proj-intel")

        # Initialize dual-write adapter for PostgreSQL + SQLite migration
        self.db_adapter = DualWriteAdapter(
            sqlite_path=db_path,
            postgres_url="postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        )

        # Load indices for fast lookups
        self.symbol_index = self._load_symbol_index()
        self.reverse_index = self.reader.reverse_index
        self.file_elements_cache = {}
        self.agent_cache = {}

        # Patterns for extraction
        self.file_path_pattern = re.compile(
            r"(?:^|\s)([./]?(?:[\w\-]+/)*[\w\-]+\.(?:py|js|ts|tsx|jsx|md|json|yaml|yml|txt|sh|sql))\b"
        )
        self.function_pattern = re.compile(
            r"\b(?:def|function|const|let|var)\s+(\w+)\s*(?:\(|=)"
        )
        self.class_pattern = re.compile(r"\bclass\s+(\w+)(?:\([\w\s,]*\))?:")

    def _load_symbol_index(self) -> Dict[str, Any]:
        """Load the symbol index for fast symbol lookups."""
        symbol_index_path = Path(
            "/home/opsvi/master_root/.proj-intel/symbol_index.json"
        )
        if symbol_index_path.exists():
            with open(symbol_index_path) as f:
                return json.load(f)
        return {}

    # Database initialization no longer needed - handled by dual-write adapter

    def process_message(
        self, message: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """
        Process a chat message for code references and correlations.

        Args:
            message: Chat message dictionary
            session_id: Session identifier

        Returns:
            Dictionary containing extracted context and correlations
        """
        content = message.get("content", "")
        message_id = message.get("id", "")
        timestamp = message.get("timestamp", datetime.now().isoformat())

        # Extract file paths mentioned
        file_paths = self._extract_file_paths(content)

        # Extract symbols (functions, classes)
        symbols = self._extract_symbols(content)

        # Build code context
        context = self._build_code_context(file_paths, symbols)

        # Store correlations in database
        self._store_correlations(session_id, message_id, timestamp, context)

        # Track changes if tools were used
        if self._has_code_modification(message):
            self._track_code_changes(session_id, message, context)

        return context

    def _extract_file_paths(self, content: str) -> List[str]:
        """Extract file paths mentioned in the message."""
        paths = self.file_path_pattern.findall(content)

        # Normalize and validate paths
        valid_paths = []
        for path in paths:
            # Convert relative to absolute if needed
            if not path.startswith("/"):
                # Check if file exists in project
                potential_path = f"/home/opsvi/master_root/{path}"
                if Path(potential_path).exists():
                    valid_paths.append(potential_path)
                elif path in self.reverse_index:
                    valid_paths.append(path)
            else:
                valid_paths.append(path)

        return list(set(valid_paths))

    def _extract_symbols(self, content: str) -> List[Dict[str, Any]]:
        """Extract code symbols from message content."""
        symbols = []

        # Extract function names
        functions = self.function_pattern.findall(content)
        for func in functions:
            if func in self.symbol_index:
                symbols.append(
                    {
                        "name": func,
                        "type": "function",
                        "locations": self.symbol_index[func],
                    }
                )

        # Extract class names
        classes = self.class_pattern.findall(content)
        for cls in classes:
            if cls in self.symbol_index:
                symbols.append(
                    {"name": cls, "type": "class", "locations": self.symbol_index[cls]}
                )

        # Also check for exact symbol mentions
        for symbol_name in self.symbol_index:
            if (
                isinstance(symbol_name, str)
                and symbol_name in content
                and len(symbol_name) > 3
            ):  # Avoid false positives
                already_found = any(s["name"] == symbol_name for s in symbols)
                if not already_found:
                    symbols.append(
                        {
                            "name": symbol_name,
                            "type": "unknown",
                            "locations": self.symbol_index[symbol_name],
                        }
                    )

        return symbols

    def _build_code_context(
        self, file_paths: List[str], symbols: List[Dict]
    ) -> Dict[str, Any]:
        """Build comprehensive code context from paths and symbols."""
        context = {"files": [], "symbols": symbols, "agents": [], "metrics": {}}

        # Get file elements for each path
        for path in file_paths:
            file_info = self._get_file_elements(path)
            if file_info:
                context["files"].append(file_info)

        # Get agent information if any symbols are agents
        for symbol in symbols:
            agent_info = self._get_agent_info(symbol["name"])
            if agent_info:
                context["agents"].append(agent_info)

        # Calculate aggregate metrics
        if context["files"]:
            context["metrics"] = {
                "total_functions": sum(f.get("fn_count", 0) for f in context["files"]),
                "total_classes": sum(f.get("class_count", 0) for f in context["files"]),
                "total_lines": sum(f.get("line_count", 0) for f in context["files"]),
                "files_referenced": len(context["files"]),
            }

        return context

    def _get_file_elements(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file elements from project intelligence."""
        if file_path in self.file_elements_cache:
            return self.file_elements_cache[file_path]

        # Try to get from reverse index
        if file_path in self.reverse_index:
            items = self.reader.read_by_path(file_path)
            for item in items:
                if (
                    item.get("kind") == "collector_item"
                    and item.get("collector") == "FileElementsCollector"
                ):
                    file_data = item.get("data", {})
                    self.file_elements_cache[file_path] = file_data
                    return file_data

        return None

    def _get_agent_info(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        """Get agent architecture information for a symbol."""
        if symbol_name in self.agent_cache:
            return self.agent_cache[symbol_name]

        # Stream through agent architecture
        for agent in self.reader.get_agent_architecture():
            if agent.get("name") == symbol_name:
                self.agent_cache[symbol_name] = agent
                return agent

        return None

    def _has_code_modification(self, message: Dict) -> bool:
        """Check if message indicates code modification."""
        tool_calls = message.get("tool_calls", [])
        modification_tools = ["Edit", "Write", "MultiEdit", "NotebookEdit"]

        for tool in tool_calls:
            if tool.get("name") in modification_tools:
                return True

        return False

    def _track_code_changes(self, session_id: str, message: Dict, context: Dict):
        """Track code changes from tool usage using dual-write adapter."""
        tool_calls = message.get("tool_calls", [])

        for tool in tool_calls:
            tool_name = tool.get("name")
            args = tool.get("arguments", {})

            if tool_name in ["Edit", "Write", "MultiEdit"]:
                file_path = args.get("file_path")
                if file_path:
                    # Get before state
                    before_info = self._get_file_elements(file_path)
                    before_hash = (
                        before_info.get("content_hash") if before_info else None
                    )

                    # Prepare affected symbols
                    affected_functions = []
                    affected_classes = []

                    if context.get("symbols"):
                        affected_functions = [
                            s["name"]
                            for s in context["symbols"]
                            if s["type"] == "function"
                        ]
                        affected_classes = [
                            s["name"]
                            for s in context["symbols"]
                            if s["type"] == "class"
                        ]

                    # Use dual-write adapter to record the change
                    self.db_adapter.write_file_activity(
                        session_id=session_id,
                        file_path=file_path,
                        action="modified",
                        tool_used=tool_name,
                        functions_affected=affected_functions,
                        classes_affected=affected_classes,
                        before_hash=before_hash,
                    )

    def _store_correlations(
        self, session_id: str, message_id: str, timestamp: str, context: Dict
    ):
        """Store correlations using dual-write adapter."""
        # Store code context for each file
        for file_info in context.get("files", []):
            # Convert symbols to the expected format
            symbols_dict = {
                "functions": [
                    s["name"]
                    for s in context.get("symbols", [])
                    if s["type"] == "function"
                ],
                "classes": [
                    s["name"]
                    for s in context.get("symbols", [])
                    if s["type"] == "class"
                ],
                "unknown": [
                    s["name"]
                    for s in context.get("symbols", [])
                    if s["type"] == "unknown"
                ],
            }

            self.db_adapter.write_code_context(
                session_id=session_id,
                file_path=file_info.get("file_path"),
                symbols=symbols_dict,
                content_hash=file_info.get("content_hash"),
                relevance_score=0.8,  # Default relevance score
            )

        # Store individual symbol references
        for symbol in context.get("symbols", []):
            for location in symbol.get("locations", []):
                file_path = None
                line_number = None

                if isinstance(location, dict):
                    file_path = location.get("file_path")
                    line_number = location.get("line_number")

                self.db_adapter.write_symbol_reference(
                    message_id=message_id,
                    session_id=session_id,
                    symbol_name=symbol["name"],
                    symbol_type=symbol["type"],
                    file_path=file_path,
                    line_number=line_number,
                    reference_type="mentioned",
                )

        # Store agent usage information
        for agent in context.get("agents", []):
            self.db_adapter.write_agent_usage(
                session_id=session_id,
                agent_class=agent.get("name"),
                agent_token=agent.get("agent_token"),
                task_description=f"Agent utilized: {agent.get('name')}",
                file_paths=[agent.get("file_path")] if agent.get("file_path") else None,
                context_data=agent,
                success=True,
            )

    def get_session_intelligence(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive intelligence report for a session using PostgreSQL."""
        report = {
            "session_id": session_id,
            "files_affected": [],
            "symbols_discussed": [],
            "agents_utilized": [],
            "complexity_changes": {},
            "modification_timeline": [],
        }

        # Use dual-write adapter's PostgreSQL queries for enhanced data
        try:
            # Get code context data
            contexts = self.db_adapter.query_code_context(session_id)

            # Process files affected
            file_references = {}
            for context in contexts:
                file_path = context.get("file_path")
                if file_path:
                    file_references[file_path] = file_references.get(file_path, 0) + 1

            report["files_affected"] = [
                {"path": path, "references": count}
                for path, count in sorted(
                    file_references.items(), key=lambda x: x[1], reverse=True
                )
            ]

            # Get hot symbols (uses PostgreSQL aggregation)
            hot_symbols = self.db_adapter.query_hot_symbols(
                days=1
            )  # Recent session data
            report["symbols_discussed"] = [
                {
                    "name": symbol["symbol_name"],
                    "type": symbol["symbol_type"],
                    "mentions": symbol["reference_count"],
                }
                for symbol in hot_symbols[:20]  # Top 20
            ]

            # Get modification timeline from PostgreSQL
            with self.db_adapter.pg_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT timestamp, file_path, action, tool_used
                    FROM file_activity
                    WHERE session_id = %s
                    ORDER BY timestamp
                """,
                    (session_id,),
                )

                report["modification_timeline"] = [
                    {
                        "timestamp": str(row[0]),
                        "file": row[1],
                        "action": row[2],
                        "tool": row[3],
                    }
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            print(f"Error querying session intelligence: {e}")
            # Fallback to basic report structure
            pass

        return report

    def close(self):
        """Close database connections."""
        self.db_adapter.close()
