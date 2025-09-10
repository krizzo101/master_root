"""
Agent Network Analyzer

Analyzes and visualizes the network of agent relationships, communication patterns,
and collaboration structures within agent swarms.
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class AgentRelationship:
    """Represents a relationship between two agents."""

    source_session: str
    target_session: str
    relationship_type: str  # spawn, communication, coordination, handoff
    strength: float  # 0.0 to 1.0
    first_seen: float
    last_seen: float
    interaction_count: int = 0
    evidence: List[str] = field(default_factory=list)


@dataclass
class NetworkMetrics:
    """Network analysis metrics for agent collaboration."""

    total_nodes: int = 0
    total_edges: int = 0
    max_depth: int = 0
    clustering_coefficient: float = 0.0
    central_agents: List[str] = field(default_factory=list)
    collaboration_efficiency: float = 0.0
    active_chains: List[List[str]] = field(default_factory=list)


class AgentNetworkAnalyzer:
    """
    Analyzes agent collaboration networks and communication patterns.

    Provides insights into:
    - Who spawns whom (hierarchical structure)
    - Who communicates with whom (collaboration patterns)
    - Collaboration efficiency and bottlenecks
    - Agent centrality and influence
    - Task handoff chains
    """

    def __init__(self, settings):
        self.settings = settings
        self.relationships: Dict[Tuple[str, str], AgentRelationship] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "spawn_count": 0,
                "spawned_by_count": 0,
                "communication_partners": set(),
                "files_shared": set(),
                "centrality_score": 0.0,
                "last_activity": 0.0,
            }
        )

        # Network analysis cache
        self.cached_analysis: Optional[NetworkMetrics] = None
        self.cache_timestamp: float = 0.0
        self.cache_validity_seconds = 5.0

    async def process_entry(self, session_id: str, entry: Dict):
        """Process a log entry to extract network relationship information."""
        timestamp = self._parse_timestamp(entry.get("timestamp", ""))

        # Update agent activity
        self.agent_metrics[session_id]["last_activity"] = timestamp

        # Look for relationship-creating events
        message = entry.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "name" in item:
                    await self._process_tool_relationship(session_id, item, timestamp)

    async def _process_tool_relationship(
        self, session_id: str, tool_item: Dict, timestamp: float
    ):
        """Process tool usage to identify relationships."""
        tool_name = tool_item["name"]
        tool_input = tool_item.get("input", {})

        if tool_name == "Task":
            # Agent spawning relationship
            agent_type = tool_input.get("subagent_type", "unknown")

            # Create spawning relationship (we'll map to actual session when available)
            await self._add_relationship(
                source=session_id,
                target=f"spawn_{agent_type}_{timestamp}",  # Placeholder until actual session known
                relationship_type="spawn",
                strength=0.9,
                timestamp=timestamp,
                evidence=[f"Spawned {agent_type} agent"],
            )

            self.agent_metrics[session_id]["spawn_count"] += 1

        elif "claude-code-wrapper" in tool_name:
            # Claude Code wrapper spawning
            task_desc = tool_input.get("task", "")[:50]

            await self._add_relationship(
                source=session_id,
                target=f"claude_code_{timestamp}",  # Placeholder
                relationship_type="spawn",
                strength=0.8,
                timestamp=timestamp,
                evidence=[f"Claude Code: {task_desc}"],
            )

            self.agent_metrics[session_id]["spawn_count"] += 1

        elif tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
            # File access creates potential coordination relationships
            file_paths = self._extract_file_paths(tool_name, tool_input)

            for file_path in file_paths:
                # Track shared file access
                self.agent_metrics[session_id]["files_shared"].add(file_path)

                # Look for other agents accessing the same file recently
                await self._check_file_coordination(session_id, file_path, timestamp)

    def _extract_file_paths(self, tool_name: str, tool_input: Dict) -> List[str]:
        """Extract file paths from tool input."""
        paths = []

        if tool_name in ["Read", "Write", "Edit"]:
            file_path = tool_input.get("file_path")
            if file_path:
                paths.append(file_path)
        elif tool_name == "MultiEdit":
            edits = tool_input.get("edits", [])
            for edit in edits:
                if isinstance(edit, dict) and "file_path" in edit:
                    paths.append(edit["file_path"])

        return paths

    async def _check_file_coordination(
        self, session_id: str, file_path: str, timestamp: float
    ):
        """Check for file coordination with other agents."""
        # Look for other agents that accessed the same file recently
        coordination_window = 30.0  # 30 seconds

        for other_session, metrics in self.agent_metrics.items():
            if other_session == session_id:
                continue

            if file_path in metrics["files_shared"]:
                # Check if access was recent
                time_delta = timestamp - metrics["last_activity"]
                if abs(time_delta) <= coordination_window:
                    # Create coordination relationship
                    await self._add_relationship(
                        source=session_id,
                        target=other_session,
                        relationship_type="coordination",
                        strength=min(0.7, 1.0 - abs(time_delta) / coordination_window),
                        timestamp=timestamp,
                        evidence=[f"Shared file access: {file_path}"],
                    )

    async def _add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        strength: float,
        timestamp: float,
        evidence: List[str],
    ):
        """Add or update a relationship between agents."""
        key = (source, target)

        if key in self.relationships:
            # Update existing relationship
            rel = self.relationships[key]
            rel.last_seen = timestamp
            rel.interaction_count += 1
            rel.strength = min(
                1.0, rel.strength + 0.1
            )  # Strengthen with repeated interaction
            rel.evidence.extend(evidence)
        else:
            # Create new relationship
            self.relationships[key] = AgentRelationship(
                source_session=source,
                target_session=target,
                relationship_type=relationship_type,
                strength=strength,
                first_seen=timestamp,
                last_seen=timestamp,
                interaction_count=1,
                evidence=evidence,
            )

        # Update communication partners tracking
        if relationship_type in ["communication", "coordination"]:
            self.agent_metrics[source]["communication_partners"].add(target)
            if target in self.agent_metrics:  # Only if target is a real session
                self.agent_metrics[target]["communication_partners"].add(source)

    async def update_analysis(self, active_sessions: Dict):
        """Update network analysis with current session data."""
        current_time = time.time()

        # Clean up old relationships
        await self._cleanup_old_relationships(current_time)

        # Update centrality scores
        await self._calculate_centrality(active_sessions)

        # Invalidate cache
        self.cached_analysis = None
        self.cache_timestamp = 0.0

    async def _cleanup_old_relationships(self, current_time: float):
        """Remove old or invalid relationships."""
        cleanup_threshold = current_time - 600.0  # 10 minutes

        to_remove = []
        for key, relationship in self.relationships.items():
            if relationship.last_seen < cleanup_threshold:
                to_remove.append(key)
            # Also remove placeholder spawn relationships if they're old
            elif (
                relationship.target.startswith("spawn_")
                or relationship.target.startswith("claude_code_")
            ) and relationship.last_seen < current_time - 60.0:  # 1 minute for spawns
                to_remove.append(key)

        for key in to_remove:
            del self.relationships[key]

    async def _calculate_centrality(self, active_sessions: Dict):
        """Calculate centrality scores for agents based on their network position."""
        if not self.relationships:
            return

        # Simple degree centrality calculation
        degree_counts = defaultdict(int)

        for source, target in self.relationships.keys():
            if source in active_sessions:
                degree_counts[source] += 1
            if target in active_sessions:
                degree_counts[target] += 1

        # Normalize centrality scores
        max_degree = max(degree_counts.values()) if degree_counts else 1

        for session_id in active_sessions:
            degree = degree_counts.get(session_id, 0)
            self.agent_metrics[session_id]["centrality_score"] = degree / max_degree

    async def get_current_analysis(self) -> NetworkMetrics:
        """Get current network analysis metrics."""
        current_time = time.time()

        # Return cached analysis if still valid
        if (
            self.cached_analysis
            and current_time - self.cache_timestamp < self.cache_validity_seconds
        ):
            return self.cached_analysis

        # Calculate fresh analysis
        metrics = NetworkMetrics()

        # Count active nodes and edges
        active_nodes = set()
        active_edges = 0

        for (source, target), relationship in self.relationships.items():
            if not (target.startswith("spawn_") or target.startswith("claude_code_")):
                active_nodes.update([source, target])
                active_edges += 1

        metrics.total_nodes = len(active_nodes)
        metrics.total_edges = active_edges

        # Find central agents
        central_agents = sorted(
            self.agent_metrics.keys(),
            key=lambda x: self.agent_metrics[x]["centrality_score"],
            reverse=True,
        )[
            :5
        ]  # Top 5 central agents

        metrics.central_agents = central_agents

        # Calculate collaboration efficiency (simple metric)
        if metrics.total_nodes > 1:
            max_possible_edges = metrics.total_nodes * (metrics.total_nodes - 1)
            metrics.collaboration_efficiency = metrics.total_edges / max_possible_edges

        # Find collaboration chains
        metrics.active_chains = await self._find_collaboration_chains()

        # Calculate network depth
        metrics.max_depth = await self._calculate_max_depth()

        # Cache the results
        self.cached_analysis = metrics
        self.cache_timestamp = current_time

        return metrics

    async def _find_collaboration_chains(self) -> List[List[str]]:
        """Find chains of agent collaboration (A spawns B, B coordinates with C, etc.)."""
        chains = []

        # Build adjacency list
        graph = defaultdict(list)
        for (source, target), rel in self.relationships.items():
            if not (target.startswith("spawn_") or target.startswith("claude_code_")):
                graph[source].append((target, rel.relationship_type))

        # Find chains using BFS
        visited = set()
        for start_node in graph:
            if start_node not in visited:
                chain = await self._trace_chain(start_node, graph, visited)
                if len(chain) > 2:  # Only keep meaningful chains
                    chains.append(chain)

        return chains[:10]  # Limit to top 10 chains

    async def _trace_chain(
        self, start_node: str, graph: Dict, visited: Set[str]
    ) -> List[str]:
        """Trace a collaboration chain from a starting node."""
        chain = [start_node]
        visited.add(start_node)

        queue = deque([(start_node, [start_node])])
        max_chain = chain

        while queue and len(max_chain) < 10:  # Prevent infinite loops
            current, path = queue.popleft()

            for neighbor, rel_type in graph.get(current, []):
                if neighbor not in path:  # Avoid cycles
                    new_path = path + [neighbor]
                    if len(new_path) > len(max_chain):
                        max_chain = new_path
                    queue.append((neighbor, new_path))
                    visited.add(neighbor)

        return max_chain

    async def _calculate_max_depth(self) -> int:
        """Calculate maximum depth of agent hierarchy."""
        # Find spawn relationships and calculate depth
        spawn_graph = defaultdict(list)

        for (source, target), rel in self.relationships.items():
            if rel.relationship_type == "spawn" and not target.startswith("spawn_"):
                spawn_graph[source].append(target)

        max_depth = 0
        for root in spawn_graph:
            depth = self._calculate_depth(root, spawn_graph, set())
            max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_depth(self, node: str, graph: Dict, visited: Set[str]) -> int:
        """Recursively calculate depth from a node."""
        if node in visited:
            return 0

        visited.add(node)
        max_child_depth = 0

        for child in graph.get(node, []):
            child_depth = self._calculate_depth(child, graph, visited)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth + 1

    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to float."""
        if not timestamp_str:
            return time.time()

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError):
            return time.time()

    def get_agent_relationships(self, session_id: str) -> List[AgentRelationship]:
        """Get all relationships for a specific agent."""
        relationships = []

        for (source, target), rel in self.relationships.items():
            if source == session_id or target == session_id:
                relationships.append(rel)

        return sorted(relationships, key=lambda x: x.last_seen, reverse=True)

    def get_collaboration_partners(self, session_id: str) -> Set[str]:
        """Get active collaboration partners for an agent."""
        return self.agent_metrics[session_id]["communication_partners"].copy()
