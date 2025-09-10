"""
Change tracking and detection for code evolution during chat sessions.
"""

import difflib
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, "/home/opsvi/master_root")
from scripts.proj_intel_reader import ProjectIntelReader


class ChangeTracker:
    """Tracks code changes and evolution during chat sessions."""

    def __init__(self, db_path: str = "/home/opsvi/master_root/chat_logs.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

        self.reader = ProjectIntelReader("/home/opsvi/master_root/.proj-intel")

        # Cache for file states
        self.file_state_cache = {}
        self.baseline_cache = {}

        # Change patterns
        self.change_patterns = {
            "refactor": ["rename", "extract", "inline", "move"],
            "feature": ["add", "implement", "create", "new"],
            "fix": ["fix", "patch", "resolve", "correct"],
            "optimize": ["optimize", "improve", "enhance", "speed"],
            "cleanup": ["clean", "remove", "delete", "deprecate"],
            "document": ["document", "comment", "annotate", "describe"],
        }

    def establish_baseline(self, session_id: str) -> Dict[str, Any]:
        """
        Establish a baseline state for a session.

        Args:
            session_id: Session identifier

        Returns:
            Baseline state dictionary
        """
        baseline = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "metrics": {
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_lines": 0,
            },
        }

        # Get file elements from project intelligence
        for file_elem in self.reader.get_file_elements(min_only=True):
            file_path = file_elem.get("file_path")
            if file_path:
                baseline["files"][file_path] = {
                    "hash": file_elem.get("content_hash"),
                    "lines": file_elem.get("line_count", 0),
                    "functions": file_elem.get("fn_count", 0),
                    "classes": file_elem.get("class_count", 0),
                    "imports": file_elem.get("import_count", 0),
                }

                baseline["metrics"]["total_files"] += 1
                baseline["metrics"]["total_functions"] += file_elem.get("fn_count", 0)
                baseline["metrics"]["total_classes"] += file_elem.get("class_count", 0)
                baseline["metrics"]["total_lines"] += file_elem.get("line_count", 0)

        # Cache the baseline
        self.baseline_cache[session_id] = baseline

        return baseline

    def track_change(
        self,
        session_id: str,
        file_path: str,
        change_type: str,
        tool_used: str,
        content: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Track a code change.

        Args:
            session_id: Session identifier
            file_path: Path to changed file
            change_type: Type of change (create/modify/delete)
            tool_used: Tool that made the change
            content: New content (optional)
            message_id: Associated message ID

        Returns:
            Change tracking information
        """
        timestamp = datetime.now().isoformat()

        # Get before state
        before_state = self._get_file_state(file_path)
        before_hash = before_state.get("hash") if before_state else None

        # Calculate after state if content provided
        after_hash = None
        if content:
            after_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Detect affected symbols
        affected_symbols = self._detect_affected_symbols(file_path, content)

        # Store in database
        self.db.execute(
            """
            INSERT INTO file_activity
            (session_id, timestamp, file_path, action, tool_used,
             functions_affected, classes_affected, before_hash, after_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                timestamp,
                file_path,
                change_type,
                tool_used,
                json.dumps(affected_symbols.get("functions", [])),
                json.dumps(affected_symbols.get("classes", [])),
                before_hash,
                after_hash,
            ),
        )
        self.db.commit()

        # Update cache
        if after_hash:
            self.file_state_cache[file_path] = {
                "hash": after_hash,
                "timestamp": timestamp,
                "content": content,
            }

        return {
            "file": file_path,
            "change_type": change_type,
            "tool": tool_used,
            "before_hash": before_hash,
            "after_hash": after_hash,
            "affected_symbols": affected_symbols,
            "timestamp": timestamp,
        }

    def _get_file_state(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a file."""
        if file_path in self.file_state_cache:
            return self.file_state_cache[file_path]

        # Try to get from project intelligence
        items = self.reader.read_by_path(file_path)
        for item in items:
            if (
                item.get("kind") == "collector_item"
                and item.get("collector") == "FileElementsCollector"
            ):
                data = item.get("data", {})
                state = {
                    "hash": data.get("content_hash"),
                    "lines": data.get("line_count"),
                    "functions": data.get("fn_count"),
                    "classes": data.get("class_count"),
                }
                self.file_state_cache[file_path] = state
                return state

        return None

    def _detect_affected_symbols(
        self, file_path: str, content: Optional[str]
    ) -> Dict[str, List[str]]:
        """Detect symbols affected by a change."""
        affected = {"functions": [], "classes": []}

        if not content:
            return affected

        # Simple pattern matching for function and class definitions
        import re

        func_pattern = re.compile(r"def\s+(\w+)\s*\(")
        class_pattern = re.compile(r"class\s+(\w+)(?:\(|:)")

        affected["functions"] = func_pattern.findall(content)
        affected["classes"] = class_pattern.findall(content)

        return affected

    def get_file_evolution(
        self, file_path: str, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the evolution history of a file."""
        query = """
            SELECT * FROM file_activity
            WHERE file_path = ?
        """
        params = [file_path]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp"

        cursor = self.db.execute(query, params)

        evolution = []
        for row in cursor:
            evolution.append(
                {
                    "session_id": row["session_id"],
                    "timestamp": row["timestamp"],
                    "action": row["action"],
                    "tool": row["tool_used"],
                    "functions_affected": json.loads(row["functions_affected"] or "[]"),
                    "classes_affected": json.loads(row["classes_affected"] or "[]"),
                    "before_hash": row["before_hash"],
                    "after_hash": row["after_hash"],
                }
            )

        return evolution

    def detect_change_patterns(self, session_id: str) -> Dict[str, Any]:
        """Detect patterns in code changes during a session."""
        cursor = self.db.execute(
            """
            SELECT * FROM file_activity
            WHERE session_id = ?
            ORDER BY timestamp
        """,
            (session_id,),
        )

        patterns = {
            "total_changes": 0,
            "files_changed": set(),
            "change_types": defaultdict(int),
            "tools_used": defaultdict(int),
            "change_categories": defaultdict(list),
            "hot_files": [],
            "change_velocity": [],
        }

        changes = []
        for row in cursor:
            change = {
                "file": row["file_path"],
                "action": row["action"],
                "tool": row["tool_used"],
                "timestamp": row["timestamp"],
                "functions": json.loads(row["functions_affected"] or "[]"),
                "classes": json.loads(row["classes_affected"] or "[]"),
            }
            changes.append(change)

            patterns["total_changes"] += 1
            patterns["files_changed"].add(row["file_path"])
            patterns["change_types"][row["action"]] += 1
            patterns["tools_used"][row["tool_used"]] += 1

        # Categorize changes
        for change in changes:
            category = self._categorize_change(change)
            if category:
                patterns["change_categories"][category].append(change["file"])

        # Find hot files (most changed)
        file_change_count = defaultdict(int)
        for change in changes:
            file_change_count[change["file"]] += 1

        patterns["hot_files"] = sorted(
            [{"file": f, "changes": c} for f, c in file_change_count.items()],
            key=lambda x: x["changes"],
            reverse=True,
        )[:10]

        # Calculate change velocity (changes over time)
        if changes:
            time_buckets = defaultdict(int)
            first_time = datetime.fromisoformat(changes[0]["timestamp"])

            for change in changes:
                change_time = datetime.fromisoformat(change["timestamp"])
                minutes_elapsed = (change_time - first_time).total_seconds() / 60
                bucket = int(minutes_elapsed / 5)  # 5-minute buckets
                time_buckets[bucket] += 1

            patterns["change_velocity"] = [
                {"bucket": b * 5, "changes": c} for b, c in sorted(time_buckets.items())
            ]

        # Convert sets and defaultdicts for JSON serialization
        patterns["files_changed"] = len(patterns["files_changed"])
        patterns["change_types"] = dict(patterns["change_types"])
        patterns["tools_used"] = dict(patterns["tools_used"])
        patterns["change_categories"] = {
            k: list(set(v)) for k, v in patterns["change_categories"].items()
        }

        return patterns

    def _categorize_change(self, change: Dict) -> Optional[str]:
        """Categorize a change based on patterns."""
        # Check action and tool patterns
        action = change["action"].lower()

        for category, keywords in self.change_patterns.items():
            for keyword in keywords:
                if keyword in action:
                    return category

        # Default categorization based on action
        if action in ["create", "write"]:
            return "feature"
        elif action in ["modify", "edit"]:
            return "refactor"
        elif action in ["delete", "remove"]:
            return "cleanup"

        return None

    def calculate_impact_score(self, session_id: str) -> Dict[str, Any]:
        """Calculate the impact score of changes in a session."""
        baseline = self.baseline_cache.get(session_id)
        if not baseline:
            baseline = self.establish_baseline(session_id)

        # Get current state
        current_state = self._get_current_state()

        impact = {
            "files": {"added": 0, "modified": 0, "deleted": 0},
            "metrics": {
                "lines_added": 0,
                "lines_removed": 0,
                "functions_added": 0,
                "functions_removed": 0,
                "classes_added": 0,
                "classes_removed": 0,
            },
            "complexity_change": 0,
            "impact_score": 0,
        }

        # Compare baseline with current
        baseline_files = set(baseline["files"].keys())
        current_files = set(current_state["files"].keys())

        impact["files"]["added"] = len(current_files - baseline_files)
        impact["files"]["deleted"] = len(baseline_files - current_files)

        for file_path in current_files & baseline_files:
            if (
                current_state["files"][file_path]["hash"]
                != baseline["files"][file_path]["hash"]
            ):
                impact["files"]["modified"] += 1

                # Calculate metric changes
                for metric in ["lines", "functions", "classes"]:
                    old_val = baseline["files"][file_path].get(metric, 0)
                    new_val = current_state["files"][file_path].get(metric, 0)
                    diff = new_val - old_val

                    if diff > 0:
                        impact["metrics"][f"{metric}_added"] += diff
                    else:
                        impact["metrics"][f"{metric}_removed"] += abs(diff)

        # Calculate impact score
        weights = {
            "file_added": 10,
            "file_modified": 5,
            "file_deleted": 8,
            "function_added": 3,
            "function_removed": 2,
            "class_added": 5,
            "class_removed": 4,
        }

        score = (
            impact["files"]["added"] * weights["file_added"]
            + impact["files"]["modified"] * weights["file_modified"]
            + impact["files"]["deleted"] * weights["file_deleted"]
            + impact["metrics"]["functions_added"] * weights["function_added"]
            + impact["metrics"]["functions_removed"] * weights["function_removed"]
            + impact["metrics"]["classes_added"] * weights["class_added"]
            + impact["metrics"]["classes_removed"] * weights["class_removed"]
        )

        impact["impact_score"] = score

        return impact

    def _get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the codebase."""
        state = {
            "files": {},
            "metrics": {
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_lines": 0,
            },
        }

        # Get from project intelligence
        for file_elem in self.reader.get_file_elements(min_only=True):
            file_path = file_elem.get("file_path")
            if file_path:
                # Check if we have a more recent version in cache
                if file_path in self.file_state_cache:
                    cached = self.file_state_cache[file_path]
                    state["files"][file_path] = cached
                else:
                    state["files"][file_path] = {
                        "hash": file_elem.get("content_hash"),
                        "lines": file_elem.get("line_count", 0),
                        "functions": file_elem.get("fn_count", 0),
                        "classes": file_elem.get("class_count", 0),
                        "imports": file_elem.get("import_count", 0),
                    }

                state["metrics"]["total_files"] += 1
                state["metrics"]["total_functions"] += state["files"][file_path].get(
                    "functions", 0
                )
                state["metrics"]["total_classes"] += state["files"][file_path].get(
                    "classes", 0
                )
                state["metrics"]["total_lines"] += state["files"][file_path].get(
                    "lines", 0
                )

        return state

    def generate_change_report(self, session_id: str) -> Dict[str, Any]:
        """Generate a comprehensive change report for a session."""
        report = {
            "session_id": session_id,
            "summary": {"total_changes": 0, "files_affected": 0, "impact_score": 0},
            "patterns": {},
            "timeline": [],
            "hot_files": [],
            "impact": {},
            "recommendations": [],
        }

        # Get change patterns
        report["patterns"] = self.detect_change_patterns(session_id)
        report["summary"]["total_changes"] = report["patterns"]["total_changes"]
        report["summary"]["files_affected"] = report["patterns"]["files_changed"]

        # Get impact analysis
        report["impact"] = self.calculate_impact_score(session_id)
        report["summary"]["impact_score"] = report["impact"]["impact_score"]

        # Get hot files
        report["hot_files"] = report["patterns"]["hot_files"]

        # Get timeline
        cursor = self.db.execute(
            """
            SELECT timestamp, file_path, action, tool_used
            FROM file_activity
            WHERE session_id = ?
            ORDER BY timestamp
        """,
            (session_id,),
        )

        for row in cursor:
            report["timeline"].append(
                {
                    "timestamp": row["timestamp"],
                    "file": row["file_path"],
                    "action": row["action"],
                    "tool": row["tool_used"],
                }
            )

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on change analysis."""
        recommendations = []

        # Check for high change velocity
        if report["patterns"]["total_changes"] > 50:
            recommendations.append(
                "High change volume detected. Consider breaking changes into smaller commits."
            )

        # Check for hot files
        if report["hot_files"] and report["hot_files"][0]["changes"] > 10:
            recommendations.append(
                f"File {report['hot_files'][0]['file']} changed {report['hot_files'][0]['changes']} times. Consider refactoring."
            )

        # Check impact score
        if report["impact"]["impact_score"] > 100:
            recommendations.append(
                "High impact changes detected. Ensure comprehensive testing before deployment."
            )

        # Check for deletions
        if report["impact"]["files"]["deleted"] > 5:
            recommendations.append(
                "Multiple files deleted. Verify dependencies are updated."
            )

        return recommendations

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
