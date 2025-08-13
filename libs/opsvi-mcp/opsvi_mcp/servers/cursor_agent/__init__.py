"""
Cursor Agent MCP Server Integration

Provides MCP tools for programmatically interacting with Cursor IDE agents
including @diagram, @code_review, @documentation, and custom agents.
"""

from .server import CursorAgentServer
from .config import CursorConfig
from .models import AgentRequest, AgentResponse, CursorAgent

__all__ = [
    "CursorAgentServer",
    "CursorConfig",
    "AgentRequest",
    "AgentResponse",
    "CursorAgent",
]
