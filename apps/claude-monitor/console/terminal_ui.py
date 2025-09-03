#!/usr/bin/env python3
"""
Beautiful Rich-based terminal UI for Claude monitoring system
Provides multiple view modes with real-time updates via WebSocket
"""

import asyncio
import json
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import websockets
from rich import print as rprint
from rich.align import Align
from rich.box import DOUBLE_EDGE, MINIMAL, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class ViewMode(Enum):
    """Available view modes"""

    MASTER = "master"
    DOCKER = "docker"
    AGENTS = "agents"
    TOKENS = "tokens"
    SYSTEM = "system"
    COSTS = "costs"


@dataclass
class MonitoringData:
    """Container for all monitoring data"""

    docker_containers: List[Dict] = field(default_factory=list)
    agent_tasks: List[Dict] = field(default_factory=list)
    token_usage: Dict[str, Any] = field(default_factory=dict)
    system_resources: Dict[str, Any] = field(default_factory=dict)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class UIState:
    """Current UI state"""

    current_view: ViewMode = ViewMode.MASTER
    show_help: bool = False
    show_overlay: bool = False
    overlay_data: Optional[Dict] = None
    selected_row: int = 0
    refresh_rate: float = 2.0
    connected: bool = False
    error_message: Optional[str] = None


class TerminalUI:
    """Rich-based terminal UI for monitoring"""

    def __init__(self, websocket_url: str = "ws://localhost:8000/ws"):
        self.console = Console()
        self.websocket_url = websocket_url
        self.data = MonitoringData()
        self.state = UIState()
        self.layout = Layout()
        self.websocket = None

        # Color schemes
        self.colors = {
            "primary": "#00d4aa",
            "secondary": "#0088cc",
            "warning": "#ff6b35",
            "danger": "#e74c3c",
            "success": "#2ecc71",
            "muted": "#7f8c8d",
            "background": "#2c3e50",
        }

        # Setup layout
        self._setup_layout()

    def _setup_layout(self):
        """Setup the Rich layout structure"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        self.layout.get("main").split_row(
            Layout(name="content", ratio=3), Layout(name="sidebar", ratio=1)
        )

    def _create_header(self) -> Panel:
        """Create header with title and connection status"""
        title = Text("Claude Monitor", style=f"bold {self.colors['primary']}")

        # Connection indicator
        if self.state.connected:
            status = Text("🟢 Connected", style=f"bold {self.colors['success']}")
        else:
            status = Text("🔴 Disconnected", style=f"bold {self.colors['danger']}")

        # Current view
        view_name = self.state.current_view.value.title()
        view_text = Text(f"View: {view_name}", style=f"bold {self.colors['secondary']}")

        # Last updated
        time_text = Text(
            f"Updated: {self.data.last_updated.strftime('%H:%M:%S')}",
            style=self.colors["muted"],
        )

        header_content = Columns([title, status, view_text, time_text], align="center")

        return Panel(
            header_content, style=f"bold {self.colors['primary']}", box=ROUNDED
        )

    def _create_footer(self) -> Panel:
        """Create footer with navigation help"""
        if self.state.show_help:
            help_text = (
                "[bold]Navigation:[/bold] Tab=Switch Views, ↑↓=Navigate, Q=Quit, R=Refresh, H=Help\n"
                "[bold]Views:[/bold] 1=Master, 2=Docker, 3=Agents, 4=Tokens, 5=System, 6=Costs\n"
                "[bold]Other:[/bold] O=Overlay, Space=Select, Enter=Details"
            )
        else:
            help_text = "Press [bold]H[/bold] for help • [bold]Q[/bold] to quit • [bold]Tab[/bold] to switch views"

        if self.state.error_message:
            help_text = f"[bold red]Error:[/bold red] {self.state.error_message}"

        return Panel(help_text, style=self.colors["muted"], box=MINIMAL)

    def _create_sidebar(self) -> Panel:
        """Create sidebar with quick stats and controls"""
        tree = Tree("📊 Quick Stats", style=f"bold {self.colors['primary']}")

        # System stats
        sys_branch = tree.add("🖥️ System", style=self.colors["secondary"])
        if self.data.system_resources:
            cpu = self.data.system_resources.get("cpu_percent", 0)
            memory = self.data.system_resources.get("memory_percent", 0)
            sys_branch.add(f"CPU: {cpu:.1f}%")
            sys_branch.add(f"Memory: {memory:.1f}%")

        # Docker stats
        docker_branch = tree.add("🐳 Docker", style=self.colors["secondary"])
        running = len(
            [c for c in self.data.docker_containers if c.get("status") == "running"]
        )
        docker_branch.add(f"Containers: {len(self.data.docker_containers)}")
        docker_branch.add(f"Running: {running}")

        # Token stats
        token_branch = tree.add("🎯 Tokens", style=self.colors["secondary"])
        if self.data.token_usage:
            total = self.data.token_usage.get("total_tokens", 0)
            cost = self.data.cost_analysis.get("total_cost", 0.0)
            token_branch.add(f"Total: {total:,}")
            token_branch.add(f"Cost: ${cost:.2f}")

        # Agent stats
        agent_branch = tree.add("🤖 Agents", style=self.colors["secondary"])
        active = len([a for a in self.data.agent_tasks if a.get("status") == "running"])
        agent_branch.add(f"Tasks: {len(self.data.agent_tasks)}")
        agent_branch.add(f"Active: {active}")

        return Panel(tree, title="Status", box=ROUNDED)

    def _create_master_view(self) -> Panel:
        """Create master view with overview of everything"""
        content = Layout()
        content.split_column(Layout(name="overview", size=8), Layout(name="details"))

        # Overview section with key metrics
        overview_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        overview_table.add_column("Metric", style=self.colors["secondary"])
        overview_table.add_column("Current", justify="right")
        overview_table.add_column("Status", justify="center")

        # Add key metrics
        metrics = [
            (
                "Docker Containers",
                len(self.data.docker_containers),
                "🟢" if self.data.docker_containers else "🔴",
            ),
            (
                "Agent Tasks",
                len(self.data.agent_tasks),
                "🟢" if self.data.agent_tasks else "⚪",
            ),
            ("Token Usage", f"{self.data.token_usage.get('total_tokens', 0):,}", "🟡"),
            (
                "Total Cost",
                f"${self.data.cost_analysis.get('total_cost', 0.0):.2f}",
                "💰",
            ),
            (
                "System CPU",
                f"{self.data.system_resources.get('cpu_percent', 0):.1f}%",
                "🟢",
            ),
            (
                "System Memory",
                f"{self.data.system_resources.get('memory_percent', 0):.1f}%",
                "🟡",
            ),
        ]

        for metric, value, status in metrics:
            overview_table.add_row(metric, str(value), status)

        content.get("overview").update(
            Panel(overview_table, title="System Overview", box=ROUNDED)
        )

        # Recent activity
        activity_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        activity_table.add_column("Time", style=self.colors["muted"])
        activity_table.add_column("Type")
        activity_table.add_column("Description", max_width=50)

        # Mock recent activity (would be populated from actual data)
        activities = [
            (
                datetime.now() - timedelta(minutes=1),
                "Agent",
                "Task completed: docker_monitor",
            ),
            (
                datetime.now() - timedelta(minutes=2),
                "Docker",
                "Container started: claude-app-1",
            ),
            (
                datetime.now() - timedelta(minutes=5),
                "Token",
                "High usage detected: 1000 tokens/min",
            ),
        ]

        for timestamp, activity_type, description in activities:
            activity_table.add_row(
                timestamp.strftime("%H:%M:%S"), activity_type, description
            )

        content.get("details").update(
            Panel(activity_table, title="Recent Activity", box=ROUNDED)
        )

        return Panel(content, title="Master Dashboard", box=DOUBLE_EDGE)

    def _create_docker_view(self) -> Panel:
        """Create Docker containers focused view"""
        table = Table(show_header=True, header_style=f"bold {self.colors['primary']}")
        table.add_column("Name", style=self.colors["secondary"])
        table.add_column("Status", justify="center")
        table.add_column("CPU", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("Network", justify="right")
        table.add_column("Claude Process", justify="center")

        for i, container in enumerate(self.data.docker_containers):
            name = container.get("name", "unknown")
            status = container.get("status", "unknown")
            cpu = f"{container.get('cpu_percent', 0):.1f}%"
            memory = f"{container.get('memory_usage', 0)/1024/1024:.1f}MB"
            network = f"{container.get('network_rx', 0)/1024:.1f}KB/s"
            has_claude = "🟢" if container.get("has_claude_process") else "🔴"

            # Highlight selected row
            style = None
            if (
                i == self.state.selected_row
                and self.state.current_view == ViewMode.DOCKER
            ):
                style = f"bold {self.colors['warning']}"

            table.add_row(name, status, cpu, memory, network, has_claude, style=style)

        if not self.data.docker_containers:
            table.add_row("No containers found", "", "", "", "", "")

        return Panel(table, title="Docker Containers", box=ROUNDED)

    def _create_agents_view(self) -> Panel:
        """Create agent orchestrator focused view"""
        content = Layout()
        content.split_column(
            Layout(name="tasks", ratio=2), Layout(name="progress", ratio=1)
        )

        # Tasks table
        tasks_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        tasks_table.add_column("Task ID", style=self.colors["secondary"])
        tasks_table.add_column("Type")
        tasks_table.add_column("Status", justify="center")
        tasks_table.add_column("Progress", justify="right")
        tasks_table.add_column("Duration")

        for i, task in enumerate(self.data.agent_tasks):
            task_id = task.get("task_id", "unknown")
            task_type = task.get("task_type", "unknown")
            status = task.get("status", "unknown")
            progress = f"{task.get('progress', 0):.0f}%"
            duration = task.get("duration", "0s")

            # Status indicator
            status_icon = {"running": "🟡", "completed": "🟢", "failed": "🔴"}.get(
                status, "⚪"
            )

            # Highlight selected row
            style = None
            if (
                i == self.state.selected_row
                and self.state.current_view == ViewMode.AGENTS
            ):
                style = f"bold {self.colors['warning']}"

            tasks_table.add_row(
                task_id,
                task_type,
                f"{status_icon} {status}",
                progress,
                duration,
                style=style,
            )

        if not self.data.agent_tasks:
            tasks_table.add_row("No active tasks", "", "", "", "")

        content.get("tasks").update(
            Panel(tasks_table, title="Agent Tasks", box=ROUNDED)
        )

        # Progress bars for running tasks
        progress_content = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            running_tasks = [
                t for t in self.data.agent_tasks if t.get("status") == "running"
            ]
            if running_tasks:
                progress_panel = Panel(
                    "\n".join(
                        [
                            f"🟡 {task.get('task_id', 'unknown')}: {task.get('progress', 0):.0f}%"
                            for task in running_tasks
                        ]
                    ),
                    title="Active Progress",
                    box=ROUNDED,
                )
            else:
                progress_panel = Panel(
                    "No active tasks", title="Active Progress", box=ROUNDED
                )

        content.get("progress").update(progress_panel)

        return Panel(content, title="Agent Orchestrator", box=DOUBLE_EDGE)

    def _create_tokens_view(self) -> Panel:
        """Create token usage focused view"""
        content = Layout()
        content.split_row(Layout(name="summary"), Layout(name="breakdown"))

        # Token summary
        summary_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        summary_table.add_column("Metric", style=self.colors["secondary"])
        summary_table.add_column("Value", justify="right")
        summary_table.add_column("Change", justify="right")

        token_data = self.data.token_usage
        metrics = [
            ("Total Tokens", f"{token_data.get('total_tokens', 0):,}", "+1.2%"),
            ("Input Tokens", f"{token_data.get('input_tokens', 0):,}", "+0.8%"),
            ("Output Tokens", f"{token_data.get('output_tokens', 0):,}", "+1.8%"),
            ("Requests", f"{token_data.get('total_requests', 0):,}", "+5"),
            (
                "Avg per Request",
                f"{token_data.get('avg_tokens_per_request', 0):.0f}",
                "-2%",
            ),
        ]

        for metric, value, change in metrics:
            change_style = (
                self.colors["success"]
                if change.startswith("+")
                else self.colors["danger"]
            )
            summary_table.add_row(metric, value, Text(change, style=change_style))

        content.get("summary").update(
            Panel(summary_table, title="Token Summary", box=ROUNDED)
        )

        # Model breakdown
        breakdown_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        breakdown_table.add_column("Model", style=self.colors["secondary"])
        breakdown_table.add_column("Requests", justify="right")
        breakdown_table.add_column("Tokens", justify="right")
        breakdown_table.add_column("Avg/Request", justify="right")

        # Mock model data (would come from actual token usage)
        models = [
            ("claude-3-5-sonnet", 245, 123500, 504),
            ("claude-3-haiku", 89, 25600, 288),
            ("claude-3-opus", 12, 8900, 742),
        ]

        for model, requests, tokens, avg in models:
            breakdown_table.add_row(model, f"{requests:,}", f"{tokens:,}", f"{avg}")

        content.get("breakdown").update(
            Panel(breakdown_table, title="Model Breakdown", box=ROUNDED)
        )

        return Panel(content, title="Token Usage Analysis", box=DOUBLE_EDGE)

    def _create_system_view(self) -> Panel:
        """Create system resources focused view"""
        content = Layout()
        content.split_column(Layout(name="resources", size=8), Layout(name="processes"))

        # System resources
        resources_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        resources_table.add_column("Resource", style=self.colors["secondary"])
        resources_table.add_column("Current", justify="right")
        resources_table.add_column("Peak", justify="right")
        resources_table.add_column("Average", justify="right")
        resources_table.add_column("Status", justify="center")

        sys_data = self.data.system_resources
        resources = [
            (
                "CPU Usage",
                f"{sys_data.get('cpu_percent', 0):.1f}%",
                "85.2%",
                "45.1%",
                "🟢",
            ),
            (
                "Memory Usage",
                f"{sys_data.get('memory_percent', 0):.1f}%",
                "78.5%",
                "52.3%",
                "🟡",
            ),
            (
                "Disk Usage",
                f"{sys_data.get('disk_percent', 0):.1f}%",
                "45.2%",
                "38.9%",
                "🟢",
            ),
            (
                "Network In",
                f"{sys_data.get('network_rx', 0)/1024:.1f} KB/s",
                "1.2 MB/s",
                "256 KB/s",
                "🟢",
            ),
            (
                "Network Out",
                f"{sys_data.get('network_tx', 0)/1024:.1f} KB/s",
                "850 KB/s",
                "180 KB/s",
                "🟢",
            ),
        ]

        for resource, current, peak, average, status in resources:
            resources_table.add_row(resource, current, peak, average, status)

        content.get("resources").update(
            Panel(resources_table, title="System Resources", box=ROUNDED)
        )

        # Top processes
        processes_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        processes_table.add_column("PID", justify="right")
        processes_table.add_column("Name", style=self.colors["secondary"])
        processes_table.add_column("CPU", justify="right")
        processes_table.add_column("Memory", justify="right")
        processes_table.add_column("Claude", justify="center")

        # Mock process data (would come from actual system monitoring)
        processes = [
            (12345, "claude-app", "15.2%", "256MB", "🟢"),
            (12346, "docker", "8.1%", "128MB", "🔴"),
            (12347, "python3", "5.4%", "89MB", "🟡"),
            (12348, "node", "3.2%", "145MB", "🔴"),
        ]

        for pid, name, cpu, memory, is_claude in processes:
            processes_table.add_row(str(pid), name, cpu, memory, is_claude)

        content.get("processes").update(
            Panel(processes_table, title="Top Processes", box=ROUNDED)
        )

        return Panel(content, title="System Monitoring", box=DOUBLE_EDGE)

    def _create_costs_view(self) -> Panel:
        """Create cost analysis focused view"""
        content = Layout()
        content.split_column(Layout(name="summary", size=6), Layout(name="breakdown"))

        # Cost summary
        summary_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        summary_table.add_column("Period", style=self.colors["secondary"])
        summary_table.add_column("Cost", justify="right")
        summary_table.add_column("Tokens", justify="right")
        summary_table.add_column("Rate", justify="right")

        cost_data = self.data.cost_analysis
        periods = [
            (
                "Today",
                f"${cost_data.get('daily_cost', 0.0):.2f}",
                "12,500",
                "$0.0080/1k",
            ),
            (
                "This Week",
                f"${cost_data.get('weekly_cost', 0.0):.2f}",
                "95,200",
                "$0.0078/1k",
            ),
            (
                "This Month",
                f"${cost_data.get('monthly_cost', 0.0):.2f}",
                "425,800",
                "$0.0082/1k",
            ),
            (
                "Total",
                f"${cost_data.get('total_cost', 0.0):.2f}",
                "1,250,000",
                "$0.0081/1k",
            ),
        ]

        for period, cost, tokens, rate in periods:
            summary_table.add_row(period, cost, tokens, rate)

        content.get("summary").update(
            Panel(summary_table, title="Cost Summary", box=ROUNDED)
        )

        # Project breakdown
        breakdown_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        breakdown_table.add_column("Project", style=self.colors["secondary"])
        breakdown_table.add_column("Today", justify="right")
        breakdown_table.add_column("Week", justify="right")
        breakdown_table.add_column("Month", justify="right")
        breakdown_table.add_column("% of Total", justify="right")

        # Mock project data (would come from actual cost tracking)
        projects = [
            ("claude-monitor", "$2.45", "$18.50", "$125.80", "35%"),
            ("agent-orchestrator", "$1.85", "$14.20", "$95.60", "28%"),
            ("web-dashboard", "$1.20", "$8.90", "$62.40", "18%"),
            ("testing", "$0.85", "$5.40", "$35.20", "10%"),
            ("other", "$0.65", "$3.00", "$31.00", "9%"),
        ]

        for project, today, week, month, percent in projects:
            breakdown_table.add_row(project, today, week, month, percent)

        content.get("breakdown").update(
            Panel(breakdown_table, title="Project Breakdown", box=ROUNDED)
        )

        return Panel(content, title="Cost Analysis", box=DOUBLE_EDGE)

    def _get_current_content(self) -> Panel:
        """Get content panel for current view mode"""
        view_methods = {
            ViewMode.MASTER: self._create_master_view,
            ViewMode.DOCKER: self._create_docker_view,
            ViewMode.AGENTS: self._create_agents_view,
            ViewMode.TOKENS: self._create_tokens_view,
            ViewMode.SYSTEM: self._create_system_view,
            ViewMode.COSTS: self._create_costs_view,
        }

        return view_methods[self.state.current_view]()

    def _create_overlay(self) -> Optional[Panel]:
        """Create overlay panel if needed"""
        if not self.state.show_overlay:
            return None

        if (
            self.state.current_view == ViewMode.DOCKER
            and self.state.selected_row < len(self.data.docker_containers)
        ):
            # Docker container details overlay
            container = self.data.docker_containers[self.state.selected_row]

            details_table = Table(show_header=False, box=MINIMAL)
            details_table.add_column(
                "Property", style=f"bold {self.colors['secondary']}"
            )
            details_table.add_column("Value")

            details = [
                ("Container ID", container.get("id", "unknown")[:12]),
                ("Image", container.get("image", "unknown")),
                ("Created", container.get("created", "unknown")),
                ("Ports", ", ".join(container.get("ports", []))),
                ("Volumes", str(len(container.get("volumes", [])))),
                ("Environment", str(len(container.get("env_vars", [])))),
                ("Command", container.get("command", "unknown")),
                ("Working Dir", container.get("working_dir", "unknown")),
            ]

            for prop, value in details:
                details_table.add_row(prop, value)

            return Panel(
                details_table,
                title=f"Container Details: {container.get('name', 'unknown')}",
                border_style=self.colors["warning"],
                box=DOUBLE_EDGE,
            )

        elif (
            self.state.current_view == ViewMode.AGENTS
            and self.state.selected_row < len(self.data.agent_tasks)
        ):
            # Agent task details overlay
            task = self.data.agent_tasks[self.state.selected_row]

            details_content = []
            details_content.append(
                f"[bold]Task ID:[/bold] {task.get('task_id', 'unknown')}"
            )
            details_content.append(
                f"[bold]Type:[/bold] {task.get('task_type', 'unknown')}"
            )
            details_content.append(
                f"[bold]Status:[/bold] {task.get('status', 'unknown')}"
            )
            details_content.append(f"[bold]Progress:[/bold] {task.get('progress', 0)}%")
            details_content.append(
                f"[bold]Duration:[/bold] {task.get('duration', '0s')}"
            )

            if "prompt" in task:
                prompt = (
                    task["prompt"][:200] + "..."
                    if len(task["prompt"]) > 200
                    else task["prompt"]
                )
                details_content.append(f"\n[bold]Prompt:[/bold]\n{prompt}")

            if "dependencies" in task:
                deps = ", ".join(task["dependencies"])
                details_content.append(f"\n[bold]Dependencies:[/bold] {deps}")

            return Panel(
                "\n".join(details_content),
                title="Task Details",
                border_style=self.colors["warning"],
                box=DOUBLE_EDGE,
            )

        elif self.state.current_view == ViewMode.TOKENS:
            # Token usage trends overlay
            trend_table = Table(
                show_header=True, header_style=f"bold {self.colors['primary']}"
            )
            trend_table.add_column("Time Period", style=self.colors["secondary"])
            trend_table.add_column("Input", justify="right")
            trend_table.add_column("Output", justify="right")
            trend_table.add_column("Total", justify="right")
            trend_table.add_column("Cost", justify="right")

            # Mock hourly data
            trends = [
                ("Last Hour", "2,500", "1,800", "4,300", "$0.35"),
                ("2 Hours Ago", "1,900", "1,200", "3,100", "$0.25"),
                ("3 Hours Ago", "3,200", "2,100", "5,300", "$0.43"),
                ("4 Hours Ago", "1,800", "1,000", "2,800", "$0.23"),
                ("5 Hours Ago", "2,100", "1,400", "3,500", "$0.28"),
            ]

            for period, input_tokens, output_tokens, total, cost in trends:
                trend_table.add_row(period, input_tokens, output_tokens, total, cost)

            return Panel(
                trend_table,
                title="Token Usage Trends",
                border_style=self.colors["warning"],
                box=DOUBLE_EDGE,
            )

        elif self.state.current_view == ViewMode.SYSTEM:
            # System process tree overlay
            process_tree = Tree(
                "🖥️ System Process Tree", style=f"bold {self.colors['primary']}"
            )

            # Mock process hierarchy
            docker_branch = process_tree.add(
                "🐳 Docker (PID: 1234)", style=self.colors["secondary"]
            )
            docker_branch.add("🔸 claude-app-1 (PID: 2345)")
            docker_branch.add("🔸 claude-app-2 (PID: 2346)")

            python_branch = process_tree.add(
                "🐍 Python Processes", style=self.colors["secondary"]
            )
            python_branch.add("🔸 monitoring_service.py (PID: 3456)")
            python_branch.add("🔸 terminal_ui.py (PID: 3457)")
            python_branch.add("🔸 data_collector.py (PID: 3458)")

            node_branch = process_tree.add(
                "📦 Node Processes", style=self.colors["secondary"]
            )
            node_branch.add("🔸 web-dashboard (PID: 4567)")

            return Panel(
                process_tree,
                title="Process Hierarchy",
                border_style=self.colors["warning"],
                box=DOUBLE_EDGE,
            )

        elif self.state.current_view == ViewMode.COSTS:
            # Cost projection overlay
            projection_table = Table(
                show_header=True, header_style=f"bold {self.colors['primary']}"
            )
            projection_table.add_column("Scenario", style=self.colors["secondary"])
            projection_table.add_column("Daily", justify="right")
            projection_table.add_column("Weekly", justify="right")
            projection_table.add_column("Monthly", justify="right")
            projection_table.add_column("Yearly", justify="right")

            projections = [
                ("Current Rate", "$7.00", "$49.00", "$210.00", "$2,555.00"),
                ("10% Increase", "$7.70", "$53.90", "$231.00", "$2,810.50"),
                ("20% Decrease", "$5.60", "$39.20", "$168.00", "$2,044.00"),
                ("Peak Usage", "$12.50", "$87.50", "$375.00", "$4,562.50"),
            ]

            for scenario, daily, weekly, monthly, yearly in projections:
                projection_table.add_row(scenario, daily, weekly, monthly, yearly)

            return Panel(
                projection_table,
                title="Cost Projections",
                border_style=self.colors["warning"],
                box=DOUBLE_EDGE,
            )

        return None

    def _render_ui(self) -> Layout:
        """Render the complete UI"""
        self.layout.get("header").update(self._create_header())
        self.layout.get("content").update(self._get_current_content())
        self.layout.get("sidebar").update(self._create_sidebar())
        self.layout.get("footer").update(self._create_footer())

        # Add overlay if active
        overlay = self._create_overlay()
        if overlay:
            # Create a centered overlay layout
            overlay_layout = Layout()
            overlay_layout.split_column(
                Layout(name="top", size=3),
                Layout(name="middle"),
                Layout(name="bottom", size=3),
            )
            overlay_layout.get("middle").split_row(
                Layout(name="left", ratio=1),
                Layout(name="center", ratio=2),
                Layout(name="right", ratio=1),
            )
            overlay_layout.get("middle").get("center").update(overlay)

            # Layer the overlay on top of the main layout
            main_content = self.layout
            combined_layout = Layout()
            combined_layout.split_column(
                Layout(main_content, ratio=1), Layout(overlay_layout, ratio=1)
            )
            return combined_layout

        return self.layout

    async def _connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.state.connected = True
            self.state.error_message = None

            # Listen for updates
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._update_data(data)
                except json.JSONDecodeError:
                    self.state.error_message = "Invalid JSON received from server"
                except Exception as e:
                    self.state.error_message = f"Error processing update: {str(e)}"

        except Exception as e:
            self.state.connected = False
            self.state.error_message = f"Connection failed: {str(e)}"

    async def _update_data(self, data: Dict):
        """Update monitoring data from WebSocket"""
        if "docker_containers" in data:
            self.data.docker_containers = data["docker_containers"]
        if "agent_tasks" in data:
            self.data.agent_tasks = data["agent_tasks"]
        if "token_usage" in data:
            self.data.token_usage = data["token_usage"]
        if "system_resources" in data:
            self.data.system_resources = data["system_resources"]
        if "cost_analysis" in data:
            self.data.cost_analysis = data["cost_analysis"]

        self.data.last_updated = datetime.now()

    def _handle_key(self, key: str) -> bool:
        """Handle keyboard input, return False to quit"""
        key = key.lower()

        if key == "q":
            return False
        elif key == "h":
            self.state.show_help = not self.state.show_help
        elif key == "r":
            # Refresh data
            self.data.last_updated = datetime.now()
        elif key == "o":
            self.state.show_overlay = not self.state.show_overlay
        elif key == "tab":
            # Switch to next view
            views = list(ViewMode)
            current_idx = views.index(self.state.current_view)
            next_idx = (current_idx + 1) % len(views)
            self.state.current_view = views[next_idx]
            self.state.selected_row = 0
        elif key in "123456":
            # Quick view switch
            view_map = {
                "1": ViewMode.MASTER,
                "2": ViewMode.DOCKER,
                "3": ViewMode.AGENTS,
                "4": ViewMode.TOKENS,
                "5": ViewMode.SYSTEM,
                "6": ViewMode.COSTS,
            }
            if key in view_map:
                self.state.current_view = view_map[key]
                self.state.selected_row = 0
        elif key in ["up", "down"]:
            # Navigate within current view
            if key == "up":
                self.state.selected_row = max(0, self.state.selected_row - 1)
            else:
                # Determine max rows based on current view
                max_rows = 0
                if self.state.current_view == ViewMode.DOCKER:
                    max_rows = len(self.data.docker_containers) - 1
                elif self.state.current_view == ViewMode.AGENTS:
                    max_rows = len(self.data.agent_tasks) - 1

                self.state.selected_row = min(max_rows, self.state.selected_row + 1)

        return True

    def _get_key_input(self) -> Optional[str]:
        """Non-blocking keyboard input using select"""
        # Use select to check if input is available without blocking
        if select.select([sys.stdin], [], [], 0.0)[0]:
            try:
                key = sys.stdin.read(1)

                # Handle special keys (arrow keys, etc.)
                if key == "\x1b":  # ESC sequence
                    # Read the rest of the sequence
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq = sys.stdin.read(2)
                        if seq == "[A":
                            return "up"
                        elif seq == "[B":
                            return "down"
                        elif seq == "[C":
                            return "right"
                        elif seq == "[D":
                            return "left"
                elif key == "\t":
                    return "tab"
                elif key in ["\r", "\n"]:
                    return "enter"
                elif key == "\x03":  # Ctrl+C
                    return "quit"

                return key
            except:
                return None
        return None

    async def run(self):
        """Main UI loop"""
        # Save original terminal settings
        old_settings = None
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except:
            pass  # Not a terminal

        try:
            # Start WebSocket connection in background
            websocket_task = asyncio.create_task(self._connect_websocket())

            # Use a simpler approach without Live screen mode to avoid conflicts
            console = Console()
            try:
                # Simulate some initial data for demo
                self.data.docker_containers = [
                    {
                        "name": "claude-app-1",
                        "status": "running",
                        "cpu_percent": 15.2,
                        "memory_usage": 268435456,  # 256MB
                        "network_rx": 1024,
                        "has_claude_process": True,
                        "id": "abc123def456",
                        "image": "claude-monitor:latest",
                        "created": "2024-01-15 10:30:00",
                        "ports": ["8000:8000", "9000:9000"],
                        "volumes": ["/data:/app/data"],
                        "env_vars": ["ENV=production", "DEBUG=false"],
                        "command": "python app.py",
                        "working_dir": "/app",
                    },
                    {
                        "name": "claude-app-2",
                        "status": "running",
                        "cpu_percent": 8.1,
                        "memory_usage": 134217728,  # 128MB
                        "network_rx": 512,
                        "has_claude_process": True,
                        "id": "def456ghi789",
                        "image": "claude-worker:latest",
                        "created": "2024-01-15 10:35:00",
                        "ports": ["8001:8000"],
                        "volumes": ["/logs:/app/logs"],
                        "env_vars": ["ENV=production"],
                        "command": "python worker.py",
                        "working_dir": "/app",
                    },
                ]

                self.data.agent_tasks = [
                    {
                        "task_id": "backend_service",
                        "task_type": "development",
                        "status": "running",
                        "progress": 75,
                        "duration": "2m 30s",
                        "prompt": "Create a comprehensive monitoring backend service with FastAPI and WebSocket support...",
                        "dependencies": [],
                    },
                    {
                        "task_id": "console_ui",
                        "task_type": "development",
                        "status": "completed",
                        "progress": 100,
                        "duration": "4m 15s",
                        "prompt": "Create a beautiful Rich-based terminal UI for monitoring with multiple view modes...",
                        "dependencies": ["backend_service"],
                    },
                ]

                self.data.token_usage = {
                    "total_tokens": 125000,
                    "input_tokens": 75000,
                    "output_tokens": 50000,
                    "total_requests": 248,
                    "avg_tokens_per_request": 504,
                }

                self.data.system_resources = {
                    "cpu_percent": 35.2,
                    "memory_percent": 62.8,
                    "disk_percent": 41.5,
                    "network_rx": 2048,
                    "network_tx": 1536,
                }

                self.data.cost_analysis = {
                    "daily_cost": 7.0,
                    "weekly_cost": 50.0,
                    "monthly_cost": 350.0,
                    "total_cost": 1250.0,
                }

                # Main UI loop without Live screen mode
                running = True
                last_render = 0
                while running:
                    # Only render every 2 seconds unless there's input
                    import time

                    now = time.time()
                    if now - last_render > 2:
                        console.clear()
                        console.print(self._render_ui())
                        console.print(
                            "\nPress Tab to switch views, 1-6 for direct view, Q to quit, H for help"
                        )
                        last_render = now

                    # Handle keyboard input (non-blocking check)
                    key = self._get_key_input()
                    if key:
                        running = self._handle_key(key)
                        # Re-render immediately after input
                        console.clear()
                        console.print(self._render_ui())
                        console.print(
                            "\nPress Tab to switch views, 1-6 for direct view, Q to quit, H for help"
                        )
                        last_render = now

                    # Small delay to prevent excessive CPU usage
                    await asyncio.sleep(0.2)

                    # Check for WebSocket errors
                    if websocket_task.done():
                        try:
                            await websocket_task
                        except Exception as e:
                            self.state.error_message = f"WebSocket error: {str(e)}"
                            # Restart connection
                            websocket_task = asyncio.create_task(
                                self._connect_websocket()
                            )

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            pass
        finally:
            if self.websocket:
                await self.websocket.close()
            # Restore terminal settings
            if old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except:
                    pass


async def main():
    """Main entry point"""
    ui = TerminalUI()
    await ui.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
