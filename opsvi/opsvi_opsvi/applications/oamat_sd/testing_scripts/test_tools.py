#!/usr/bin/env python3
"""
Test script to verify file system tools are working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.applications.oamat_sd.src.tools.file_system_tools import (
    create_file_system_tools,
)
from src.applications.oamat_sd.src.utils.project_context import ProjectContextManager


async def test_file_system_tools():
    """Test that file system tools work correctly."""

    # Set up project context
    test_project_name = "test_project"
    test_project_path = Path("/tmp/test_project")
    test_project_path.mkdir(exist_ok=True)

    ProjectContextManager.set_context(test_project_name, str(test_project_path))

    # Create file system tools
    tools = create_file_system_tools()

    print(f"Created {len(tools)} file system tools")
    for tool in tools:
        print(f"Tool: {tool.name} - {tool.description}")

    # Test write_file tool
    write_file_tool = None
    for tool in tools:
        if tool.name == "write_file":
            write_file_tool = tool
            break

    if write_file_tool:
        print("\nTesting write_file tool...")

        # Create test state
        test_state = {
            "project_path": str(test_project_path),
            "context": {},
            "agent_context": {"role": "test_agent"},
        }

        # Test writing a file
        result = write_file_tool.invoke(
            {"file_path": "test.txt", "content": "Hello, World!", "state": test_state}
        )

        print(f"Write result: {result}")

        # Check if file was created
        test_file = test_project_path / "test.txt"
        if test_file.exists():
            print(f"✅ File created successfully: {test_file}")
            with open(test_file) as f:
                content = f.read()
            print(f"File content: {content}")
        else:
            print(f"❌ File was not created: {test_file}")
    else:
        print("❌ write_file tool not found")

    # Clean up
    import shutil

    shutil.rmtree(test_project_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_file_system_tools())
