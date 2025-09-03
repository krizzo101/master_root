#!/usr/bin/env python3
"""
View Manager for Claude Monitor Console UI

Handles view layouts, switching, overlays, data flow, and filtering/sorting
for the Rich-based terminal interface.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from rich.align import Align
from rich.box import DOUBLE_EDGE, MINIMAL, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
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


class SortOrder(Enum):
    """Sort order options"""

    ASC = "asc"
    DESC = "desc"


@dataclass
class FilterConfig:
    """Configuration for data filtering"""

    field: str
    operator: str  # eq, ne, gt, lt, contains, startswith, endswith
    value: Any
    case_sensitive: bool = False


@dataclass
class SortConfig:
    """Configuration for data sorting"""

    field: str
    order: SortOrder = SortOrder.ASC
    numeric: bool = False


@dataclass
class ViewConfig:
    """Configuration for a specific view"""

    name: str
    title: str
    description: str
    sortable_fields: List[str] = field(default_factory=list)
    filterable_fields: List[str] = field(default_factory=list)
    default_sort: Optional[SortConfig] = None
    refresh_rate: float = 2.0
    supports_overlay: bool = True
    supports_selection: bool = True


@dataclass
class ViewState:
    """Current state of a view"""

    mode: ViewMode
    selected_row: int = 0
    sort_config: Optional[SortConfig] = None
    filters: List[FilterConfig] = field(default_factory=list)
    show_overlay: bool = False
    overlay_data: Optional[Dict] = None
    last_refresh: datetime = field(default_factory=datetime.now)


class BaseView(ABC):
    """Abstract base class for all views"""

    def __init__(self, config: ViewConfig, colors: Dict[str, str]):
        self.config = config
        self.colors = colors
        self.state = ViewState(mode=ViewMode.MASTER)

    @abstractmethod
    def render_content(self, data: Dict[str, Any]) -> Panel:
        """Render the main content panel for this view"""
        pass

    @abstractmethod
    def render_overlay(self, data: Dict[str, Any]) -> Optional[Panel]:
        """Render overlay panel if applicable"""
        pass

    @abstractmethod
    def get_data_for_view(self, data: Dict[str, Any]) -> List[Dict]:
        """Extract and prepare data for this view"""
        pass

    def apply_filters(self, data: List[Dict]) -> List[Dict]:
        """Apply current filters to data"""
        filtered_data = data.copy()

        for filter_config in self.state.filters:
            filtered_data = self._apply_single_filter(filtered_data, filter_config)

        return filtered_data

    def apply_sort(self, data: List[Dict]) -> List[Dict]:
        """Apply current sort configuration to data"""
        if not self.state.sort_config:
            return data

        sort_config = self.state.sort_config
        reverse = sort_config.order == SortOrder.DESC

        def sort_key(item):
            value = item.get(sort_config.field, "")
            if sort_config.numeric:
                try:
                    return float(value) if value != "" else 0
                except (ValueError, TypeError):
                    return 0
            return str(value).lower()

        return sorted(data, key=sort_key, reverse=reverse)

    def _apply_single_filter(
        self, data: List[Dict], filter_config: FilterConfig
    ) -> List[Dict]:
        """Apply a single filter to the data"""
        result = []

        for item in data:
            field_value = item.get(filter_config.field, "")
            filter_value = filter_config.value

            # Handle case sensitivity
            if isinstance(field_value, str) and not filter_config.case_sensitive:
                field_value = field_value.lower()
            if isinstance(filter_value, str) and not filter_config.case_sensitive:
                filter_value = filter_value.lower()

            # Apply operator
            match = False
            if filter_config.operator == "eq":
                match = field_value == filter_value
            elif filter_config.operator == "ne":
                match = field_value != filter_value
            elif filter_config.operator == "gt":
                try:
                    match = float(field_value) > float(filter_value)
                except (ValueError, TypeError):
                    match = False
            elif filter_config.operator == "lt":
                try:
                    match = float(field_value) < float(filter_value)
                except (ValueError, TypeError):
                    match = False
            elif filter_config.operator == "contains":
                match = str(filter_value) in str(field_value)
            elif filter_config.operator == "startswith":
                match = str(field_value).startswith(str(filter_value))
            elif filter_config.operator == "endswith":
                match = str(field_value).endswith(str(filter_value))

            if match:
                result.append(item)

        return result


class MasterView(BaseView):
    """Master dashboard view"""

    def get_data_for_view(self, data: Dict[str, Any]) -> List[Dict]:
        """Get overview metrics for master view"""
        return [
            {
                "metric": "Docker Containers",
                "value": len(data.get("docker_containers", [])),
                "status": "🟢" if data.get("docker_containers") else "🔴",
            },
            {
                "metric": "Agent Tasks",
                "value": len(data.get("agent_tasks", [])),
                "status": "🟢" if data.get("agent_tasks") else "⚪",
            },
            {
                "metric": "Token Usage",
                "value": f"{data.get('token_usage', {}).get('total_tokens', 0):,}",
                "status": "🟡",
            },
        ]

    def render_content(self, data: Dict[str, Any]) -> Panel:
        """Render master view content"""
        content = Layout()
        content.split_column(Layout(name="overview", size=8), Layout(name="details"))

        # Overview metrics table
        overview_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        overview_table.add_column("Metric", style=self.colors["secondary"])
        overview_table.add_column("Current", justify="right")
        overview_table.add_column("Status", justify="center")

        metrics_data = self.get_data_for_view(data)
        for item in metrics_data:
            overview_table.add_row(item["metric"], str(item["value"]), item["status"])

        content["overview"] = Panel(
            overview_table, title="System Overview", box=ROUNDED
        )

        # Recent activity
        activity_table = Table(
            show_header=True, header_style=f"bold {self.colors['primary']}"
        )
        activity_table.add_column("Time", style=self.colors["muted"])
        activity_table.add_column("Type")
        activity_table.add_column("Description", max_width=50)

        # Mock recent activity
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

        content["details"] = Panel(activity_table, title="Recent Activity", box=ROUNDED)

        return Panel(content, title="Master Dashboard", box=DOUBLE_EDGE)

    def render_overlay(self, data: Dict[str, Any]) -> Optional[Panel]:
        """Master view doesn't have overlays"""
        return None


