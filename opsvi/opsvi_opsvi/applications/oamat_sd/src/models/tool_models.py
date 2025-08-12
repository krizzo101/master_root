"""
Tool Data Models

Enums and dataclasses for MCP tool registry system.
Extracted from mcp_tool_registry.py for better modularity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


def _get_tools_config():
    """Helper to get tools configuration for dataclass defaults"""
    try:
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        return ConfigManager().tools
    except ImportError:
        # Fallback for testing
        from types import SimpleNamespace

        return SimpleNamespace(defaults={"avg_response_time": 0.0})


class ToolCategory(str, Enum):
    """Categories of available tools."""

    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    REASONING = "reasoning"
    DATABASE = "database"
    WEB_SCRAPING = "web_scraping"
    TIME = "time"


class ToolStatus(str, Enum):
    """Tool operational status."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


@dataclass
class ToolMetadata:
    """Metadata for an MCP tool."""

    name: str
    category: ToolCategory
    description: str
    methods: list[str]
    status: ToolStatus = ToolStatus.OPERATIONAL
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    last_health_check: datetime | None = None
    error_count: int = 0
    success_count: int = 0


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""

    tool_name: str
    method: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = field(
        default_factory=lambda: _get_tools_config().defaults["avg_response_time"]
    )
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ParallelExecutionResult:
    """Result of parallel tool execution."""

    results: list[ToolExecutionResult]
    total_time: float
    success_rate: float
    failed_executions: list[ToolExecutionResult] = field(default_factory=list)
