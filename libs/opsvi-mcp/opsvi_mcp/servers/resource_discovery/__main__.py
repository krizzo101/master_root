#!/usr/bin/env python3
"""Entry point for the Resource Discovery MCP server."""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