class DockerView(BaseView):
    """Docker containers view"""

    def get_data_for_view(self, data: Dict[str, Any]) -> List[Dict]:
        """Get docker containers data"""
        return data.get("docker_containers", [])

    def render_content(self, data: Dict[str, Any]) -> Panel:
        """Render docker view content"""
        table = Table(show_header=True, header_style=f"bold {self.colors['primary']}")
        table.add_column("Name", style=self.colors["secondary"])
        table.add_column("Status", justify="center")
        table.add_column("CPU", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("Network", justify="right")
        table.add_column("Claude Process", justify="center")

        containers_data = self.get_data_for_view(data)
        filtered_data = self.apply_filters(containers_data)
        sorted_data = self.apply_sort(filtered_data)

        for i, container in enumerate(sorted_data):
            name = container.get("name", "unknown")
            status = container.get("status", "unknown")
            cpu = f"{container.get('cpu_percent', 0):.1f}%"
            memory = f"{container.get('memory_usage', 0)/1024/1024:.1f}MB"
            network = f"{container.get('network_rx', 0)/1024:.1f}KB/s"
            has_claude = "🟢" if container.get("has_claude_process") else "🔴"

            # Highlight selected row
            style = None
            if i == self.state.selected_row and self.config.supports_selection:
                style = f"bold {self.colors['warning']}"

            table.add_row(name, status, cpu, memory, network, has_claude, style=style)

        if not sorted_data:
            table.add_row("No containers found", "", "", "", "", "")

        return Panel(table, title="Docker Containers", box=ROUNDED)

    def render_overlay(self, data: Dict[str, Any]) -> Optional[Panel]:
        """Render docker container details overlay"""
        containers = self.get_data_for_view(data)
        if not containers or self.state.selected_row >= len(containers):
            return None

        container = containers[self.state.selected_row]

        details_table = Table(show_header=False, box=MINIMAL)
        details_table.add_column("Property", style=f"bold {self.colors['secondary']}")
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


class AgentsView(BaseView):
    """Agent tasks view"""

    def get_data_for_view(self, data: Dict[str, Any]) -> List[Dict]:
        """Get agent tasks data"""
        return data.get("agent_tasks", [])

    def render_content(self, data: Dict[str, Any]) -> Panel:
        """Render agents view content"""
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

        tasks_data = self.get_data_for_view(data)
        filtered_data = self.apply_filters(tasks_data)
        sorted_data = self.apply_sort(filtered_data)

        for i, task in enumerate(sorted_data):
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
            if i == self.state.selected_row and self.config.supports_selection:
                style = f"bold {self.colors['warning']}"

            tasks_table.add_row(
                task_id,
                task_type,
                f"{status_icon} {status}",
                progress,
                duration,
                style=style,
            )

        if not sorted_data:
            tasks_table.add_row("No active tasks", "", "", "", "")

        content["tasks"] = Panel(tasks_table, title="Agent Tasks", box=ROUNDED)

        # Progress summary for running tasks
        running_tasks = [t for t in sorted_data if t.get("status") == "running"]
        if running_tasks:
            progress_content = "\n".join(
                [
                    f"🟡 {task.get('task_id', 'unknown')}: {task.get('progress', 0):.0f}%"
                    for task in running_tasks
                ]
            )
        else:
            progress_content = "No active tasks"

        content["progress"] = Panel(
            progress_content, title="Active Progress", box=ROUNDED
        )

        return Panel(content, title="Agent Orchestrator", box=DOUBLE_EDGE)

    def render_overlay(self, data: Dict[str, Any]) -> Optional[Panel]:
        """Render agent task details overlay"""
        tasks = self.get_data_for_view(data)
        if not tasks or self.state.selected_row >= len(tasks):
            return None

        task = tasks[self.state.selected_row]

        details_content = []
        details_content.append(
            f"[bold]Task ID:[/bold] {task.get('task_id', 'unknown')}"
        )
        details_content.append(f"[bold]Type:[/bold] {task.get('task_type', 'unknown')}")
        details_content.append(f"[bold]Status:[/bold] {task.get('status', 'unknown')}")
        details_content.append(f"[bold]Progress:[/bold] {task.get('progress', 0)}%")
        details_content.append(f"[bold]Duration:[/bold] {task.get('duration', '0s')}")

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


class ViewManager:
    """Central manager for all UI views"""

    def __init__(self, colors: Dict[str, str]):
        self.colors = colors
        self.current_view: ViewMode = ViewMode.MASTER
        self.views: Dict[ViewMode, BaseView] = {}
        self.view_configs: Dict[ViewMode, ViewConfig] = {}

        # Initialize view configurations
        self._init_view_configs()

        # Initialize views
        self._init_views()

    def _init_view_configs(self):
        """Initialize configuration for all views"""
        self.view_configs = {
            ViewMode.MASTER: ViewConfig(
                name="master",
                title="Master Dashboard",
                description="Overview of all system components",
                sortable_fields=["metric", "value"],
                filterable_fields=["metric"],
                supports_overlay=False,
                supports_selection=False,
            ),
            ViewMode.DOCKER: ViewConfig(
                name="docker",
                title="Docker Containers",
                description="Docker container monitoring and management",
                sortable_fields=["name", "status", "cpu_percent", "memory_usage"],
                filterable_fields=["name", "status", "has_claude_process"],
                default_sort=SortConfig(field="name", order=SortOrder.ASC),
            ),
            ViewMode.AGENTS: ViewConfig(
                name="agents",
                title="Agent Tasks",
                description="Agent orchestration and task management",
                sortable_fields=["task_id", "task_type", "status", "progress"],
                filterable_fields=["task_type", "status"],
                default_sort=SortConfig(
                    field="progress", order=SortOrder.DESC, numeric=True
                ),
            ),
            ViewMode.TOKENS: ViewConfig(
                name="tokens",
                title="Token Usage",
                description="Token consumption and cost analysis",
                sortable_fields=["model", "requests", "tokens"],
                filterable_fields=["model"],
                supports_selection=False,
            ),
            ViewMode.SYSTEM: ViewConfig(
                name="system",
                title="System Resources",
                description="System resource monitoring",
                sortable_fields=["resource", "current", "peak"],
                filterable_fields=["resource"],
                supports_selection=False,
            ),
            ViewMode.COSTS: ViewConfig(
                name="costs",
                title="Cost Analysis",
                description="Cost tracking and projections",
                sortable_fields=["period", "cost", "tokens"],
                filterable_fields=["period"],
                supports_selection=False,
            ),
        }

    def _init_views(self):
        """Initialize all view instances"""
        self.views = {
            ViewMode.MASTER: MasterView(
                self.view_configs[ViewMode.MASTER], self.colors
            ),
            ViewMode.DOCKER: DockerView(
                self.view_configs[ViewMode.DOCKER], self.colors
            ),
            ViewMode.AGENTS: AgentsView(
                self.view_configs[ViewMode.AGENTS], self.colors
            ),
            # Token, System, and Costs views would be implemented similarly
            # For now, using simplified versions
        }

        # Set default sort for views that have it configured
        for mode, view in self.views.items():
            config = self.view_configs[mode]
            if config.default_sort:
                view.state.sort_config = config.default_sort

    def switch_view(self, mode: ViewMode):
        """Switch to a different view mode"""
        self.current_view = mode
        # Reset selection when switching views
        if mode in self.views:
            self.views[mode].state.selected_row = 0

    def get_current_view(self) -> BaseView:
        """Get the currently active view"""
        return self.views.get(self.current_view)

    def render_current_view(self, data: Dict[str, Any]) -> Panel:
        """Render content for the current view"""
        view = self.get_current_view()
        if view:
            return view.render_content(data)
        return Panel("View not found", title="Error")

    def render_current_overlay(self, data: Dict[str, Any]) -> Optional[Panel]:
        """Render overlay for the current view if active"""
        view = self.get_current_view()
        if view and view.state.show_overlay:
            return view.render_overlay(data)
        return None

    def handle_navigation(self, direction: str, data: Dict[str, Any]) -> bool:
        """Handle navigation within current view"""
        view = self.get_current_view()
        if not view or not view.config.supports_selection:
            return False

        view_data = view.get_data_for_view(data)
        filtered_data = view.apply_filters(view_data)
        max_rows = len(filtered_data) - 1

        if direction == "up":
            view.state.selected_row = max(0, view.state.selected_row - 1)
        elif direction == "down":
            view.state.selected_row = min(max_rows, view.state.selected_row + 1)

        return True

    def toggle_overlay(self):
        """Toggle overlay for current view"""
        view = self.get_current_view()
        if view and view.config.supports_overlay:
            view.state.show_overlay = not view.state.show_overlay

    def add_filter(
        self, field: str, operator: str, value: Any, case_sensitive: bool = False
    ):
        """Add filter to current view"""
        view = self.get_current_view()
        if not view:
            return False

        config = self.view_configs[self.current_view]
        if field not in config.filterable_fields:
            return False

        filter_config = FilterConfig(
            field=field, operator=operator, value=value, case_sensitive=case_sensitive
        )
        view.state.filters.append(filter_config)
        return True

    def remove_filter(self, field: str):
        """Remove filter from current view"""
        view = self.get_current_view()
        if not view:
            return False

        view.state.filters = [f for f in view.state.filters if f.field != field]
        return True

    def clear_filters(self):
        """Clear all filters from current view"""
        view = self.get_current_view()
        if view:
            view.state.filters.clear()

    def set_sort(
        self, field: str, order: SortOrder = SortOrder.ASC, numeric: bool = False
    ):
        """Set sort configuration for current view"""
        view = self.get_current_view()
        if not view:
            return False

        config = self.view_configs[self.current_view]
        if field not in config.sortable_fields:
            return False

        view.state.sort_config = SortConfig(field=field, order=order, numeric=numeric)
        return True

    def get_view_info(self) -> Dict[str, Any]:
        """Get information about current view and available actions"""
        view = self.get_current_view()
        if not view:
            return {}

        config = self.view_configs[self.current_view]

        return {
            "mode": self.current_view.value,
            "title": config.title,
            "description": config.description,
            "supports_overlay": config.supports_overlay,
            "supports_selection": config.supports_selection,
            "sortable_fields": config.sortable_fields,
            "filterable_fields": config.filterable_fields,
            "current_sort": view.state.sort_config.field
            if view.state.sort_config
            else None,
            "active_filters": len(view.state.filters),
            "selected_row": view.state.selected_row,
            "overlay_active": view.state.show_overlay,
        }

    def get_available_views(self) -> List[Dict[str, str]]:
        """Get list of all available views"""
        return [
            {
                "mode": mode.value,
                "title": config.title,
                "description": config.description,
                "key": str(i + 1),
            }
            for i, (mode, config) in enumerate(self.view_configs.items())
        ]

    def search_current_view(self, query: str, data: Dict[str, Any]) -> List[Dict]:
        """Search within current view data"""
        view = self.get_current_view()
        if not view:
            return []

        view_data = view.get_data_for_view(data)
        results = []

        query_lower = query.lower()

        for item in view_data:
            # Search in all string fields
            for key, value in item.items():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(item)
                    break

        return results
