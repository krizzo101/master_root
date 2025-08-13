"""
Claude Code V2 - Fire-and-Forget MCP Server

Enhanced version with decoupled execution and result collection.
Agents are spawned independently and deposit results in a shared location.
"""

from .server import ClaudeCodeV2Server
from .job_manager import FireAndForgetJobManager
from .result_collector import ResultCollector

__all__ = ["ClaudeCodeV2Server", "FireAndForgetJobManager", "ResultCollector"]
