#!/usr/bin/env python3
"""
Agent Status Monitor for Real-Time Agent Orchestration
Provides real-time monitoring capabilities for launched agents
"""

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

# Add chat-search to path
sys.path.append(str(Path(__file__).parent.parent.parent / "chat-search"))
from chat_search import ChatSearcher


@dataclass
class LogEntry:
    """Individual log entry from agent execution"""

    timestamp: str
    role: str
    content: str
    session_id: str
    file_path: str
    line_number: int


@dataclass
class ErrorInfo:
    """Error information from agent logs"""

    timestamp: str
    error_type: str
    error_message: str
    context: str = ""
    severity: str = "warning"  # warning, error, critical


@dataclass
class ProgressStatus:
    """Progress information extracted from agent logs"""

    current_task: str = ""
    completed_tasks: List[str] = field(default_factory=list)
    progress_percentage: float = 0.0
    last_activity: Optional[str] = None
    estimated_completion: Optional[str] = None


@dataclass
class AgentStatus:
    """Complete status information for an agent"""

    agent_uuid: str
    status: str  # running, completed, failed, stuck, unknown
    progress: ProgressStatus
    context_usage: float = 0.0
    error_count: int = 0
    recent_errors: List[ErrorInfo] = field(default_factory=list)
    last_activity_timestamp: Optional[str] = None
    deliverables_completed: List[str] = field(default_factory=list)
    deliverables_missing: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    runtime_duration: Optional[float] = None


