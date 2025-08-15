#!/usr/bin/env python3
"""
Test to understand how FastMCP handles tool parameters
"""

import asyncio
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any

# Create a test server
mcp = FastMCP("test-server")

@mcp.tool()
async def simple_tool(text: str, number: int = 42) -> dict:
    """A simple tool with basic parameters"""
    return {"text": text, "number": number}

@mcp.tool()
async def complex_tool(
    items: List[str],
    options: Optional[Dict[str, Any]] = None,
    flag: bool = False
) -> dict:
    """A tool with complex parameters"""
    return {"items": items, "options": options or {}, "flag": flag}

# Print tool information
print("Registered tools:")
for name, tool_info in mcp._tool_manager._tools.items():
    print(f"\n{name}:")
    print(f"  Function: {tool_info}")
    
print("\n\nExploring MCP attributes:")
print(f"MCP attributes: {dir(mcp)}")
print(f"\nTool manager attributes: {dir(mcp._tool_manager)}")