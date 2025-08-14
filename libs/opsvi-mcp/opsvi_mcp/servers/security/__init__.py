"""Security Analysis MCP Server

Provides security scanning, vulnerability detection, and compliance checking.
"""

from .server import SecurityServer, server

__all__ = ["SecurityServer", "server"]