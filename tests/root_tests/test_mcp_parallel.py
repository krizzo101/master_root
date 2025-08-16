#!/usr/bin/env python3
"""
Test script for Claude MCP server parallel spawning capability.
This is our bootstrap tool - we need this working to fix everything else efficiently.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs/opsvi-mcp'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs/opsvi-orch'))

async def test_parallel_spawning():
    """Test if we can spawn multiple Claude instances in parallel."""
    
    print("=" * 80)
    print("CLAUDE MCP SERVER PARALLEL SPAWNING TEST")
    print("=" * 80)
    
    try:
        # Import the job manager
        from opsvi_orch.managers.job_manager import JobManager, JobConfig
        from opsvi_orch.executors.claude_executor import ClaudeBatchExecutor, ClaudeJobExecutor
        
        print("\n1. Initializing job manager and executors...")
        
        # Initialize components
        job_config = JobConfig(
            max_concurrent=5,
            enable_recursion=False,  # Start simple
            enable_checkpointing=False
        )
        
        job_manager = JobManager(config=job_config)
        claude_executor = ClaudeJobExecutor()
        batch_executor = ClaudeBatchExecutor(
            job_executor=claude_executor,
            max_concurrent=5
        )
        
        print("   ✓ Components initialized")
        
        # Define test tasks - simple enough to complete quickly
        test_tasks = [
            "Write a Python function that returns 'Hello from Instance 1'",
            "Write a Python function that returns 'Hello from Instance 2'",
            "Write a Python function that returns 'Hello from Instance 3'",
            "Create a JSON object with keys: name, version, status",
            "Write a markdown list with 3 items about parallel processing"
        ]
        
        print(f"\n2. Preparing {len(test_tasks)} test tasks...")
        for i, task in enumerate(test_tasks, 1):
            print(f"   Task {i}: {task[:50]}...")
        
        print("\n3. Executing tasks in parallel...")
        start_time = datetime.now()
        
        # Execute batch
        result = await batch_executor.execute_batch(
            tasks=test_tasks,
            parent_job_id=None,
            cwd=os.getcwd(),
            output_format="json"
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"\n4. Execution completed in {execution_time:.2f} seconds")
        print(f"   Total tasks: {result['total_tasks']}")
        print(f"   Successful: {result['successful']}")
        print(f"   Failed: {result['failed']}")
        
        if result['successful'] > 0:
            print("\n5. Sample results:")
            for i, r in enumerate(result['results'][:3], 1):
                print(f"   Result {i}: {str(r)[:100]}...")
        
        if result['failed'] > 0:
            print("\n6. Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        
        # Calculate parallelism efficiency
        if result['successful'] > 1:
            avg_time_per_task = result['metrics']['average_time_ms'] / 1000
            theoretical_serial_time = avg_time_per_task * result['total_tasks']
            parallelism_efficiency = (theoretical_serial_time / execution_time) * 100
            print(f"\n7. Parallelism Efficiency: {parallelism_efficiency:.1f}%")
            print(f"   (100% = perfect parallelism, <100% = overhead)")
        
        # Determine if test passed
        success = result['successful'] >= 3  # At least 3 tasks should succeed
        
        print("\n" + "=" * 80)
        if success:
            print("✅ TEST PASSED: Parallel spawning is working!")
            print("We can now use this to refactor the codebase efficiently.")
        else:
            print("❌ TEST FAILED: Parallel spawning needs fixing.")
            print("Fix this first before proceeding with refactoring.")
        print("=" * 80)
        
        return success
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure the MCP server and orchestration packages are properly installed.")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_server_direct():
    """Alternative test using MCP server tools directly."""
    
    print("\n" + "=" * 80)
    print("TESTING MCP SERVER TOOLS DIRECTLY")
    print("=" * 80)
    
    try:
        # This would test the actual MCP tools
        from opsvi_mcp.servers.claude_code.server import create_mcp_tools
        
        print("\n1. Loading MCP tools...")
        tools = create_mcp_tools()
        
        if 'claude_run_batch_async' in tools:
            print("   ✓ claude_run_batch_async tool found")
            
            # Test the tool
            batch_tool = tools['claude_run_batch_async']
            
            tasks = [
                "Return the string 'test1'",
                "Return the string 'test2'",
                "Return the string 'test3'"
            ]
            
            print(f"\n2. Testing batch execution with {len(tasks)} tasks...")
            result = await batch_tool(
                tasks=tasks,
                outputFormat="json",
                permissionMode="bypassPermissions"
            )
            
            print(f"\n3. Result: {result}")
            
            return True
        else:
            print("   ❌ claude_run_batch_async tool not found")
            return False
            
    except Exception as e:
        print(f"\n❌ MCP Server Test Failed: {e}")
        return False


def main():
    """Run all tests."""
    
    print("\nCLAUDE MCP PARALLEL SPAWNING TEST SUITE")
    print("This test verifies we can spawn multiple Claude instances in parallel.")
    print("This capability is essential for efficiently refactoring the codebase.")
    
    # Check environment
    print("\nEnvironment Check:")
    claude_token = os.environ.get("CLAUDE_CODE_TOKEN")
    if claude_token:
        print(f"  ✓ CLAUDE_CODE_TOKEN is set ({len(claude_token)} chars)")
    else:
        print("  ❌ CLAUDE_CODE_TOKEN is not set")
        print("     Set it with: export CLAUDE_CODE_TOKEN=your_token")
    
    # Check if Claude CLI is available
    import subprocess
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Claude CLI is available: {result.stdout.strip()}")
        else:
            print("  ❌ Claude CLI returned error")
    except FileNotFoundError:
        print("  ❌ Claude CLI not found in PATH")
        print("     Install with: npm install -g @anthropic-ai/claude-cli")
    
    # Run tests
    print("\nRunning tests...")
    
    # Test 1: Orchestration library parallel spawning
    test1_result = asyncio.run(test_parallel_spawning())
    
    # Test 2: MCP server direct (optional)
    # test2_result = asyncio.run(test_mcp_server_direct())
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if test1_result:
        print("\n✅ SUCCESS: Parallel Claude spawning is working!")
        print("\nNext Steps:")
        print("1. Use this capability to spawn multiple Claude instances")
        print("2. Assign refactoring tasks to each instance")
        print("3. Collect and integrate results")
        print("\nExample command to refactor in parallel:")
        print("  tasks = [")
        print("    'Extract Claude code from opsvi-orch to new opsvi-claude package',")
        print("    'Clean up boilerplate in opsvi-comm package',")
        print("    'Create abstract interfaces in opsvi-foundation',")
        print("    # ... more tasks")
        print("  ]")
        print("  results = await batch_executor.execute_batch(tasks)")
    else:
        print("\n❌ FAILURE: Parallel spawning is not working yet.")
        print("\nDebugging Steps:")
        print("1. Check if Claude CLI is installed and in PATH")
        print("2. Verify CLAUDE_CODE_TOKEN is set correctly")
        print("3. Test a single Claude spawn first")
        print("4. Check logs for specific error messages")
        print("5. Verify the Send API implementation is correct")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()