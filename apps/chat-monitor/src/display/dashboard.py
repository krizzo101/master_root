"""
Dashboard Display System

Real-time dashboard for agent collaboration monitoring with multiple panels
and interactive display modes.
"""

import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class Dashboard:
    """
    Real-time dashboard display for agent collaboration monitoring.

    Features:
    - Multi-panel layout with statistics, communication flows, and activity logs
    - Dynamic content updates without flicker
    - Focus mode support for different collaboration aspects
    - Color-coded session identification
    """

    def __init__(self, settings):
        self.settings = settings
        self.focus_settings = settings.get_focus_settings()
        self.is_initialized = False
        self.last_update = 0.0

        # Terminal control
        self.term_height = 24
        self.term_width = 80

        # Color scheme
        self.colors = {
            "header": "\033[1;37m",  # Bold white
            "success": "\033[1;32m",  # Bold green
            "warning": "\033[1;33m",  # Bold yellow
            "error": "\033[1;31m",  # Bold red
            "info": "\033[1;36m",  # Bold cyan
            "dim": "\033[2m",  # Dim
            "reset": "\033[0m",  # Reset
        }

        # Session colors for consistency
        self.session_colors = [
            "\033[31m",
            "\033[32m",
            "\033[33m",
            "\033[34m",
            "\033[35m",
            "\033[36m",
            "\033[91m",
            "\033[92m",
            "\033[93m",
            "\033[94m",
            "\033[95m",
            "\033[96m",
        ]
        self.session_color_map = {}

    async def initialize(self):
        """Initialize the dashboard display."""
        if not sys.stdout.isatty():
            print("⚠️  Enhanced chat monitor works best in a terminal")
            print("📊 Starting in text-only mode...")
            self.is_initialized = True
            return

        # Get terminal dimensions
        try:
            import shutil

            self.term_width, self.term_height = shutil.get_terminal_size()
        except:
            pass

        # Clear screen and setup
        self._clear_screen()
        self._print_header()

        self.is_initialized = True

        print(f"🚀 Enhanced Chat Monitor initialized")
        print(f"📐 Terminal: {self.term_width}x{self.term_height}")
        print(f"🎯 Focus mode: {self.settings.focus_mode}")
        print(f"📂 Monitoring: {self.settings.chat_logs_dir}")
        print("━" * min(60, self.term_width - 1))

    async def update_display(self, dashboard_data: Dict[str, Any]):
        """Update the dashboard with new data."""
        if not self.is_initialized:
            return

        current_time = time.time()
        if current_time - self.last_update < (1.0 / self.settings.refresh_rate_hz):
            return  # Skip update if too frequent

        try:
            await self._render_dashboard(dashboard_data)
            self.last_update = current_time
        except Exception as e:
            if self.settings.verbose:
                print(f"Dashboard update error: {e}")

    async def _render_dashboard(self, data: Dict[str, Any]):
        """Render the complete dashboard."""
        active_sessions = data.get("active_sessions", {})
        network_analysis = data.get("network_analysis", {})
        workspace_status = data.get("workspace_status", {})
        metrics = data.get("metrics", {})
        collaboration_events = data.get("collaboration_events", [])

        # Assign colors to sessions
        self._assign_session_colors(active_sessions)

        # Print status summary
        self._print_status_summary(active_sessions, metrics)

        # Print collaboration insights based on focus mode
        if self.focus_settings.get("show_communication_panel"):
            self._print_communication_panel(network_analysis, collaboration_events)

        if self.focus_settings.get("show_workspace_panel"):
            self._print_workspace_panel(workspace_status)

        if self.focus_settings.get("show_handoffs_panel"):
            self._print_handoffs_panel(collaboration_events)

        # Always show recent activity
        self._print_recent_activity(collaboration_events[:10])

        # Footer with controls
        self._print_footer()

    def _assign_session_colors(self, active_sessions: Dict):
        """Assign consistent colors to sessions."""
        session_ids = list(active_sessions.keys())

        for i, session_id in enumerate(session_ids):
            if session_id not in self.session_color_map:
                color_index = len(self.session_color_map) % len(self.session_colors)
                self.session_color_map[session_id] = self.session_colors[color_index]

    def _print_status_summary(self, active_sessions: Dict, metrics: Any):
        """Print the main status summary."""
        if not metrics:
            return

        # Header with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"\n{self.colors['header']}🐝 AGENT COLLABORATION OBSERVATORY{self.colors['reset']} - {timestamp}"
        )
        print("═" * min(70, self.term_width - 1))

        # Key metrics
        active_count = getattr(metrics, "active_agents", len(active_sessions))
        spawn_count = getattr(metrics, "total_spawns", 0)
        collaboration_count = getattr(metrics, "total_collaborations", 0)
        efficiency = getattr(metrics, "collaboration_efficiency", 0.0)

        print(
            f"📊 {self.colors['success']}{active_count}{self.colors['reset']} active agents  "
            f"🤖 {self.colors['info']}{spawn_count}{self.colors['reset']} spawned  "
            f"🤝 {self.colors['warning']}{collaboration_count}{self.colors['reset']} collaborations  "
            f"⚡ {efficiency:.1%} efficiency"
        )

        # Show active agents with their status
        if active_sessions:
            print(f"\n{self.colors['header']}ACTIVE AGENTS:{self.colors['reset']}")
            for session_id, session in list(active_sessions.items())[
                :6
            ]:  # Show up to 6
                color = self.session_color_map.get(session_id, self.colors["reset"])
                partner_count = len(session.communication_partners)
                spawn_count = len(session.agents_spawned)

                print(
                    f"  {color}●{self.colors['reset']} {session_id[:12]:<12} "
                    f"Partners: {partner_count}  Spawned: {spawn_count}"
                )

            if len(active_sessions) > 6:
                remaining = len(active_sessions) - 6
                print(
                    f"  {self.colors['dim']}... and {remaining} more agents{self.colors['reset']}"
                )

    def _print_communication_panel(self, network_analysis: Any, events: List[Dict]):
        """Print communication patterns panel."""
        print(
            f"\n{self.colors['header']}📡 COMMUNICATION PATTERNS{self.colors['reset']}"
        )
        print("─" * 30)

        if network_analysis:
            central_agents = getattr(network_analysis, "central_agents", [])[:3]
            if central_agents:
                print(
                    f"🎯 Central Agents: {', '.join(agent[:8] for agent in central_agents)}"
                )

            total_edges = getattr(network_analysis, "total_edges", 0)
            if total_edges > 0:
                print(f"🔗 Active Connections: {total_edges}")

        # Show recent communication events
        comm_events = [
            e for e in events if e.get("event_type") == "agent_communication"
        ][:3]
        for event in comm_events:
            source = event.get("primary_session", "unknown")[:8]
            partner = event.get("partner_session", "unknown")[:8]
            print(f"  💬 {source} ↔ {partner}")

    def _print_workspace_panel(self, workspace_status: Any):
        """Print workspace coordination panel."""
        print(
            f"\n{self.colors['header']}📁 WORKSPACE COORDINATION{self.colors['reset']}"
        )
        print("─" * 30)

        if workspace_status:
            concurrent_count = getattr(workspace_status, "concurrent_access_count", 0)
            conflict_count = getattr(workspace_status, "conflict_count", 0)
            hotspots = getattr(workspace_status, "collaboration_hotspots", [])[:3]

            print(f"🔄 Concurrent Access: {concurrent_count} files")
            if conflict_count > 0:
                print(
                    f"{self.colors['warning']}⚠️  Conflicts: {conflict_count}{self.colors['reset']}"
                )

            if hotspots:
                print("🔥 Hotspots:")
                for hotspot in hotspots:
                    filename = os.path.basename(hotspot)
                    print(f"  📄 {filename}")

    def _print_handoffs_panel(self, events: List[Dict]):
        """Print task handoff patterns panel."""
        print(f"\n{self.colors['header']}🔄 TASK HANDOFFS{self.colors['reset']}")
        print("─" * 30)

        handoff_events = [e for e in events if "handoff" in e.get("event_type", "")][:3]
        if handoff_events:
            for event in handoff_events:
                source = event.get("primary_session", "unknown")[:8]
                event_type = event.get("event_type", "handoff")
                print(f"  🔄 {source}: {event_type.replace('_', ' ').title()}")
        else:
            print(
                f"  {self.colors['dim']}No recent handoffs detected{self.colors['reset']}"
            )

    def _print_recent_activity(self, events: List[Dict]):
        """Print recent collaboration activity."""
        if not events:
            return

        print(
            f"\n{self.colors['header']}📋 RECENT COLLABORATION ACTIVITY{self.colors['reset']}"
        )
        print("─" * 40)

        for event in events[:5]:  # Show last 5 events
            timestamp = event.get("timestamp", 0)
            if timestamp:
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            else:
                time_str = "unknown"

            session_id = event.get("session_id", "unknown")[:8]
            event_type = event.get("event_type", "unknown")
            significance = event.get("significance", 0)

            # Choose emoji based on event type
            emoji = "🤝"
            if "spawn" in event_type:
                emoji = "🚀"
            elif "workspace" in event_type:
                emoji = "📁"
            elif "handoff" in event_type:
                emoji = "🔄"
            elif "communication" in event_type:
                emoji = "💬"

            # Color by significance
            if significance >= 7:
                sig_color = self.colors["error"]
            elif significance >= 5:
                sig_color = self.colors["warning"]
            else:
                sig_color = self.colors["info"]

            session_color = self.session_color_map.get(session_id, self.colors["reset"])

            print(
                f"  [{time_str}] {emoji} {session_color}{session_id}{self.colors['reset']} - "
                f"{sig_color}{event_type.replace('_', ' ').title()}{self.colors['reset']}"
            )

    def _print_footer(self):
        """Print footer with controls and status."""
        print(f"\n{self.colors['dim']}─" * min(60, self.term_width - 1))
        print(
            f"🎛️  Focus: {self.settings.focus_mode}  |  "
            f"Refresh: {self.settings.refresh_rate_hz}Hz  |  "
            f"Press Ctrl+C to stop{self.colors['reset']}"
        )

    def _print_header(self):
        """Print the initial header."""
        print(f"{self.colors['header']}")
        print("  ███████ ███    ██ ██   ██  █████  ███    ██  ██████ ███████ ██████  ")
        print("  ██      ████   ██ ██   ██ ██   ██ ████   ██ ██      ██      ██   ██ ")
        print("  █████   ██ ██  ██ ███████ ███████ ██ ██  ██ ██      █████   ██   ██ ")
        print("  ██      ██  ██ ██ ██   ██ ██   ██ ██  ██ ██ ██      ██      ██   ██ ")
        print("  ███████ ██   ████ ██   ██ ██   ██ ██   ████  ██████ ███████ ██████  ")
        print("                                                                       ")
        print("  🐝 AGENT COLLABORATION OBSERVATORY")
        print(f"{self.colors['reset']}")

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system("clear" if os.name == "posix" else "cls")

    async def cleanup(self):
        """Cleanup dashboard resources."""
        if self.is_initialized:
            print(
                f"\n{self.colors['info']}📊 Enhanced Chat Monitor stopped.{self.colors['reset']}"
            )
            print("Thank you for using the Agent Collaboration Observatory!")
