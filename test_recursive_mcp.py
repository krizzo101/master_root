#!/usr/bin/env python3
"""
Recursive Claude Code task using MCP tools.
This demonstrates spawning child Claude instances that can spawn their own children.
"""

import json
import sys
import os

# Set up environment for MCP
os.environ['PYTHONPATH'] = '/home/opsvi/master_root/libs'

# Import FastMCP for creating the MCP client
from fastmcp import FastMCP
from fastmcp.exceptions import *


async def run_recursive_analysis():
    """Run a multi-level recursive task."""
    
    # Initialize FastMCP client
    mcp = FastMCP("claude-code-recursive-demo")
    
    print("=" * 70)
    print("RECURSIVE CLAUDE CODE TASK DEMONSTRATION")
    print("=" * 70)
    
    # Level 1: Main task that spawns child tasks
    main_task = """
    This is a recursive task demonstration. Please:
    1. Report that you are the MAIN instance at recursion depth 0
    2. Use the mcp__claude-code-wrapper__claude_run tool to spawn a CHILD task with this instruction:
       'Report that you are CHILD instance at depth 1, then list 3 Python packages'
    3. Report the child's output
    4. Confirm task completion
    """
    
    print("\nMAIN TASK (Depth 0):")
    print(main_task)
    print("-" * 70)
    
    # Connect to the Claude Code wrapper MCP server
    async with mcp:
        # Call the claude_run tool
        result = await mcp.call_tool(
            "claude_run",
            task=main_task,
            cwd="/home/opsvi/master_root",
            outputFormat="text",
            permissionMode="bypassPermissions",
            verbose=False
        )
        
        print("\nRESULT FROM MAIN INSTANCE:")
        print("=" * 70)
        print(result)
    
    print("\n" + "=" * 70)
    print("✅ Recursive task demonstration complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_recursive_analysis())