class AgentStatusMonitor:
    """
    Real-time agent status monitoring system
    Integrates with chat_search.py to provide structured agent monitoring
    """

    def __init__(self, chat_logs_dir: str = None):
        """
        Initialize the agent status monitor

        Args:
            chat_logs_dir: Directory containing chat logs (defaults to ~/.claude/projects/{cwd})
        """
        if chat_logs_dir is None:
            # Default to Claude projects directory
            cwd = Path.cwd().name
            chat_logs_dir = (
                Path.home()
                / ".claude"
                / "projects"
                / f"-home-opsvi-master-root-apps-agent-orchestrator"
            )

        self.chat_logs_dir = Path(chat_logs_dir)
        self.searcher = ChatSearcher(str(self.chat_logs_dir))

        # Cache for agent statuses (avoid re-parsing frequently)
        self._status_cache: Dict[str, AgentStatus] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_duration = timedelta(seconds=15)  # Cache for 15 seconds max

    async def get_agent_status(self, agent_uuid: str) -> AgentStatus:
        """
        Get current status for a specific agent

        Args:
            agent_uuid: The UUID of the agent to monitor

        Returns:
            AgentStatus object with current agent state
        """
        # Check cache first
        now = datetime.now()
        if (
            agent_uuid in self._status_cache
            and agent_uuid in self._cache_timestamps
            and now - self._cache_timestamps[agent_uuid] < self.cache_duration
        ):
            return self._status_cache[agent_uuid]

        # Find agent's log file
        log_files = list(self.chat_logs_dir.glob(f"{agent_uuid}.jsonl"))
        if not log_files:
            return AgentStatus(
                agent_uuid=agent_uuid, status="unknown", progress=ProgressStatus()
            )

        log_file = log_files[0]

        # Parse agent logs
        status = await self._parse_agent_logs(agent_uuid, log_file)

        # Cache the result
        self._status_cache[agent_uuid] = status
        self._cache_timestamps[agent_uuid] = now

        return status

    async def get_all_agent_statuses(
        self, team_id: str = None
    ) -> Dict[str, AgentStatus]:
        """
        Get status for all agents in a team or all active agents

        Args:
            team_id: Optional team identifier to filter agents

        Returns:
            Dictionary mapping agent UUIDs to their AgentStatus
        """
        statuses = {}

        # Find all UUID-named log files
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$"
        )

        for log_file in self.chat_logs_dir.glob("*.jsonl"):
            if uuid_pattern.match(log_file.name):
                agent_uuid = log_file.stem

                # If team_id provided, filter by it (assuming team info in logs)
                if team_id and not await self._agent_belongs_to_team(
                    agent_uuid, team_id
                ):
                    continue

                status = await self.get_agent_status(agent_uuid)
                statuses[agent_uuid] = status

        return statuses

    async def monitor_agent_logs(
        self, agent_uuid: str
    ) -> AsyncGenerator[LogEntry, None]:
        """
        Monitor agent logs in real-time (async generator)

        Args:
            agent_uuid: The UUID of the agent to monitor

        Yields:
            LogEntry objects as they appear in the logs
        """
        log_file = self.chat_logs_dir / f"{agent_uuid}.jsonl"
        if not log_file.exists():
            return

        # Start monitoring from end of file
        last_position = log_file.stat().st_size if log_file.exists() else 0

        while True:
            try:
                # Check if file has grown
                current_size = log_file.stat().st_size
                if current_size > last_position:
                    with open(log_file, "r", encoding="utf-8") as f:
                        f.seek(last_position)

                        for line_num, line in enumerate(f, start=1):
                            line = line.strip()
                            if not line:
                                continue

                            try:
                                log_data = json.loads(line)
                                message = log_data.get("message", {})

                                yield LogEntry(
                                    timestamp=log_data.get("timestamp", ""),
                                    role=message.get("role", ""),
                                    content=str(message.get("content", "")),
                                    session_id=log_data.get("sessionId", ""),
                                    file_path=str(log_file),
                                    line_number=line_num,
                                )
                            except json.JSONDecodeError:
                                continue

                    last_position = current_size

                # Brief pause before next check
                await asyncio.sleep(1)

            except FileNotFoundError:
                # Agent log file doesn't exist yet or was removed
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error monitoring agent {agent_uuid}: {e}")
                await asyncio.sleep(5)

    async def _parse_agent_logs(self, agent_uuid: str, log_file: Path) -> AgentStatus:
        """Parse agent logs to extract status information"""

        status = AgentStatus(
            agent_uuid=agent_uuid,
            status="running",  # Default assumption
            progress=ProgressStatus(),
        )

        try:
            # Use chat_search to find relevant entries
            recent_logs = self.searcher.search(
                query=".*",  # Get all entries
                files_filter=[log_file.name],
                limit=1000,  # Get recent entries
                context=False,
            )

            if not recent_logs:
                status.status = "unknown"
                return status

            # Sort by timestamp
            recent_logs.sort(key=lambda x: x.get("timestamp", ""))

            # Extract information
            await self._extract_agent_info(status, recent_logs)

        except Exception as e:
            print(f"Error parsing logs for agent {agent_uuid}: {e}")
            status.status = "unknown"

        return status

    async def _extract_agent_info(self, status: AgentStatus, log_entries: List[Dict]):
        """Extract detailed information from log entries"""

        if not log_entries:
            return

        first_entry = log_entries[0]
        last_entry = log_entries[-1]

        # Set basic timing info
        status.start_time = first_entry.get("timestamp", "")
        status.last_activity_timestamp = last_entry.get("timestamp", "")

        # Calculate runtime if we have valid timestamps
        if status.start_time and status.last_activity_timestamp:
            try:
                start_dt = datetime.fromisoformat(
                    status.start_time.replace("Z", "+00:00")
                )
                last_dt = datetime.fromisoformat(
                    status.last_activity_timestamp.replace("Z", "+00:00")
                )
                status.runtime_duration = (last_dt - start_dt).total_seconds()
            except:
                pass

        # Analyze activity patterns
        await self._analyze_activity_patterns(status, log_entries)
        await self._detect_completion_status(status, log_entries)
        await self._extract_errors(status, log_entries)
        await self._estimate_progress(status, log_entries)
        await self._detect_deliverables(status, log_entries)

    async def _analyze_activity_patterns(
        self, status: AgentStatus, log_entries: List[Dict]
    ):
        """Analyze activity patterns to detect stuck agents"""

        now = datetime.now()

        # Check if agent has been inactive too long
        if status.last_activity_timestamp:
            try:
                last_activity = datetime.fromisoformat(
                    status.last_activity_timestamp.replace("Z", "+00:00")
                )
                if (now - last_activity).total_seconds() > 600:  # 10 minutes
                    if status.status == "running":
                        status.status = "stuck"
            except:
                pass

    async def _detect_completion_status(
        self, status: AgentStatus, log_entries: List[Dict]
    ):
        """Detect if agent has completed successfully or failed"""

        # Look for completion indicators in recent entries
        for entry in reversed(log_entries[-50:]):  # Check last 50 entries
            content = str(entry.get("full_content", "")).lower()

            # Success indicators
            if any(
                indicator in content
                for indicator in [
                    "task completed successfully",
                    "execution complete",
                    "finished successfully",
                    "deliverables completed",
                    "all tasks completed",
                ]
            ):
                status.status = "completed"
                return

            # Failure indicators
            if any(
                indicator in content
                for indicator in [
                    "task failed",
                    "execution failed",
                    "error occurred",
                    "unable to complete",
                    "fatal error",
                ]
            ):
                status.status = "failed"
                return

    async def _extract_errors(self, status: AgentStatus, log_entries: List[Dict]):
        """Extract error information from logs"""

        errors = []

        for entry in log_entries:
            content = str(entry.get("full_content", ""))

            # Look for error patterns
            if any(
                pattern in content.lower()
                for pattern in ["error:", "exception:", "failed:", "traceback", "errno"]
            ):
                error = ErrorInfo(
                    timestamp=entry.get("timestamp", ""),
                    error_type="execution_error",
                    error_message=content[:200],
                    context=entry.get("match_type", ""),
                )
                errors.append(error)

        status.error_count = len(errors)
        status.recent_errors = errors[-5:]  # Keep last 5 errors

    async def _estimate_progress(self, status: AgentStatus, log_entries: List[Dict]):
        """Estimate progress based on log activity"""

        total_entries = len(log_entries)
        if total_entries == 0:
            return

        # Look for task completion indicators
        completed_tasks = []
        current_task = ""

        for entry in log_entries:
            content = str(entry.get("full_content", "")).lower()

            # Look for task indicators
            if "task:" in content or "executing:" in content:
                # Extract task name
                lines = content.split("\n")
                for line in lines:
                    if "task:" in line or "executing:" in line:
                        current_task = line.strip()[:100]
                        break

            # Look for completion indicators
            if any(
                indicator in content
                for indicator in ["completed", "finished", "done", "✓", "success"]
            ):
                if current_task:
                    completed_tasks.append(current_task)

        status.progress.completed_tasks = list(set(completed_tasks))
        status.progress.current_task = current_task

        # Rough progress estimation
        if total_entries > 0:
            # More log activity generally means more progress
            status.progress.progress_percentage = min(
                (len(completed_tasks) * 10 + total_entries * 0.5), 100
            )

    async def _detect_deliverables(self, status: AgentStatus, log_entries: List[Dict]):
        """Detect what deliverables have been completed"""

        deliverables = []

        for entry in log_entries:
            content = str(entry.get("full_content", ""))

            # Look for file creation/modification
            if any(
                pattern in content.lower()
                for pattern in ["created file", "wrote file", "saved to", "generated"]
            ):
                # Try to extract filename
                import re

                file_patterns = [
                    r'(?:created|wrote|saved to|generated)\s+["\']?([^"\'\s]+\.[a-zA-Z0-9]+)',
                    r'file[:\s]+["\']?([^"\'\s]+\.[a-zA-Z0-9]+)',
                ]

                for pattern in file_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    deliverables.extend(matches)

        status.deliverables_completed = list(set(deliverables))

    async def _agent_belongs_to_team(self, agent_uuid: str, team_id: str) -> bool:
        """Check if agent belongs to a specific team"""

        # This is a placeholder - in practice, you might check:
        # 1. Agent metadata in logs
        # 2. Team-specific prefixes in UUIDs
        # 3. Team configuration files

        if team_id in agent_uuid:
            return True

        # Could also search log content for team identifiers
        try:
            results = self.searcher.search(
                query=team_id, files_filter=[f"{agent_uuid}.jsonl"], limit=1
            )
            return len(results) > 0
        except:
            return False


# Example usage and testing
async def example_usage():
    """Example of how to use the AgentStatusMonitor"""

    monitor = AgentStatusMonitor()

    # Example UUID - replace with actual agent UUID
    test_uuid = "team-phase1-001-monitor-1725408000"

    print(f"Getting status for agent: {test_uuid}")
    status = await monitor.get_agent_status(test_uuid)

    print(f"Status: {status.status}")
    print(f"Progress: {status.progress.progress_percentage}%")
    print(f"Errors: {status.error_count}")
    print(f"Last activity: {status.last_activity_timestamp}")

    # Get all agent statuses
    print("\nGetting all agent statuses...")
    all_statuses = await monitor.get_all_agent_statuses()

    for uuid, agent_status in all_statuses.items():
        print(f"Agent {uuid[:8]}: {agent_status.status}")


if __name__ == "__main__":
    asyncio.run(example_usage())
