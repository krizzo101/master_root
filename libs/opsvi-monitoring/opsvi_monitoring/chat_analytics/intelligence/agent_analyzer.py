"""
Agent architecture analysis and correlation with chat activity.
"""

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, "/home/opsvi/master_root")
from scripts.proj_intel_reader import ProjectIntelReader


class AgentAnalyzer:
    """Analyzes agent architecture and usage patterns in chat sessions."""

    def __init__(self, db_path: str = "/home/opsvi/master_root/chat_logs.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

        self.reader = ProjectIntelReader("/home/opsvi/master_root/.proj-intel")

        # Cache for agent data
        self.agent_cache = {}
        self.agent_hierarchy = {}

        # Load all agents on initialization
        self._load_agents()

    def _load_agents(self):
        """Load all agent architectures from project intelligence."""
        for agent_data in self.reader.get_agent_architecture():
            agent_name = agent_data.get("name")
            if agent_name:
                self.agent_cache[agent_name] = {
                    "name": agent_name,
                    "file_path": agent_data.get("file_path"),
                    "bases": agent_data.get("bases", []),
                    "methods": agent_data.get("methods", []),
                    "docstring": agent_data.get("docstring_head"),
                    "complexity": len(agent_data.get("methods", [])),
                    "line_count": agent_data.get("line_count", 0),
                }

                # Build hierarchy
                for base in agent_data.get("bases", []):
                    if base not in self.agent_hierarchy:
                        self.agent_hierarchy[base] = []
                    self.agent_hierarchy[base].append(agent_name)

    def track_agent_usage(
        self, agent_name: str, session_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track agent usage in a chat session.

        Args:
            agent_name: Name of the agent
            session_id: Chat session ID
            context: Usage context (methods called, etc.)

        Returns:
            Agent usage information
        """
        timestamp = datetime.now().isoformat()

        # Get agent metadata
        agent_data = self.get_agent_metadata(agent_name)

        # Extract methods invoked from context
        methods_invoked = context.get("methods_invoked", [])

        # Store in database
        self.db.execute(
            """
            INSERT INTO agent_usage
            (session_id, timestamp, agent_class, file_path, methods_invoked, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                timestamp,
                agent_name,
                agent_data.get("file_path"),
                json.dumps(methods_invoked),
                json.dumps(context),
            ),
        )
        self.db.commit()

        return {
            "agent": agent_name,
            "session_id": session_id,
            "timestamp": timestamp,
            "metadata": agent_data,
            "methods_invoked": methods_invoked,
        }

    def get_agent_metadata(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive metadata for an agent."""
        if agent_name in self.agent_cache:
            return self.agent_cache[agent_name]

        # Try to find in project intelligence
        for agent_data in self.reader.get_agent_architecture():
            if agent_data.get("name") == agent_name:
                metadata = {
                    "name": agent_name,
                    "file_path": agent_data.get("file_path"),
                    "bases": agent_data.get("bases", []),
                    "methods": agent_data.get("methods", []),
                    "docstring": agent_data.get("docstring_head"),
                    "complexity": len(agent_data.get("methods", [])),
                    "line_count": agent_data.get("line_count", 0),
                }
                self.agent_cache[agent_name] = metadata
                return metadata

        return {"name": agent_name, "found": False}

    def get_agent_hierarchy(self) -> Dict[str, List[str]]:
        """Get the complete agent inheritance hierarchy."""
        return self.agent_hierarchy

    def analyze_agent_utilization(
        self, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze agent utilization patterns.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            Agent utilization analysis
        """
        query = """
            SELECT agent_class, COUNT(*) as usage_count,
                   COUNT(DISTINCT session_id) as session_count
            FROM agent_usage
        """
        params = []

        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        query += " GROUP BY agent_class ORDER BY usage_count DESC"

        cursor = self.db.execute(query, params)

        utilization = {
            "most_used": [],
            "by_complexity": [],
            "by_methods": defaultdict(int),
            "inheritance_patterns": {},
            "summary": {
                "total_agents": len(self.agent_cache),
                "agents_used": 0,
                "total_invocations": 0,
            },
        }

        for row in cursor:
            agent_name = row["agent_class"]
            usage_count = row["usage_count"]
            session_count = row["session_count"]

            # Get agent metadata
            metadata = self.get_agent_metadata(agent_name)

            agent_info = {
                "name": agent_name,
                "usage_count": usage_count,
                "session_count": session_count,
                "complexity": metadata.get("complexity", 0),
                "methods": len(metadata.get("methods", [])),
                "file": metadata.get("file_path"),
            }

            utilization["most_used"].append(agent_info)
            utilization["summary"]["agents_used"] += 1
            utilization["summary"]["total_invocations"] += usage_count

        # Sort by complexity
        utilization["by_complexity"] = sorted(
            utilization["most_used"], key=lambda x: x["complexity"], reverse=True
        )[:10]

        # Analyze method usage
        self._analyze_method_usage(utilization, session_id)

        # Analyze inheritance patterns
        self._analyze_inheritance_patterns(utilization)

        return utilization

    def _analyze_method_usage(self, utilization: Dict, session_id: Optional[str]):
        """Analyze which methods are most commonly invoked."""
        query = """
            SELECT methods_invoked FROM agent_usage
        """
        params = []

        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        cursor = self.db.execute(query, params)

        method_count = defaultdict(int)
        for row in cursor:
            methods = json.loads(row["methods_invoked"] or "[]")
            for method in methods:
                method_count[method] += 1

        utilization["by_methods"] = dict(
            sorted(method_count.items(), key=lambda x: x[1], reverse=True)[:20]
        )

    def _analyze_inheritance_patterns(self, utilization: Dict):
        """Analyze inheritance patterns in agent usage."""
        # Find which base classes are most extended
        base_usage = defaultdict(int)
        for agent_name in [a["name"] for a in utilization["most_used"]]:
            metadata = self.get_agent_metadata(agent_name)
            for base in metadata.get("bases", []):
                base_usage[base] += 1

        utilization["inheritance_patterns"] = {
            "most_extended": dict(
                sorted(base_usage.items(), key=lambda x: x[1], reverse=True)
            ),
            "hierarchy_depth": self._calculate_hierarchy_depth(),
        }

    def _calculate_hierarchy_depth(self) -> Dict[str, int]:
        """Calculate the depth of inheritance hierarchy."""
        depths = {}

        def get_depth(agent_name: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()

            if agent_name in visited:
                return 0  # Circular inheritance

            visited.add(agent_name)

            metadata = self.get_agent_metadata(agent_name)
            bases = metadata.get("bases", [])

            if not bases:
                return 0

            max_depth = 0
            for base in bases:
                depth = get_depth(base, visited.copy())
                max_depth = max(max_depth, depth)

            return max_depth + 1

        for agent_name in self.agent_cache:
            depths[agent_name] = get_depth(agent_name)

        return dict(sorted(depths.items(), key=lambda x: x[1], reverse=True)[:10])

    def find_related_agents(self, agent_name: str) -> Dict[str, Any]:
        """Find agents related through inheritance or usage patterns."""
        related = {
            "agent": agent_name,
            "parents": [],
            "children": [],
            "siblings": [],
            "frequently_used_together": [],
        }

        metadata = self.get_agent_metadata(agent_name)

        # Get parents (base classes)
        related["parents"] = metadata.get("bases", [])

        # Get children (classes that extend this agent)
        related["children"] = self.agent_hierarchy.get(agent_name, [])

        # Get siblings (classes with same base)
        siblings = set()
        for base in related["parents"]:
            for child in self.agent_hierarchy.get(base, []):
                if child != agent_name:
                    siblings.add(child)
        related["siblings"] = list(siblings)

        # Find frequently used together
        cursor = self.db.execute(
            """
            SELECT a2.agent_class, COUNT(*) as cooccurrence_count
            FROM agent_usage a1
            JOIN agent_usage a2 ON a1.session_id = a2.session_id
            WHERE a1.agent_class = ? AND a2.agent_class != ?
            GROUP BY a2.agent_class
            ORDER BY cooccurrence_count DESC
            LIMIT 10
        """,
            (agent_name, agent_name),
        )

        for row in cursor:
            related["frequently_used_together"].append(
                {
                    "agent": row["agent_class"],
                    "cooccurrences": row["cooccurrence_count"],
                }
            )

        return related

    def get_agent_evolution(self, agent_name: str) -> Dict[str, Any]:
        """Track how an agent has been discussed and modified over time."""
        evolution = {
            "agent": agent_name,
            "first_mention": None,
            "last_mention": None,
            "total_mentions": 0,
            "sessions": [],
            "methods_evolution": {},
            "modification_timeline": [],
        }

        # Get usage history
        cursor = self.db.execute(
            """
            SELECT * FROM agent_usage
            WHERE agent_class = ?
            ORDER BY timestamp
        """,
            (agent_name,),
        )

        sessions = set()
        method_usage_over_time = defaultdict(list)

        for row in cursor:
            timestamp = row["timestamp"]
            session_id = row["session_id"]
            methods = json.loads(row["methods_invoked"] or "[]")

            if not evolution["first_mention"]:
                evolution["first_mention"] = timestamp
            evolution["last_mention"] = timestamp
            evolution["total_mentions"] += 1
            sessions.add(session_id)

            for method in methods:
                method_usage_over_time[method].append(timestamp)

        evolution["sessions"] = list(sessions)
        evolution["methods_evolution"] = {
            method: {
                "first_use": times[0],
                "last_use": times[-1],
                "total_uses": len(times),
            }
            for method, times in method_usage_over_time.items()
        }

        # Get file modification history
        metadata = self.get_agent_metadata(agent_name)
        if metadata.get("file_path"):
            cursor = self.db.execute(
                """
                SELECT * FROM file_activity
                WHERE file_path = ?
                ORDER BY timestamp
            """,
                (metadata["file_path"],),
            )

            for row in cursor:
                evolution["modification_timeline"].append(
                    {
                        "timestamp": row["timestamp"],
                        "action": row["action"],
                        "tool": row["tool_used"],
                    }
                )

        return evolution

    def detect_agent_patterns(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Detect patterns in agent usage."""
        patterns = {
            "usage_patterns": [],
            "collaboration_patterns": [],
            "inheritance_patterns": [],
            "complexity_correlation": {},
            "recommendations": [],
        }

        # Analyze usage patterns
        query = """
            SELECT agent_class, COUNT(*) as count,
                   GROUP_CONCAT(DISTINCT session_id) as sessions
            FROM agent_usage
        """
        params = []

        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        query += " GROUP BY agent_class"

        cursor = self.db.execute(query, params)

        usage_data = []
        for row in cursor:
            agent_name = row["agent_class"]
            metadata = self.get_agent_metadata(agent_name)

            usage_data.append(
                {
                    "agent": agent_name,
                    "count": row["count"],
                    "complexity": metadata.get("complexity", 0),
                    "methods": len(metadata.get("methods", [])),
                    "bases": len(metadata.get("bases", [])),
                }
            )

        # Find patterns
        if usage_data:
            # High complexity agents that are frequently used
            high_complexity_frequent = [
                a for a in usage_data if a["complexity"] > 10 and a["count"] > 5
            ]
            if high_complexity_frequent:
                patterns["usage_patterns"].append(
                    {
                        "pattern": "high_complexity_frequent_use",
                        "agents": high_complexity_frequent,
                        "insight": "Complex agents being frequently used - consider simplification",
                    }
                )

            # Agents with many bases (deep inheritance)
            deep_inheritance = [a for a in usage_data if a["bases"] > 3]
            if deep_inheritance:
                patterns["inheritance_patterns"].append(
                    {
                        "pattern": "deep_inheritance",
                        "agents": deep_inheritance,
                        "insight": "Deep inheritance hierarchy detected - may impact maintainability",
                    }
                )

        # Find collaboration patterns
        patterns["collaboration_patterns"] = self._find_collaboration_patterns(
            session_id
        )

        # Generate recommendations
        patterns["recommendations"] = self._generate_agent_recommendations(patterns)

        return patterns

    def _find_collaboration_patterns(self, session_id: Optional[str]) -> List[Dict]:
        """Find patterns in how agents collaborate."""
        query = """
            SELECT a1.agent_class as agent1, a2.agent_class as agent2,
                   COUNT(*) as collaboration_count
            FROM agent_usage a1
            JOIN agent_usage a2 ON a1.session_id = a2.session_id
                AND a1.timestamp < a2.timestamp
        """
        params = []

        if session_id:
            query += " WHERE a1.session_id = ?"
            params.append(session_id)

        query += """
            GROUP BY agent1, agent2
            HAVING collaboration_count > 2
            ORDER BY collaboration_count DESC
            LIMIT 20
        """

        cursor = self.db.execute(query, params)

        collaborations = []
        for row in cursor:
            collaborations.append(
                {
                    "agent1": row["agent1"],
                    "agent2": row["agent2"],
                    "frequency": row["collaboration_count"],
                    "pattern": "sequential_collaboration",
                }
            )

        return collaborations

    def _generate_agent_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on agent analysis."""
        recommendations = []

        # Check for high complexity
        high_complexity = [
            p
            for p in patterns.get("usage_patterns", [])
            if p.get("pattern") == "high_complexity_frequent_use"
        ]
        if high_complexity:
            recommendations.append(
                "Consider refactoring frequently used complex agents for better maintainability"
            )

        # Check for deep inheritance
        deep_inheritance = [
            p
            for p in patterns.get("inheritance_patterns", [])
            if p.get("pattern") == "deep_inheritance"
        ]
        if deep_inheritance:
            recommendations.append(
                "Deep inheritance hierarchies detected. Consider composition over inheritance"
            )

        # Check for collaboration patterns
        if len(patterns.get("collaboration_patterns", [])) > 10:
            recommendations.append(
                "Multiple agent collaboration patterns detected. Consider creating orchestrator agents"
            )

        return recommendations

    def generate_agent_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive agent analysis report."""
        report = {
            "summary": {
                "total_agents": len(self.agent_cache),
                "agents_used": 0,
                "total_invocations": 0,
                "average_complexity": 0,
            },
            "utilization": {},
            "patterns": {},
            "hierarchy": {},
            "hot_agents": [],
            "recommendations": [],
        }

        # Get utilization analysis
        report["utilization"] = self.analyze_agent_utilization(session_id)
        report["summary"]["agents_used"] = report["utilization"]["summary"][
            "agents_used"
        ]
        report["summary"]["total_invocations"] = report["utilization"]["summary"][
            "total_invocations"
        ]

        # Calculate average complexity
        if self.agent_cache:
            total_complexity = sum(
                a.get("complexity", 0) for a in self.agent_cache.values()
            )
            report["summary"]["average_complexity"] = total_complexity / len(
                self.agent_cache
            )

        # Get patterns
        report["patterns"] = self.detect_agent_patterns(session_id)

        # Get hierarchy
        report["hierarchy"] = self.get_agent_hierarchy()

        # Get hot agents
        report["hot_agents"] = report["utilization"]["most_used"][:10]

        # Compile recommendations
        report["recommendations"] = report["patterns"].get(
            "recommendations", []
        ) + self._generate_overall_recommendations(report)

        return report

    def _generate_overall_recommendations(self, report: Dict) -> List[str]:
        """Generate overall recommendations from complete report."""
        recommendations = []

        # Check utilization rate
        utilization_rate = (
            (report["summary"]["agents_used"] / report["summary"]["total_agents"])
            if report["summary"]["total_agents"] > 0
            else 0
        )

        if utilization_rate < 0.2:
            recommendations.append(
                f"Only {utilization_rate*100:.1f}% of agents are being used. Review agent architecture for redundancy"
            )

        # Check complexity
        if report["summary"]["average_complexity"] > 15:
            recommendations.append(
                "High average agent complexity detected. Consider breaking down complex agents"
            )

        return recommendations

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
