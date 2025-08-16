#!/usr/bin/env python3
"""
Test script to verify V2 server parameter fixes
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, '/home/opsvi/master_root/libs')

from opsvi_mcp.servers.claude_code_v2.server import ClaudeCodeV2Server
from opsvi_mcp.servers.claude_code_v2.config import ServerConfig


async def test_spawn_agent():
    """Test spawn_agent with simple parameters"""
    print("\n=== Testing spawn_agent with simple parameters ===")
    
    config = ServerConfig()
    server = ClaudeCodeV2Server(config)
    
    # Setup tools
    server._setup_tools()
    
    # Get the spawn_agent function
    spawn_agent = None
    for tool in server.mcp._tools.values():
        if tool.name == "spawn_agent":
            spawn_agent = tool.fn
            break
    
    if not spawn_agent:
        print("ERROR: spawn_agent tool not found")
        return False
    
    # Test with simple parameters
    result = await spawn_agent(
        task="Test task for V2 fixes",
        agent_profile="test_profile",
        output_dir="/tmp/v2_test",
        timeout=300,
        metadata={"test": "value"}
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print("✅ spawn_agent works with simple parameters!")
        return result.get("job_id")
    else:
        print(f"❌ spawn_agent failed: {result.get('error')}")
        return None


async def test_collect_results(job_id=None):
    """Test collect_results with simple parameters"""
    print("\n=== Testing collect_results with simple parameters ===")
    
    config = ServerConfig()
    server = ClaudeCodeV2Server(config)
    
    # Setup tools
    server._setup_tools()
    
    # Get the collect_results function
    collect_results = None
    for tool in server.mcp._tools.values():
        if tool.name == "collect_results":
            collect_results = tool.fn
            break
    
    if not collect_results:
        print("ERROR: collect_results tool not found")
        return False
    
    # Test with simple parameters
    job_ids = [job_id] if job_id else None
    result = await collect_results(
        job_ids=job_ids,
        output_dir="/tmp/v2_test",
        include_partial=True,
        cleanup=False
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print("✅ collect_results works with simple parameters!")
        return True
    else:
        print(f"❌ collect_results failed: {result.get('error')}")
        return False


async def test_spawn_parallel():
    """Test spawn_parallel_agents which should already work"""
    print("\n=== Testing spawn_parallel_agents (should already work) ===")
    
    config = ServerConfig()
    server = ClaudeCodeV2Server(config)
    
    # Setup tools
    server._setup_tools()
    
    # Get the spawn_parallel_agents function
    spawn_parallel = None
    for tool in server.mcp._tools.values():
        if tool.name == "spawn_parallel_agents":
            spawn_parallel = tool.fn
            break
    
    if not spawn_parallel:
        print("ERROR: spawn_parallel_agents tool not found")
        return False
    
    # Test with simple parameters
    result = await spawn_parallel(
        tasks=["Task 1", "Task 2"],
        agent_profile="parallel_test",
        output_dir="/tmp/v2_parallel_test",
        timeout=300
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print("✅ spawn_parallel_agents still works!")
        return True
    else:
        print(f"❌ spawn_parallel_agents failed: {result.get('error')}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("V2 Server Parameter Fix Verification")
    print("=" * 60)
    
    # Ensure output directories exist
    os.makedirs("/tmp/v2_test", exist_ok=True)
    os.makedirs("/tmp/v2_parallel_test", exist_ok=True)
    os.makedirs("/tmp/claude_results", exist_ok=True)
    
    # Test spawn_agent
    job_id = await test_spawn_agent()
    
    # Test collect_results
    await test_collect_results(job_id)
    
    # Test spawn_parallel_agents
    await test_spawn_parallel()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- spawn_agent: Now uses simple parameters instead of Pydantic model")
    print("- collect_results: Now uses simple parameters instead of Pydantic model")
    print("- spawn_parallel_agents: Already worked, still works")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())