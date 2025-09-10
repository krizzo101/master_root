"""
Enhanced Swarm Intelligence System
=================================

Multi-source data collection and analysis for comprehensive agent swarm monitoring.
Extends the existing collaboration detection with system-level intelligence.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import psutil
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


@dataclass
class AgentProcess:
    """System process information for an active agent."""

    pid: int
    session_id: str
    cpu_percent: float
    memory_mb: float
    parent_pid: Optional[int] = None
    command_line: List[str] = field(default_factory=list)
    start_time: float = 0.0


@dataclass
class WorkspaceEvent:
    """File system event with agent attribution."""

    timestamp: float
    agent_id: str
    file_path: str
    operation: str  # 'read', 'write', 'create', 'delete'
    conflict_agents: Set[str] = field(default_factory=set)


@dataclass
class SwarmMetrics:
    """Performance and health metrics for the entire swarm."""

    total_agents: int
    active_agents: int
    total_cpu_usage: float
    total_memory_mb: float
    conflicts_detected: int
    tasks_completed: int
    average_response_time: float
    timestamp: float


class ProcessMonitor:
    """Monitor system processes to identify and track agent instances."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_pid_map: Dict[str, int] = {}
        self.pid_session_map: Dict[int, str] = {}

    def discover_agent_processes(self) -> List[AgentProcess]:
        """Discover currently running agent processes."""
        agents = []

        for proc in psutil.process_iter(
            [
                "pid",
                "ppid",
                "name",
                "cmdline",
                "cpu_percent",
                "memory_info",
                "create_time",
            ]
        ):
            try:
                if self.is_claude_agent(proc.info):
                    session_id = self.extract_session_id(proc.info)
                    if session_id:
                        agent = AgentProcess(
                            pid=proc.info["pid"],
                            session_id=session_id,
                            cpu_percent=proc.info["cpu_percent"] or 0.0,
                            memory_mb=(proc.info["memory_info"].rss / 1024 / 1024)
                            if proc.info["memory_info"]
                            else 0.0,
                            parent_pid=proc.info["ppid"],
                            command_line=proc.info["cmdline"] or [],
                            start_time=proc.info["create_time"] or 0.0,
                        )
                        agents.append(agent)

                        # Update mappings
                        self.session_pid_map[session_id] = agent.pid
                        self.pid_session_map[agent.pid] = session_id

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return agents

    def is_claude_agent(self, proc_info: Dict) -> bool:
        """Determine if a process is a Claude Code agent."""
        cmdline = proc_info.get("cmdline", [])
        if not cmdline:
            return False

        cmdline_str = " ".join(cmdline).lower()
        return any(
            indicator in cmdline_str
            for indicator in [
                "claude",
                "python.*monitor",
                "chat-monitor",
                "mcp.*claude",
            ]
        )

    def extract_session_id(self, proc_info: Dict) -> Optional[str]:
        """Extract session ID from process information."""
        # Look for session IDs in command line arguments
        cmdline = proc_info.get("cmdline", [])
        for arg in cmdline:
            if len(arg) == 36 and "-" in arg:  # UUID pattern
                return arg

        # Fallback: use PID as session identifier
        return f"proc_{proc_info['pid']}"


