#!/usr/bin/env python3
"""
MCP Server for Resource Discovery V2
Binary Decision Support: Do we have this capability? YES/NO
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the path
root_path = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(root_path))

from fastmcp import FastMCP  # noqa: E402

from opsvi_mcp.tools.resource_discovery_v2 import ResourceDiscoveryV2  # noqa: E402

# Initialize the MCP server
mcp = FastMCP("resource-discovery-v2")

# Initialize the resource discovery tool
discovery_tool = ResourceDiscoveryV2(root_path=str(root_path))


@mcp.tool()
def check_capability(functionality: str) -> Dict[str, Any]:
    """
    Check if a capability exists in the codebase.
    
    Purpose: Binary decision - do we have this or not?
    Returns: YES/NO with location if found.
    
    Args:
        functionality: What capability you're looking for (e.g., "JWT auth", "Redis cache")
    
    Returns:
        - capability_exists: true/false
        - confidence: 0.0-1.0 score
        - primary_package: package name if found
        - usage: import statement if found
        - recommendation: what to do next
    
    Examples:
        check_capability("JWT authentication")  # -> opsvi-auth exists
        check_capability("WebSocket support")   # -> not found, create new
    """
    return discovery_tool.check_capability(functionality)


@mcp.tool()
def quick_check(package_name: str) -> Dict[str, Any]:
    """
    Direct package existence check - fastest method.
    
    Use when you know the exact package name.
    
    Args:
        package_name: Name of package (with or without "opsvi-" prefix)
    
    Returns:
        Same structure as check_capability but with 100% confidence if found.
    
    Examples:
        quick_check("auth")      # checks for opsvi-auth
        quick_check("opsvi-llm") # checks for opsvi-llm
    """
    return discovery_tool.quick_check(package_name)


@mcp.tool()
def list_categories() -> Dict[str, Any]:
    """
    Get a simple overview of available package categories.
    
    NOT for documentation - just to see what types of packages exist.
    
    Returns:
        Categories grouped by type (ai_ml, data, security, etc.)
        
    Use check_capability() for finding specific functionality.
    """
    return discovery_tool.list_categories()


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()