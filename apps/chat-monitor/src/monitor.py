#!/usr/bin/env python3
"""
Enhanced Chat Monitor - Agent Collaboration Observatory

Main monitoring engine that provides real-time visibility into Claude Code
agent swarms with focus on collaboration patterns, inter-agent communication,
and shared workspace coordination.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from analysis.metrics import MetricsCalculator
from collaboration.detector import CollaborationDetector
from collaboration.network import AgentNetworkAnalyzer
from collaboration.workspace import WorkspaceTracker
from config.settings import Settings
from display.dashboard import Dashboard
from orchestrator_registry import OrchestratorRegistry


@dataclass
class AgentSession:
    """Represents an active agent session with collaboration context."""

    session_id: str
    start_time: datetime
    last_activity: datetime
    tool_sequence: List[str] = field(default_factory=list)
    files_accessed: Set[str] = field(default_factory=set)
    agents_spawned: List[str] = field(default_factory=list)
    collaboration_events: List[dict] = field(default_factory=list)
    current_status: str = "active"
    communication_partners: Set[str] = field(default_factory=set)


class EnhancedChatMonitor:
    """
    Next-generation chat monitor focused on agent collaboration visibility.

    Unlike basic monitors that show individual tool usage, this monitor:
    1. Detects and visualizes inter-agent communication patterns
    2. Tracks shared workspace coordination and conflicts
    3. Identifies task handoff chains and collaboration networks
    4. Provides real-time collaboration intelligence
    """

    def __init__(self, settings: Settings, selected_runs: Optional[List[str]] = None):
        self.settings = settings
        self.selected_runs = selected_runs or []
        self.active_sessions: Dict[str, AgentSession] = {}
        self.session_log_paths: Dict[str, Path] = {}

        # Orchestrator registry for run selection
        self.orchestrator_registry = OrchestratorRegistry()

        # Core collaboration analysis components
        self.collaboration_detector = CollaborationDetector(settings)
        self.network_analyzer = AgentNetworkAnalyzer(settings)
        self.workspace_tracker = WorkspaceTracker(settings)
        self.metrics_calculator = MetricsCalculator(settings)

        # Display and user interface
        self.dashboard = Dashboard(settings)

        # Monitoring state
        self.is_running = False
        self.last_file_positions: Dict[Path, int] = {}

        # Setup logging
        logging.basicConfig(
            level=logging.INFO if settings.verbose else logging.WARNING,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """Start the enhanced monitoring system."""
        self.logger.info(
            "Starting Enhanced Chat Monitor - Agent Collaboration Observatory"
        )
        self.logger.info(f"Monitoring directory: {self.settings.chat_logs_dir}")

        self.is_running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Initialize dashboard
        await self.dashboard.initialize()

        try:
            # Start concurrent monitoring tasks
            await asyncio.gather(
                self._monitor_log_files(),
                self._update_collaboration_analysis(),
                self._refresh_dashboard(),
                self._cleanup_inactive_sessions(),
            )
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            raise
        finally:
            await self._shutdown()

    async def _monitor_log_files(self):
        """Monitor chat log files for new entries."""
        while self.is_running:
            try:
                # Discover active session files
                await self._discover_session_files()

                # Process new entries in each active session
                for session_id, log_path in self.session_log_paths.items():
                    await self._process_session_updates(session_id, log_path)

                await asyncio.sleep(self.settings.file_poll_interval)

            except Exception as e:
                self.logger.error(f"File monitoring error: {e}")
                await asyncio.sleep(1)

    async def _discover_session_files(self):
        """Discover and track active session log files."""
        if self.selected_runs:
            # Monitor only selected orchestrator runs
            await self._discover_run_sessions()
        else:
            # Fallback to traditional system-wide discovery
            await self._discover_system_wide_sessions()

    async def _discover_run_sessions(self):
        """Discover sessions for selected orchestrator runs."""
        for run_id in self.selected_runs:
            run_details = self.orchestrator_registry.get_run_details(run_id)
            if not run_details:
                self.logger.warning(f"Run not found: {run_id}")
                continue

            self.logger.info(f"Monitoring orchestrator run: {run_details.title}")

            # Monitor all log directories for this run
            for log_dir in run_details.log_directories:
                await self._scan_log_directory(Path(log_dir))

    async def _discover_system_wide_sessions(self):
        """Traditional system-wide session discovery."""
        chat_logs_dir = Path(self.settings.chat_logs_dir)

        if not chat_logs_dir.exists():
            self.logger.warning(f"Chat logs directory not found: {chat_logs_dir}")
            return

        await self._scan_log_directory(chat_logs_dir)

    async def _scan_log_directory(self, log_dir: Path):
        """Scan a specific log directory for session files."""
        if not log_dir.exists():
            return

        # Find all .jsonl files
        for jsonl_file in log_dir.glob("*.jsonl"):
            session_id = jsonl_file.stem

            # Track new session files
            if session_id not in self.session_log_paths:
                self.session_log_paths[session_id] = jsonl_file
                self.last_file_positions[jsonl_file] = 0
                self.logger.info(f"Discovered new session: {session_id}")

                # Initialize session tracking
                if session_id not in self.active_sessions:
                    self.active_sessions[session_id] = AgentSession(
                        session_id=session_id,
                        start_time=datetime.now(),
                        last_activity=datetime.now(),
                    )

    async def _process_session_updates(self, session_id: str, log_path: Path):
        """Process new log entries for a specific session."""
        try:
            if not log_path.exists():
                return

            # Read new lines since last position
            with open(log_path, "r") as f:
                f.seek(self.last_file_positions[log_path])
                new_lines = f.readlines()
                self.last_file_positions[log_path] = f.tell()

            if not new_lines:
                return

            session = self.active_sessions[session_id]

            for line in new_lines:
                await self._process_log_entry(session, line.strip())

        except Exception as e:
            self.logger.error(f"Session processing error for {session_id}: {e}")

    async def _process_log_entry(self, session: AgentSession, line: str):
        """Process a single log entry and extract collaboration intelligence."""
        if not line or not line.startswith("{"):
            return

        try:
            entry = json.loads(line)

            # Update session activity
            session.last_activity = datetime.now()

            # Extract collaboration signals
            collaboration_events = await self.collaboration_detector.analyze_entry(
                session.session_id, entry
            )

            # Process detected collaboration events
            for event in collaboration_events:
                await self._handle_collaboration_event(session, event)

            # Track tool usage and patterns
            await self._track_tool_usage(session, entry)

            # Update workspace coordination
            await self.workspace_tracker.process_entry(session.session_id, entry)

            # Update network analysis
            await self.network_analyzer.process_entry(session.session_id, entry)

        except json.JSONDecodeError:
            # Skip malformed JSON
            pass
        except Exception as e:
            self.logger.error(f"Entry processing error: {e}")

    async def _handle_collaboration_event(self, session: AgentSession, event: dict):
        """Handle detected collaboration event."""
        session.collaboration_events.append(event)

        # Track communication partners
        if event.get("type") == "agent_communication":
            partner_id = event.get("partner_session_id")
            if partner_id:
                session.communication_partners.add(partner_id)

                # Update partner's communication partners too
                if partner_id in self.active_sessions:
                    self.active_sessions[partner_id].communication_partners.add(
                        session.session_id
                    )

        # Log significant collaboration events
        if event.get("significance", 0) >= self.settings.collaboration_log_threshold:
            self.logger.info(
                f"Collaboration event: {event['type']} between {session.session_id} "
                f"and {event.get('partner_session_id', 'unknown')}"
            )

    async def _track_tool_usage(self, session: AgentSession, entry: dict):
        """Track tool usage patterns for collaboration analysis."""
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list) or not content:
            return

        for item in content:
            if isinstance(item, dict) and "name" in item:
                tool_name = item["name"]
                session.tool_sequence.append(tool_name)

                # Track agent spawning
                if tool_name in [
                    "Task",
                    "mcp__claude-code-wrapper__claude_run",
                    "mcp__claude-code-wrapper__claude_run_async",
                ]:
                    await self._handle_agent_spawn(session, item)

                # Track file access for workspace coordination
                if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                    await self._handle_file_access(session, item)

    async def _handle_agent_spawn(self, session: AgentSession, tool_item: dict):
        """Handle agent spawning events."""
        tool_input = tool_item.get("input", {})

        if "subagent_type" in tool_input:
            # Task tool spawn
            agent_type = tool_input["subagent_type"]
            session.agents_spawned.append(agent_type)
            self.logger.debug(f"Agent spawn: {session.session_id} -> {agent_type}")
        elif "task" in tool_input:
            # Claude Code wrapper spawn
            task_desc = tool_input["task"][:50]
            session.agents_spawned.append(f"claude_code: {task_desc}")
            self.logger.debug(f"Claude Code spawn: {session.session_id} -> {task_desc}")

    async def _handle_file_access(self, session: AgentSession, tool_item: dict):
        """Handle file access events for workspace tracking."""
        tool_input = tool_item.get("input", {})

        if "file_path" in tool_input:
            file_path = tool_input["file_path"]
            session.files_accessed.add(file_path)

        elif "edits" in tool_input:  # MultiEdit
            for edit in tool_input.get("edits", []):
                if "file_path" in edit:
                    session.files_accessed.add(edit["file_path"])

    async def _update_collaboration_analysis(self):
        """Periodically update collaboration analysis and metrics."""
        while self.is_running:
            try:
                # Update network analysis
                await self.network_analyzer.update_analysis(self.active_sessions)

                # Update workspace coordination analysis
                await self.workspace_tracker.update_analysis(self.active_sessions)

                # Calculate current metrics
                await self.metrics_calculator.update_metrics(self.active_sessions)

                await asyncio.sleep(self.settings.analysis_update_interval)

            except Exception as e:
                self.logger.error(f"Analysis update error: {e}")
                await asyncio.sleep(1)

    async def _refresh_dashboard(self):
        """Periodically refresh the dashboard display."""
        while self.is_running:
            try:
                # Gather current state for dashboard
                dashboard_data = {
                    "active_sessions": self.active_sessions,
                    "network_analysis": await self.network_analyzer.get_current_analysis(),
                    "workspace_status": await self.workspace_tracker.get_current_status(),
                    "metrics": await self.metrics_calculator.get_current_metrics(),
                    "collaboration_events": await self._get_recent_collaboration_events(),
                }

                # Update dashboard
                await self.dashboard.update_display(dashboard_data)

                await asyncio.sleep(self.settings.dashboard_refresh_interval)

            except Exception as e:
                self.logger.error(f"Dashboard refresh error: {e}")
                await asyncio.sleep(1)

    async def _get_recent_collaboration_events(self) -> List[dict]:
        """Get recent collaboration events across all sessions."""
        events = []
        cutoff_time = datetime.now().timestamp() - self.settings.recent_events_window

        for session in self.active_sessions.values():
            for event in session.collaboration_events:
                if event.get("timestamp", 0) >= cutoff_time:
                    events.append({**event, "session_id": session.session_id})

        return sorted(events, key=lambda x: x.get("timestamp", 0), reverse=True)

    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions periodically."""
        while self.is_running:
            try:
                current_time = datetime.now()
                inactive_sessions = []

                for session_id, session in self.active_sessions.items():
                    time_since_activity = current_time - session.last_activity
                    if (
                        time_since_activity.total_seconds()
                        > self.settings.session_timeout
                    ):
                        inactive_sessions.append(session_id)
                        session.current_status = "inactive"

                # Remove inactive sessions
                for session_id in inactive_sessions:
                    self.logger.info(f"Marking session as inactive: {session_id}")
                    # Keep session data but mark as inactive for historical analysis

                await asyncio.sleep(self.settings.cleanup_interval)

            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(30)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.is_running = False

    async def _shutdown(self):
        """Perform cleanup on shutdown."""
        self.logger.info("Shutting down Enhanced Chat Monitor...")

        # Close dashboard
        await self.dashboard.cleanup()

        # Save final analysis data if configured
        if self.settings.save_on_exit:
            await self._save_session_data()

    async def _save_session_data(self):
        """Save session data for historical analysis."""
        try:
            output_path = (
                Path(self.settings.output_dir)
                / f"session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare serializable data
            session_data = {}
            for session_id, session in self.active_sessions.items():
                session_data[session_id] = {
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "tool_sequence": session.tool_sequence,
                    "files_accessed": list(session.files_accessed),
                    "agents_spawned": session.agents_spawned,
                    "collaboration_events": session.collaboration_events,
                    "current_status": session.current_status,
                    "communication_partners": list(session.communication_partners),
                }

            with open(output_path, "w") as f:
                json.dump(session_data, f, indent=2)

            self.logger.info(f"Session data saved to: {output_path}")

        except Exception as e:
            self.logger.error(f"Error saving session data: {e}")


def select_orchestrator_runs(registry: OrchestratorRegistry) -> List[str]:
    """
    Interactive selector for orchestrator runs to monitor.

    Returns:
        List of selected run IDs, or empty list for system-wide monitoring
    """
    print("\n" + "=" * 70)
    print("🎯 ORCHESTRATOR RUN SELECTOR")
    print("=" * 70)

    # Get available runs
    active_runs = registry.list_active_runs()
    completed_runs = registry.list_completed_runs(limit=5)

    if not active_runs and not completed_runs:
        print("📭 No orchestrator runs found.")
        print(
            "💡 Tip: Start an orchestrator that registers runs, or use system-wide monitoring"
        )
        return []

    print("\n📋 ACTIVE RUNS:")
    if active_runs:
        for i, run in enumerate(active_runs, 1):
            agent_count = len(run.agent_sessions)
            worktree_count = len(run.metadata.get("worktrees", []))
            start_time = datetime.fromisoformat(run.start_time).strftime("%H:%M:%S")

            print(
                f"  [{i}] {run.title:<30} ({agent_count} agents, {worktree_count} worktrees) [{start_time}]"
            )
    else:
        print("  📭 No active runs")

    print("\n🏁 RECENT COMPLETED:")
    completed_offset = len(active_runs)
    if completed_runs:
        for i, run in enumerate(completed_runs, completed_offset + 1):
            agent_count = len(run.agent_sessions)
            completed_time = datetime.fromisoformat(run.last_updated).strftime(
                "%H:%M:%S"
            )
            print(f"  [{i}] {run.title:<30} (completed at {completed_time})")
    else:
        print("  📭 No recent completed runs")

    print("\n💫 OTHER OPTIONS:")
    print(f"  [a] All active agents (system-wide)")
    print(f"  [r] Refresh list")
    print(f"  [q] Quit")

    while True:
        try:
            choice = (
                input(
                    f"\nSelect run to monitor [1-{len(active_runs + completed_runs)}, a, r, q]: "
                )
                .strip()
                .lower()
            )

            if choice == "q":
                print("Goodbye!")
                sys.exit(0)
            elif choice == "a":
                print("🌍 Monitoring all active agents (system-wide)")
                return []
            elif choice == "r":
                print("🔄 Refreshing...")
                return select_orchestrator_runs(registry)
            elif choice.isdigit():
                choice_num = int(choice)
                all_runs = active_runs + completed_runs

                if 1 <= choice_num <= len(all_runs):
                    selected_run = all_runs[choice_num - 1]

                    # Show selection details
                    print(f"\n🎯 Selected: {selected_run.title}")
                    print(f"📊 Agents: {len(selected_run.agent_sessions)}")
                    print(f"📂 Log directories:")
                    for log_dir in selected_run.log_directories:
                        print(f"  - {log_dir}")

                    return [selected_run.run_id]
                else:
                    print(f"❌ Invalid choice. Please select 1-{len(all_runs)}")
            else:
                print("❌ Invalid input. Please try again.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")


def list_orchestrator_runs(registry: OrchestratorRegistry):
    """List all available orchestrator runs."""
    active_runs = registry.list_active_runs()
    completed_runs = registry.list_completed_runs(limit=10)

    print("🎯 ORCHESTRATOR RUNS")
    print("=" * 50)

    print("\n📋 ACTIVE RUNS:")
    if active_runs:
        for run in active_runs:
            agent_count = len(run.agent_sessions)
            worktree_count = len(run.metadata.get("worktrees", []))
            start_time = datetime.fromisoformat(run.start_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print(f"  🟢 {run.run_id}")
            print(f"     Title: {run.title}")
            print(f"     Agents: {agent_count}, Worktrees: {worktree_count}")
            print(f"     Started: {start_time}")
            print()
    else:
        print("  📭 No active runs")

    print("\n🏁 COMPLETED RUNS:")
    if completed_runs:
        for run in completed_runs:
            agent_count = len(run.agent_sessions)
            completed_time = datetime.fromisoformat(run.last_updated).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print(f"  🔴 {run.run_id}")
            print(f"     Title: {run.title}")
            print(f"     Agents: {agent_count}")
            print(f"     Completed: {completed_time}")
            print()
    else:
        print("  📭 No completed runs")


def cli_main():
    """CLI entry point wrapper for async main function."""
    asyncio.run(main())


async def main():
    """Main entry point for enhanced chat monitor."""
    parser = argparse.ArgumentParser(
        description="Enhanced Chat Monitor - Agent Collaboration Observatory"
    )
    parser.add_argument(
        "--focus",
        choices=["communication", "workspace", "handoffs", "all"],
        default="all",
        help="Focus monitoring on specific collaboration aspects",
    )
    parser.add_argument(
        "--run", metavar="RUN_ID", help="Monitor specific orchestrator run by ID"
    )
    parser.add_argument(
        "--orchestrator",
        metavar="SESSION_ID",
        help="Monitor by orchestrator session ID",
    )
    parser.add_argument(
        "--run-pattern",
        metavar="PATTERN",
        help="Monitor runs matching title pattern (regex)",
    )
    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="List available orchestrator runs and exit",
    )
    parser.add_argument(
        "--all-agents",
        action="store_true",
        help="Monitor all agents system-wide (skip run selection)",
    )
    parser.add_argument(
        "--analyze-session",
        metavar="SESSION_ID",
        help="Analyze historical session data",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--config", metavar="CONFIG_FILE", help="Custom configuration file path"
    )

    args = parser.parse_args()

    # Initialize orchestrator registry
    registry = OrchestratorRegistry()

    # Handle list-runs command
    if args.list_runs:
        list_orchestrator_runs(registry)
        return

    # Load configuration
    settings = Settings.load(args.config, focus_mode=args.focus, verbose=args.verbose)

    if args.analyze_session:
        # Historical analysis mode (TODO: implement)
        print(
            f"Historical analysis mode not yet implemented for session: {args.analyze_session}"
        )
        return

    # Determine which runs to monitor
    selected_runs = []

    if args.run:
        # Monitor specific run by ID
        selected_runs = [args.run]
        run_details = registry.get_run_details(args.run)
        if run_details:
            print(f"🎯 Monitoring run: {run_details.title}")
        else:
            print(f"❌ Run not found: {args.run}")
            return

    elif args.orchestrator:
        # Find runs by orchestrator session ID
        active_runs = registry.list_active_runs()
        matching_runs = [
            run for run in active_runs if run.orchestrator_session == args.orchestrator
        ]

        if matching_runs:
            selected_runs = [run.run_id for run in matching_runs]
            print(
                f"🎯 Monitoring {len(matching_runs)} runs by orchestrator {args.orchestrator}"
            )
        else:
            print(f"❌ No runs found for orchestrator: {args.orchestrator}")
            return

    elif args.run_pattern:
        # Find runs by title pattern
        matching_runs = registry.find_runs_by_pattern(args.run_pattern)

        if matching_runs:
            selected_runs = [run.run_id for run in matching_runs]
            print(
                f"🎯 Monitoring {len(matching_runs)} runs matching pattern: {args.run_pattern}"
            )
            for run in matching_runs:
                print(f"  - {run.title}")
        else:
            print(f"❌ No runs found matching pattern: {args.run_pattern}")
            return

    elif args.all_agents:
        # Explicitly requested system-wide monitoring
        selected_runs = []
        print("🌍 Monitoring all agents system-wide")

    else:
        # Interactive run selection (default behavior)
        if sys.stdout.isatty():
            selected_runs = select_orchestrator_runs(registry)
        else:
            # Non-interactive mode - default to system-wide
            selected_runs = []
            print("🌍 Non-interactive mode: Monitoring all agents system-wide")

    # Start monitoring with selected runs
    monitor = EnhancedChatMonitor(settings, selected_runs)

    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Monitoring error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
