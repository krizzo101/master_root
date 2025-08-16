#!/usr/bin/env python3
"""
Test Script for Smart Decomposition Agent

Validates that the meta-intelligence system works with operational MCP tools.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add project root for imports
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))


async def test_smart_decomposition():
    """Test Smart Decomposition Agent with a simple request"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🧠 Testing Smart Decomposition Meta-Intelligence Agent")
    print("=" * 60)

    try:
        # Import and create agent
        from smart_decomposition_agent import SmartDecompositionAgent

        print("✅ Agent imported successfully")

        agent = SmartDecompositionAgent()
        print("✅ Agent initialized successfully")
        print(f"✅ MCP tools available: {len(agent.available_tools)}")
        print(f"   Tools: {agent.available_tools}")

        # Test request
        test_request = (
            "Research Python web frameworks and recommend the best one for a small team"
        )
        print(f"\n🎯 Test Request: {test_request}")

        # Process request
        print("\n⚙️ Processing request...")
        result = await agent.process_request(test_request)

        # Display results
        print("\n📊 RESULTS:")
        print("=" * 40)

        if result["success"]:
            print("✅ SUCCESS")
            solution = result["solution"]
            print(f"\n📋 Artifact Type: {solution.get('artifact_type', 'Unknown')}")
            print("\n📄 Solution Preview:")
            content = solution.get("content", "No content")
            print(content[:500] + "..." if len(content) > 500 else content)

            # Show complexity analysis
            if result.get("complexity_analysis"):
                analysis = result["complexity_analysis"]
                print("\n🔍 Complexity Analysis:")
                print(f"   Score: {analysis.get('complexity_score', 'N/A')}")
                print(f"   Strategy: {analysis.get('execution_strategy', 'N/A')}")
                print(f"   Agents: {analysis.get('recommended_agents', [])}")

            # Show agent contributions
            if result.get("agent_outputs"):
                print("\n🤖 Agent Contributions:")
                for role, output in result["agent_outputs"].items():
                    status = "✅" if output.get("success") else "❌"
                    print(f"   {status} {role}")
        else:
            print("❌ FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get("errors"):
                print("Additional errors:")
                for error in result["errors"]:
                    print(f"  - {error}")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()


async def test_mcp_tools_directly():
    """Test MCP tools directly to ensure they're working"""
    print("\n🔧 Testing MCP Tools Directly")
    print("=" * 40)

    try:
        from src.tools.mcp_tool_registry import (
            create_mcp_tool_registry,
        )

        registry = create_mcp_tool_registry()
        print(f"✅ Registry created with {len(registry.registered_tools)} tools")

        # Test a simple tool execution
        print("\n🧪 Testing tool execution...")

        # Note: In a real test, we would execute tools, but that requires API keys
        # For now, just validate the tools are registered
        for tool_name in registry.registered_tools.keys():
            print(f"   ✅ {tool_name} - registered")

        print("✅ MCP tools validation complete")

    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function"""
    print("🚀 Smart Decomposition Agent Test Suite")
    print("=" * 60)

    # Test MCP tools first
    await test_mcp_tools_directly()

    # Test Smart Decomposition Agent
    await test_smart_decomposition()

    print("\n🎉 Test suite complete!")


if __name__ == "__main__":
    asyncio.run(main())
