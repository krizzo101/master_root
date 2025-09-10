"""
Symbol tracking and analysis for code discussions.
"""

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, "/home/opsvi/master_root")
from scripts.proj_intel_reader import ProjectIntelReader


class SymbolTracker:
    """Tracks and analyzes symbol references across chat sessions."""

    def __init__(self, db_path: str = "/home/opsvi/master_root/chat_logs.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

        # Load symbol index
        self.symbol_index = self._load_symbol_index()
        self.reader = ProjectIntelReader("/home/opsvi/master_root/.proj-intel")

        # Cache for symbol metadata
        self.symbol_cache = {}

        # Symbol type detection patterns
        self.symbol_types = {
            "class": [
                "Base",
                "Model",
                "Schema",
                "Error",
                "Exception",
                "Manager",
                "Handler",
            ],
            "function": [
                "get_",
                "set_",
                "is_",
                "has_",
                "create_",
                "update_",
                "delete_",
                "process_",
            ],
            "constant": ["_CONSTANT", "_CONFIG", "_DEFAULT", "_MAX", "_MIN"],
            "method": [
                "__init__",
                "__str__",
                "__repr__",
                "__call__",
                "__enter__",
                "__exit__",
            ],
        }

    def _load_symbol_index(self) -> Dict[str, Any]:
        """Load the symbol index from project intelligence."""
        symbol_index_path = Path(
            "/home/opsvi/master_root/.proj-intel/symbol_index.json"
        )
        if symbol_index_path.exists():
            with open(symbol_index_path) as f:
                return json.load(f)
        return {}

    def track_symbol(
        self,
        symbol_name: str,
        session_id: str,
        message_id: str,
        context: str,
        reference_type: str = "mentioned",
    ) -> Dict[str, Any]:
        """
        Track a symbol reference in a chat message.

        Args:
            symbol_name: Name of the symbol
            session_id: Chat session ID
            message_id: Message ID
            context: Surrounding context
            reference_type: Type of reference (mentioned/modified/created/deleted)

        Returns:
            Symbol metadata and tracking info
        """
        # Get symbol metadata
        metadata = self.get_symbol_metadata(symbol_name)

        # Determine symbol type
        symbol_type = self._infer_symbol_type(symbol_name, metadata)

        # Get file location
        file_path, line_number = self._get_symbol_location(symbol_name)

        # Store in database
        self.db.execute(
            """
            INSERT INTO symbol_references
            (message_id, session_id, symbol_name, symbol_type, file_path, line_number, reference_type)
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
        self.db.commit()

        return {
            "symbol": symbol_name,
            "type": symbol_type,
            "file": file_path,
            "line": line_number,
            "metadata": metadata,
            "reference_type": reference_type,
        }

    def get_symbol_metadata(self, symbol_name: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a symbol."""
        if symbol_name in self.symbol_cache:
            return self.symbol_cache[symbol_name]

        metadata = {
            "name": symbol_name,
            "locations": [],
            "type": "unknown",
            "definitions": [],
            "references": [],
            "complexity": 0,
        }

        # Get from symbol index
        if symbol_name in self.symbol_index:
            index_data = self.symbol_index[symbol_name]

            # Handle different index formats
            if isinstance(index_data, dict):
                metadata["locations"] = index_data.get("locations", [])
                metadata["type"] = index_data.get("type", "unknown")
            elif isinstance(index_data, list):
                metadata["locations"] = index_data
            else:
                metadata["locations"] = [{"file": str(index_data)}]

        # Search in agent architecture
        for agent in self.reader.get_agent_architecture():
            if agent.get("name") == symbol_name:
                metadata["type"] = "agent"
                metadata["definitions"].append(
                    {
                        "file": agent.get("file_path"),
                        "methods": agent.get("methods", []),
                        "bases": agent.get("bases", []),
                        "docstring": agent.get("docstring_head"),
                    }
                )
                metadata["complexity"] = len(agent.get("methods", []))

        # Cache the result
        self.symbol_cache[symbol_name] = metadata
        return metadata

    def _infer_symbol_type(self, symbol_name: str, metadata: Dict) -> str:
        """Infer the type of a symbol based on naming patterns and metadata."""
        if metadata.get("type") != "unknown":
            return metadata["type"]

        # Check naming patterns
        for sym_type, patterns in self.symbol_types.items():
            for pattern in patterns:
                if pattern in symbol_name:
                    return sym_type

        # Check case patterns
        if symbol_name.isupper():
            return "constant"
        elif symbol_name[0].isupper():
            return "class"
        elif "_" in symbol_name:
            return "function"
        else:
            return "variable"

    def _get_symbol_location(
        self, symbol_name: str
    ) -> Tuple[Optional[str], Optional[int]]:
        """Get the primary file location for a symbol."""
        metadata = self.get_symbol_metadata(symbol_name)

        if metadata["locations"]:
            location = metadata["locations"][0]
            if isinstance(location, dict):
                return location.get("file"), location.get("line")
            else:
                return str(location), None

        return None, None

    def get_symbol_history(
        self, symbol_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get the discussion history for a symbol."""
        cursor = self.db.execute(
            """
            SELECT sr.*, cl.content, cl.timestamp
            FROM symbol_references sr
            LEFT JOIN chat_logs cl ON sr.message_id = cl.id
            WHERE sr.symbol_name = ?
            ORDER BY cl.timestamp DESC
            LIMIT ?
        """,
            (symbol_name, limit),
        )

        history = []
        for row in cursor:
            history.append(
                {
                    "session_id": row["session_id"],
                    "message_id": row["message_id"],
                    "timestamp": row["timestamp"],
                    "reference_type": row["reference_type"],
                    "file_path": row["file_path"],
                    "content_preview": row["content"][:200] if row["content"] else None,
                }
            )

        return history

    def get_hot_symbols(
        self, session_id: Optional[str] = None, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get the most discussed symbols."""
        query = """
            SELECT symbol_name, symbol_type, COUNT(*) as reference_count,
                   COUNT(DISTINCT session_id) as session_count,
                   COUNT(DISTINCT file_path) as file_count
            FROM symbol_references
            WHERE 1=1
        """
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if days:
            query += " AND datetime(timestamp) > datetime('now', '-' || ? || ' days')"
            params.append(days)

        query += """
            GROUP BY symbol_name, symbol_type
            ORDER BY reference_count DESC
            LIMIT 50
        """

        cursor = self.db.execute(query, params)

        hot_symbols = []
        for row in cursor:
            # Get additional metadata
            metadata = self.get_symbol_metadata(row["symbol_name"])

            hot_symbols.append(
                {
                    "name": row["symbol_name"],
                    "type": row["symbol_type"],
                    "references": row["reference_count"],
                    "sessions": row["session_count"],
                    "files": row["file_count"],
                    "complexity": metadata.get("complexity", 0),
                    "locations": len(metadata.get("locations", [])),
                }
            )

        return hot_symbols

    def get_symbol_relationships(self, symbol_name: str) -> Dict[str, Any]:
        """Get relationships between symbols (co-occurrence analysis)."""
        # Get sessions where this symbol was mentioned
        cursor = self.db.execute(
            """
            SELECT DISTINCT session_id
            FROM symbol_references
            WHERE symbol_name = ?
        """,
            (symbol_name,),
        )

        sessions = [row["session_id"] for row in cursor]

        if not sessions:
            return {"symbol": symbol_name, "related": []}

        # Find co-occurring symbols
        placeholders = ",".join("?" * len(sessions))
        cursor = self.db.execute(
            f"""
            SELECT symbol_name, COUNT(*) as cooccurrence_count
            FROM symbol_references
            WHERE session_id IN ({placeholders})
              AND symbol_name != ?
            GROUP BY symbol_name
            ORDER BY cooccurrence_count DESC
            LIMIT 20
        """,
            sessions + [symbol_name],
        )

        related = []
        for row in cursor:
            related_metadata = self.get_symbol_metadata(row["symbol_name"])
            related.append(
                {
                    "name": row["symbol_name"],
                    "cooccurrences": row["cooccurrence_count"],
                    "type": related_metadata.get("type", "unknown"),
                    "strength": row["cooccurrence_count"] / len(sessions),
                }
            )

        return {"symbol": symbol_name, "sessions": len(sessions), "related": related}

    def analyze_symbol_evolution(self, symbol_name: str) -> Dict[str, Any]:
        """Analyze how a symbol evolved over time."""
        history = self.get_symbol_history(symbol_name)

        if not history:
            return {"symbol": symbol_name, "evolution": []}

        evolution = {
            "symbol": symbol_name,
            "first_mention": history[-1]["timestamp"] if history else None,
            "last_mention": history[0]["timestamp"] if history else None,
            "total_references": len(history),
            "reference_types": defaultdict(int),
            "sessions": set(),
            "files_affected": set(),
            "timeline": [],
        }

        for entry in history:
            evolution["reference_types"][entry["reference_type"]] += 1
            evolution["sessions"].add(entry["session_id"])
            if entry["file_path"]:
                evolution["files_affected"].add(entry["file_path"])

        # Create timeline
        timeline_data = defaultdict(lambda: {"count": 0, "types": defaultdict(int)})
        for entry in history:
            if entry["timestamp"]:
                date = entry["timestamp"].split("T")[0]
                timeline_data[date]["count"] += 1
                timeline_data[date]["types"][entry["reference_type"]] += 1

        evolution["timeline"] = [
            {"date": date, "count": data["count"], "types": dict(data["types"])}
            for date, data in sorted(timeline_data.items())
        ]

        evolution["sessions"] = len(evolution["sessions"])
        evolution["files_affected"] = len(evolution["files_affected"])
        evolution["reference_types"] = dict(evolution["reference_types"])

        return evolution

    def find_undefined_symbols(self, session_id: str) -> List[Dict[str, str]]:
        """Find symbols discussed but not found in the codebase."""
        cursor = self.db.execute(
            """
            SELECT DISTINCT symbol_name
            FROM symbol_references
            WHERE session_id = ?
              AND (file_path IS NULL OR file_path = '')
        """,
            (session_id,),
        )

        undefined = []
        for row in cursor:
            symbol_name = row["symbol_name"]
            # Double-check in symbol index
            if symbol_name not in self.symbol_index:
                undefined.append(
                    {
                        "name": symbol_name,
                        "status": "undefined",
                        "suggestion": self._suggest_similar_symbol(symbol_name),
                    }
                )

        return undefined

    def _suggest_similar_symbol(self, symbol_name: str) -> Optional[str]:
        """Suggest a similar existing symbol."""
        symbol_lower = symbol_name.lower()
        best_match = None
        best_score = 0

        for existing_symbol in self.symbol_index:
            # Simple similarity check
            if (
                symbol_lower in existing_symbol.lower()
                or existing_symbol.lower() in symbol_lower
            ):
                score = len(set(symbol_lower) & set(existing_symbol.lower()))
                if score > best_score:
                    best_score = score
                    best_match = existing_symbol

        return best_match

    def generate_symbol_report(
        self, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive symbol analysis report."""
        report = {
            "summary": {
                "total_symbols": 0,
                "unique_symbols": 0,
                "undefined_symbols": 0,
                "most_referenced": None,
                "most_modified": None,
            },
            "by_type": defaultdict(int),
            "by_reference_type": defaultdict(int),
            "hot_symbols": [],
            "undefined": [],
            "evolution": [],
        }

        # Get basic stats
        query = """
            SELECT COUNT(*) as total, COUNT(DISTINCT symbol_name) as unique_count
            FROM symbol_references
        """
        params = []
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        cursor = self.db.execute(query, params)
        row = cursor.fetchone()
        report["summary"]["total_symbols"] = row["total"]
        report["summary"]["unique_symbols"] = row["unique_count"]

        # Get type distribution
        query = """
            SELECT symbol_type, COUNT(*) as count
            FROM symbol_references
        """
        if session_id:
            query += " WHERE session_id = ?"
        query += " GROUP BY symbol_type"

        cursor = self.db.execute(query, params)
        for row in cursor:
            report["by_type"][row["symbol_type"]] = row["count"]

        # Get reference type distribution
        query = """
            SELECT reference_type, COUNT(*) as count
            FROM symbol_references
        """
        if session_id:
            query += " WHERE session_id = ?"
        query += " GROUP BY reference_type"

        cursor = self.db.execute(query, params)
        for row in cursor:
            report["by_reference_type"][row["reference_type"]] = row["count"]

        # Get hot symbols
        report["hot_symbols"] = self.get_hot_symbols(session_id, days=30)

        # Get undefined symbols if session specified
        if session_id:
            report["undefined"] = self.find_undefined_symbols(session_id)
            report["summary"]["undefined_symbols"] = len(report["undefined"])

        # Convert defaultdicts to regular dicts
        report["by_type"] = dict(report["by_type"])
        report["by_reference_type"] = dict(report["by_reference_type"])

        return report

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
