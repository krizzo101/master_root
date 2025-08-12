#!/usr/bin/env python3
"""
Test script to check if ArXiv MCP tools are available and working.
"""

import asyncio
import json


async def test_arxiv_mcp():
    """Test if ArXiv MCP tools are available and working."""
    print("Testing ArXiv MCP tools...")

    # Test 1: Check if MCP tools are available in the environment
    print("\n1. Checking for MCP tools in environment...")

    # List all available modules and functions
    import builtins

    for name in dir(builtins):
        if "mcp" in name.lower() and "research" in name.lower():
            mcp_functions.append(name)

    print(f"Found MCP functions in builtins: {mcp_functions}")

    # Test 2: Try to call the MCP tool directly
    print("\n2. Trying to call MCP tool directly...")

    try:
        # Try to get the MCP tool function from the environment
        if "mcp_research_papers_search_papers" in globals():
            print("Found mcp_research_papers_search_papers in globals")

            # Call the tool
            print(f"Result: {json.dumps(result, indent=2)}")

        else:
            print("mcp_research_papers_search_papers not found in globals")

    except Exception as e:
        print(f"Error calling MCP tool: {e}")

    # Test 3: Check if we can import the MCP tools
    print("\n3. Trying to import MCP tools...")

    try:
        import mcp_research_papers_search_papers

        print("Successfully imported mcp_research_papers_search_papers")

        # Call the tool
        )
        print(f"Result: {json.dumps(result, indent=2)}")

    except ImportError as e:
        print(f"ImportError: {e}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Check if MCP tools are available as functions
    print("\n4. Checking available functions...")

    # List all functions in the current namespace
    try:
        print(f"MCP functions in current namespace: {mcp_functions}")
    except Exception as e:
        print(f"Error checking functions: {e}")


if __name__ == "__main__":
    asyncio.run(test_arxiv_mcp())
