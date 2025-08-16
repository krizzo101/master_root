#!/usr/bin/env python3
"""
Test script to verify that agents can use file system tools correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain.agents import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.tools.file_system_tools import (
    create_file_system_tools,
)
from src.applications.oamat_sd.src.utils.project_context import ProjectContextManager


async def test_agent_with_tools():
    """Test that an agent can use file system tools correctly."""

    # Set up project context
    test_project_name = "test_agent_project"
    test_project_path = Path("/tmp/test_agent_project")
    test_project_path.mkdir(exist_ok=True)

    ProjectContextManager.set_context(test_project_name, str(test_project_path))

    # Create file system tools
    tools = create_file_system_tools()

    print(f"Created {len(tools)} file system tools")
    for tool in tools:
        print(f"Tool: {tool.name}")

    # Create a simple agent
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a test agent. Your task is to create a simple Python file.\n\n"
                "**MANDATORY: You MUST use the write_file tool to create a file.**\n\n"
                "**CRITICAL: Use the write_file tool to create the file. Do not just describe what you would do.**\n\n"
                "Available tools: {tools}\n"
                "Tool names: {tool_names}",
            ),
            (
                "human",
                'Create a Python file called "hello.py" with a simple "Hello, World!" program.\n\n'
                'Example:\nwrite_file("hello.py", "print(\'Hello, World!\')")\n\n'
                "Now create the file using the write_file tool.\n\n"
                "{input}\n\n{agent_scratchpad}",
            ),
        ]
    )

    agent = create_react_agent(llm=model, tools=tools, prompt=prompt)

    print("\nTesting agent with tools...")

    # Test the agent
    result = await agent.ainvoke(
        {"input": "Create a hello.py file with a simple Hello World program"}
    )

    print(f"Agent result: {result}")

    # Check if file was created
    test_file = test_project_path / "hello.py"
    if test_file.exists():
        print(f"✅ File created successfully: {test_file}")
        with open(test_file) as f:
            content = f.read()
        print(f"File content: {content}")
    else:
        print(f"❌ File was not created: {test_file}")

    # Clean up
    import shutil

    shutil.rmtree(test_project_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())