class WorkspaceMonitor(FileSystemEventHandler):
    """Monitor file system changes to detect workspace conflicts."""

    def __init__(self, workspace_path: str = "/home/opsvi/master_root"):
        super().__init__()
        self.workspace_path = Path(workspace_path)
        self.logger = logging.getLogger(__name__)
        self.recent_events: List[WorkspaceEvent] = []
        self.file_access_timeline: Dict[
            str, List[Tuple[float, str]]
        ] = {}  # file -> [(time, agent_id)]
        self.conflict_window = 5.0  # seconds

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._record_file_access(event.src_path, "write")

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._record_file_access(event.src_path, "create")

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self._record_file_access(event.src_path, "delete")

    def _record_file_access(self, file_path: str, operation: str):
        """Record file access and detect potential conflicts."""
        timestamp = time.time()
        agent_id = self._identify_accessing_agent(file_path)

        if not agent_id:
            return

        # Update timeline
        if file_path not in self.file_access_timeline:
            self.file_access_timeline[file_path] = []

        # Check for recent duplicate events to avoid spam
        recent_events = self.file_access_timeline[file_path]
        if recent_events:
            last_time, last_agent = recent_events[-1]
            if (
                timestamp - last_time < 1.0 and last_agent == agent_id
            ):  # Same agent within 1 second
                return  # Skip duplicate event

        self.file_access_timeline[file_path].append((timestamp, agent_id))

        # Detect conflicts (multiple agents accessing same file within window)
        recent_accesses = [
            (t, aid)
            for t, aid in self.file_access_timeline[file_path]
            if timestamp - t <= self.conflict_window
        ]

        conflict_agents = set(aid for _, aid in recent_accesses if aid != agent_id)

        # Only create event if there are actual conflicts
        if conflict_agents:
            event = WorkspaceEvent(
                timestamp=timestamp,
                agent_id=agent_id,
                file_path=file_path,
                operation=operation,
                conflict_agents=conflict_agents,
            )

            self.recent_events.append(event)

            # Rate-limit conflict warnings (max 1 per file per 5 seconds)
            last_warning_key = f"warning_{file_path}"
            last_warning_time = getattr(self, "_last_warnings", {}).get(
                last_warning_key, 0
            )

            if timestamp - last_warning_time > 5.0:  # 5 second cooldown
                if not hasattr(self, "_last_warnings"):
                    self._last_warnings = {}
                self._last_warnings[last_warning_key] = timestamp

                self.logger.warning(
                    f"Workspace conflict: Multiple agents writing to {file_path} simultaneously"
                )

    def _identify_accessing_agent(self, file_path: str) -> Optional[str]:
        """Identify which agent is accessing a file (simplified approach)."""
        # For now, disable automatic file system monitoring to prevent spam
        # In production, you'd correlate with process monitoring or use lsof
        return None  # Disable until proper process correlation is implemented

    def get_recent_conflicts(self, window_seconds: int = 60) -> List[WorkspaceEvent]:
        """Get recent workspace conflicts."""
        cutoff = time.time() - window_seconds
        return [
            event
            for event in self.recent_events
            if event.timestamp >= cutoff and event.conflict_agents
        ]

    def cleanup_old_events(self, retention_seconds: int = 3600):
        """Remove old events to prevent memory bloat."""
        cutoff = time.time() - retention_seconds
        self.recent_events = [e for e in self.recent_events if e.timestamp >= cutoff]

        # Clean up timeline data
        for file_path in list(self.file_access_timeline.keys()):
            self.file_access_timeline[file_path] = [
                (t, aid)
                for t, aid in self.file_access_timeline[file_path]
                if t >= cutoff
            ]
            if not self.file_access_timeline[file_path]:
                del self.file_access_timeline[file_path]


