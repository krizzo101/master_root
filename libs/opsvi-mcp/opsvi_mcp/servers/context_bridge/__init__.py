"""
Context Bridge MCP Server
=========================

Bridges IDE context (from Claude Code/Cursor) to custom MCP agents.

Author: Integration Architect Agent
Version: 1.0.0
"""

from .server import ContextBridgeServer
from .client import ContextBridgeClient
from .models import ContextEvent, IDEContext, DiagnosticInfo

__version__ = "1.0.0"
__all__ = [
    "ContextBridgeServer",
    "ContextBridgeClient",
    "ContextEvent",
    "IDEContext",
    "DiagnosticInfo",
]
