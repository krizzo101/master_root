"""Claude Code V3 - Enhanced MCP Server with intelligent orchestration"""

from .server import server
from .config import EnhancedConfig
from .task_decomposer import TaskDecomposer
from .timeout_manager import TimeoutManager

__all__ = [
    "server",
    "EnhancedConfig",
    "TaskDecomposer",
    "TimeoutManager"
]

__version__ = "3.0.0"