class SwarmIntelligenceEngine:
    """
    Central intelligence system for comprehensive swarm monitoring.

    Integrates multiple data sources:
    - Existing log-based collaboration detection
    - System process monitoring
    - File system workspace monitoring
    - Performance and resource analytics
    """

    def __init__(self, workspace_path: str = "/home/opsvi/master_root"):
        self.logger = logging.getLogger(__name__)
        self.process_monitor = ProcessMonitor()
        self.workspace_monitor = WorkspaceMonitor(workspace_path)
        self.observer = Observer()

        # Historical data
        self.swarm_metrics_history: List[SwarmMetrics] = []
        self.agent_performance_cache: Dict[str, Dict] = {}

        # Setup file system monitoring
        self.observer.schedule(self.workspace_monitor, workspace_path, recursive=True)

    async def initialize(self):
        """Initialize the swarm intelligence system."""
        self.logger.info("Initializing Enhanced Swarm Intelligence System")
        self.observer.start()

    async def shutdown(self):
        """Clean shutdown of monitoring systems."""
        self.observer.stop()
        self.observer.join()
        self.logger.info("Swarm Intelligence System shutdown complete")

    async def collect_swarm_snapshot(self) -> Dict:
        """Collect comprehensive snapshot of current swarm state."""
        timestamp = time.time()

        # Get current agent processes
        agent_processes = self.process_monitor.discover_agent_processes()

        # Get recent workspace activity
        recent_conflicts = self.workspace_monitor.get_recent_conflicts(
            window_seconds=60
        )

        # Calculate swarm metrics
        swarm_metrics = self._calculate_swarm_metrics(
            agent_processes, recent_conflicts, timestamp
        )

        snapshot = {
            "timestamp": timestamp,
            "agent_processes": agent_processes,
            "workspace_conflicts": recent_conflicts,
            "swarm_metrics": swarm_metrics,
            "active_agent_count": len(agent_processes),
            "system_health": self._assess_system_health(
                agent_processes, recent_conflicts
            ),
        }

        # Store metrics history
        self.swarm_metrics_history.append(swarm_metrics)
        self._cleanup_old_metrics()

        return snapshot

    def _calculate_swarm_metrics(
        self,
        agents: List[AgentProcess],
        conflicts: List[WorkspaceEvent],
        timestamp: float,
    ) -> SwarmMetrics:
        """Calculate comprehensive swarm performance metrics."""
        return SwarmMetrics(
            total_agents=len(agents),
            active_agents=len([a for a in agents if a.cpu_percent > 0.1]),
            total_cpu_usage=sum(a.cpu_percent for a in agents),
            total_memory_mb=sum(a.memory_mb for a in agents),
            conflicts_detected=len(conflicts),
            tasks_completed=0,  # TODO: Extract from logs
            average_response_time=0.0,  # TODO: Calculate from logs
            timestamp=timestamp,
        )

    def _assess_system_health(
        self, agents: List[AgentProcess], conflicts: List[WorkspaceEvent]
    ) -> Dict:
        """Assess overall system health and identify issues."""
        health = {"status": "healthy", "issues": [], "warnings": []}

        # Check for resource issues
        total_cpu = sum(a.cpu_percent for a in agents)
        total_memory = sum(a.memory_mb for a in agents)

        if total_cpu > 80:
            health["warnings"].append(f"High CPU usage: {total_cpu:.1f}%")

        if total_memory > 8000:  # 8GB threshold
            health["warnings"].append(f"High memory usage: {total_memory:.1f}MB")

        # Check for excessive conflicts
        if len(conflicts) > 10:
            health["issues"].append(
                f"High workspace conflict rate: {len(conflicts)} conflicts"
            )
            health["status"] = "degraded"

        # Check for agent failures (processes dying)
        # TODO: Implement agent lifecycle tracking

        if health["issues"]:
            health["status"] = "unhealthy"
        elif health["warnings"]:
            health["status"] = "warning"

        return health

    def _cleanup_old_metrics(self, retention_hours: int = 24):
        """Clean up old metrics data."""
        cutoff = time.time() - (retention_hours * 3600)
        self.swarm_metrics_history = [
            m for m in self.swarm_metrics_history if m.timestamp >= cutoff
        ]

        # Clean up workspace events
        self.workspace_monitor.cleanup_old_events(
            retention_seconds=retention_hours * 3600
        )

    async def get_agent_relationships(self) -> Dict[str, List[str]]:
        """Build agent relationship map from process hierarchy."""
        agents = self.process_monitor.discover_agent_processes()
        relationships = {}

        for agent in agents:
            if agent.parent_pid:
                parent_session = self.process_monitor.pid_session_map.get(
                    agent.parent_pid
                )
                if parent_session:
                    if parent_session not in relationships:
                        relationships[parent_session] = []
                    relationships[parent_session].append(agent.session_id)

        return relationships

    async def predict_conflicts(self) -> List[Dict]:
        """Predict potential workspace conflicts based on patterns."""
        predictions = []

        # Analyze file access patterns
        for file_path, timeline in self.workspace_monitor.file_access_timeline.items():
            if len(timeline) < 2:
                continue

            # Look for patterns of alternating access
            agents = set(agent_id for _, agent_id in timeline[-10:])  # Last 10 accesses
            if len(agents) > 1:
                predictions.append(
                    {
                        "type": "workspace_conflict",
                        "file_path": file_path,
                        "agents_at_risk": list(agents),
                        "confidence": 0.7,  # TODO: ML-based confidence scoring
                        "recommendation": f"Consider file locking or agent coordination for {file_path}",
                    }
                )

        return predictions
