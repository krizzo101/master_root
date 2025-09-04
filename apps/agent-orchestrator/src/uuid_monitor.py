#!/usr/bin/env python3
"""
UUID-Based Log Monitoring System
Real-time monitoring system that tracks agents by their UUID log files
"""

import asyncio
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from agent_monitor import AgentStatus, AgentStatusMonitor
from log_parser import AgentLogParser
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class UUIDLogHandler(FileSystemEventHandler):
    """File system event handler for UUID log files"""

    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$"
        )

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            filename = Path(event.src_path).name
            if self._is_uuid_file(filename):
                uuid = filename.replace(".jsonl", "")
                if self.callback:
                    asyncio.create_task(self.callback("modified", uuid, event.src_path))

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            filename = Path(event.src_path).name
            if self._is_uuid_file(filename):
                uuid = filename.replace(".jsonl", "")
                if self.callback:
                    asyncio.create_task(self.callback("created", uuid, event.src_path))

    def _is_uuid_file(self, filename: str) -> bool:
        """Check if filename matches UUID pattern"""
        import re

        return bool(re.match(self.uuid_pattern, filename))


class UUIDMonitoringSystem:
    """
    Comprehensive UUID-based log monitoring system
    Provides real-time tracking of all agent UUIDs
    """

    def __init__(self, chat_logs_dir: str = None, update_interval: int = 15):
        """
        Initialize the UUID monitoring system

        Args:
            chat_logs_dir: Directory containing chat logs
            update_interval: How often to update statuses (seconds)
        """
        if chat_logs_dir is None:
            chat_logs_dir = (
                Path.home()
                / ".claude"
                / "projects"
                / f"-home-opsvi-master-root-apps-agent-orchestrator"
            )

        self.chat_logs_dir = Path(chat_logs_dir)
        self.update_interval = update_interval

        # Initialize monitoring components
        self.status_monitor = AgentStatusMonitor(str(chat_logs_dir))
        self.log_parser = AgentLogParser(str(chat_logs_dir))

        # Tracking state
        self.active_agents: Set[str] = set()
        self.agent_statuses: Dict[str, AgentStatus] = {}
        self.agent_last_seen: Dict[str, datetime] = {}
        self.team_assignments: Dict[str, str] = {}  # UUID -> team_id

        # File system monitoring
        self.observer = Observer()
        self.handler = UUIDLogHandler(callback=self._on_file_event)

        # Performance tracking
        self.monitoring_stats = {
            "agents_discovered": 0,
            "status_updates": 0,
            "errors_detected": 0,
            "last_scan_time": None,
            "scan_duration": 0.0,
        }

        # Control flags
        self._running = False
        self._scan_task = None

    async def start_monitoring(self):
        """Start the UUID monitoring system"""
        if self._running:
            return

        self._running = True
        print(f"Starting UUID monitoring system...")
        print(f"Monitoring directory: {self.chat_logs_dir}")
        print(f"Update interval: {self.update_interval} seconds")

        # Ensure logs directory exists
        self.chat_logs_dir.mkdir(parents=True, exist_ok=True)

        # Start file system monitoring
        self.observer.schedule(self.handler, str(self.chat_logs_dir), recursive=False)
        self.observer.start()

        # Initial scan for existing UUIDs
        await self._scan_for_uuids()

        # Start periodic monitoring task
        self._scan_task = asyncio.create_task(self._monitoring_loop())

        print(f"✓ Monitoring started. Found {len(self.active_agents)} active agents")

    async def stop_monitoring(self):
        """Stop the UUID monitoring system"""
        if not self._running:
            return

        self._running = False

        # Stop file system monitoring
        self.observer.stop()
        self.observer.join()

        # Cancel monitoring task
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

        print("UUID monitoring system stopped")

    async def get_real_time_status(self, uuid: str) -> AgentStatus:
        """Get real-time status for a specific agent"""
        if uuid in self.agent_statuses:
            # Check if cached status is recent
            last_update = self.agent_last_seen.get(uuid)
            if (
                last_update
                and (datetime.now() - last_update).seconds < self.update_interval
            ):
                return self.agent_statuses[uuid]

        # Get fresh status
        status = await self.status_monitor.get_agent_status(uuid)
        self.agent_statuses[uuid] = status
        self.agent_last_seen[uuid] = datetime.now()

        return status

    async def get_all_active_agents(self) -> Dict[str, AgentStatus]:
        """Get status for all currently active agents"""
        result = {}

        for uuid in self.active_agents:
            try:
                status = await self.get_real_time_status(uuid)
                result[uuid] = status
            except Exception as e:
                print(f"Error getting status for {uuid}: {e}")

        return result

    async def get_team_agents(self, team_id: str) -> Dict[str, AgentStatus]:
        """Get all agents belonging to a specific team"""
        result = {}

        for uuid, assigned_team in self.team_assignments.items():
            if assigned_team == team_id and uuid in self.active_agents:
                try:
                    status = await self.get_real_time_status(uuid)
                    result[uuid] = status
                except Exception as e:
                    print(f"Error getting status for team agent {uuid}: {e}")

        return result

    async def detect_stuck_agents(self, threshold_minutes: int = 10) -> List[str]:
        """Detect agents that haven't been active for too long"""
        stuck_agents = []
        threshold = timedelta(minutes=threshold_minutes)
        now = datetime.now()

        for uuid in self.active_agents:
            try:
                status = await self.get_real_time_status(uuid)

                if status.last_activity_timestamp:
                    last_activity = datetime.fromisoformat(
                        status.last_activity_timestamp.replace("Z", "+00:00")
                    )
                    if now - last_activity > threshold:
                        stuck_agents.append(uuid)

            except Exception as e:
                print(f"Error checking stuck status for {uuid}: {e}")

        return stuck_agents

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        summary = {
            "total_active_agents": len(self.active_agents),
            "agents_by_status": defaultdict(int),
            "agents_by_team": defaultdict(list),
            "error_summary": defaultdict(int),
            "performance_metrics": {},
            "monitoring_stats": self.monitoring_stats.copy(),
            "timestamp": datetime.now().isoformat(),
        }

        # Analyze all active agents
        total_errors = 0
        total_progress = 0.0

        for uuid in self.active_agents:
            try:
                status = await self.get_real_time_status(uuid)

                # Count by status
                summary["agents_by_status"][status.status] += 1

                # Group by team
                team = self.team_assignments.get(uuid, "unassigned")
                summary["agents_by_team"][team].append(uuid)

                # Error summary
                total_errors += status.error_count
                for error in status.recent_errors:
                    summary["error_summary"][error.error_type] += 1

                # Progress tracking
                total_progress += status.progress.progress_percentage

            except Exception as e:
                print(f"Error in summary for {uuid}: {e}")

        # Performance metrics
        if self.active_agents:
            summary["performance_metrics"] = {
                "average_progress": total_progress / len(self.active_agents),
                "total_errors": total_errors,
                "error_rate": total_errors / len(self.active_agents),
                "agents_per_team": {
                    team: len(agents)
                    for team, agents in summary["agents_by_team"].items()
                },
            }

        return summary

    async def _monitoring_loop(self):
        """Main monitoring loop that runs periodically"""
        while self._running:
            try:
                start_time = time.time()

                # Scan for new UUIDs
                await self._scan_for_uuids()

                # Update existing agent statuses
                await self._update_agent_statuses()

                # Clean up inactive agents
                await self._cleanup_inactive_agents()

                # Update stats
                scan_duration = time.time() - start_time
                self.monitoring_stats.update(
                    {
                        "last_scan_time": datetime.now().isoformat(),
                        "scan_duration": scan_duration,
                        "status_updates": self.monitoring_stats.get("status_updates", 0)
                        + len(self.active_agents),
                    }
                )

                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)

    async def _scan_for_uuids(self):
        """Scan directory for UUID log files"""
        import re

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$"
        )

        if not self.chat_logs_dir.exists():
            return

        discovered = 0
        for log_file in self.chat_logs_dir.glob("*.jsonl"):
            if uuid_pattern.match(log_file.name):
                uuid = log_file.stem

                if uuid not in self.active_agents:
                    self.active_agents.add(uuid)
                    discovered += 1

                    # Try to determine team assignment
                    team_id = await self._detect_team_assignment(uuid)
                    if team_id:
                        self.team_assignments[uuid] = team_id

        if discovered > 0:
            self.monitoring_stats["agents_discovered"] += discovered
            print(f"Discovered {discovered} new agents")

    async def _update_agent_statuses(self):
        """Update cached statuses for active agents"""
        for uuid in list(self.active_agents):
            try:
                status = await self.status_monitor.get_agent_status(uuid)
                self.agent_statuses[uuid] = status
                self.agent_last_seen[uuid] = datetime.now()
            except Exception as e:
                print(f"Error updating status for {uuid}: {e}")

    async def _cleanup_inactive_agents(self):
        """Remove agents that are no longer active"""
        to_remove = []

        for uuid in self.active_agents:
            log_file = self.chat_logs_dir / f"{uuid}.jsonl"
            if not log_file.exists():
                to_remove.append(uuid)
                continue

            # Check if agent has been inactive for too long (e.g., 1 hour)
            last_seen = self.agent_last_seen.get(uuid)
            if last_seen and (datetime.now() - last_seen).total_seconds() > 3600:
                status = self.agent_statuses.get(uuid)
                if status and status.status in ["completed", "failed"]:
                    to_remove.append(uuid)

        for uuid in to_remove:
            self.active_agents.discard(uuid)
            self.agent_statuses.pop(uuid, None)
            self.agent_last_seen.pop(uuid, None)
            self.team_assignments.pop(uuid, None)

        if to_remove:
            print(f"Cleaned up {len(to_remove)} inactive agents")

    async def _detect_team_assignment(self, uuid: str) -> Optional[str]:
        """Try to detect which team an agent belongs to"""
        try:
            # Look for team identifiers in the UUID or early log entries
            if "team-" in uuid:
                parts = uuid.split("-")
                for part in parts:
                    if part.startswith("team") or "phase" in part:
                        return part

            # Search early log entries for team information
            results = self.status_monitor.searcher.search(
                query=r"(?i)(team|phase|group)",
                files_filter=[f"{uuid}.jsonl"],
                limit=10,
            )

            for result in results:
                content = str(result.get("full_content", "")).lower()
                if "team" in content or "phase" in content:
                    # Extract team identifier
                    import re

                    team_match = re.search(r"(team[-_]?\w+|phase[-_]?\w+)", content)
                    if team_match:
                        return team_match.group(1)

        except Exception as e:
            print(f"Error detecting team for {uuid}: {e}")

        return None

    async def _on_file_event(self, event_type: str, uuid: str, file_path: str):
        """Handle file system events for UUID log files"""
        if event_type == "created":
            if uuid not in self.active_agents:
                self.active_agents.add(uuid)
                team_id = await self._detect_team_assignment(uuid)
                if team_id:
                    self.team_assignments[uuid] = team_id
                print(f"New agent detected: {uuid}")

        elif event_type == "modified":
            if uuid in self.active_agents:
                # Invalidate cache to force fresh status check
                self.agent_last_seen[uuid] = datetime.min


# Example usage and testing
async def example_usage():
    """Example of how to use the UUID monitoring system"""

    monitor = UUIDMonitoringSystem()

    try:
        # Start monitoring
        await monitor.start_monitoring()

        # Run for a while to demonstrate
        for i in range(6):  # Run for ~90 seconds
            await asyncio.sleep(15)

            print(f"\n=== Monitoring Update {i+1} ===")

            # Get monitoring summary
            summary = await monitor.get_monitoring_summary()
            print(f"Active agents: {summary['total_active_agents']}")
            print(f"Status distribution: {dict(summary['agents_by_status'])}")
            print(f"Teams: {dict(summary['agents_by_team'])}")

            # Check for stuck agents
            stuck = await monitor.detect_stuck_agents()
            if stuck:
                print(f"Stuck agents detected: {stuck}")

            # Show some individual agent details
            all_agents = await monitor.get_all_active_agents()
            for uuid, status in list(all_agents.items())[:3]:  # Show first 3
                print(
                    f"  {uuid[:8]}: {status.status} ({status.progress.progress_percentage:.1f}%)"
                )

    finally:
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(example_usage())
