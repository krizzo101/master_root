#!/usr/bin/env python3
"""
Test script to verify parallel spawning capability of Claude MCP server.
Current issue: It works recursively but NOT in parallel - we need to fix this.
"""

import asyncio
import time
import os
import sys

# Add libs to path
sys.path.insert(0, '/home/opsvi/master_root/libs')

async def test_parallel_execution():
    """Test if Claude instances actually run in parallel."""
    
    print("Testing Claude MCP Parallel Execution")
    print("=" * 60)
    
    # Import the MCP server module
    from opsvi_mcp.servers.claude_code_wrapper import (
        claude_run_batch_async,
        claude_results_batch
    )
    
    # Simple test tasks that should complete quickly
    tasks = [
        "echo 'Task 1 completed'",
        "echo 'Task 2 completed'", 
        "echo 'Task 3 completed'",
        "echo 'Task 4 completed'",
        "echo 'Task 5 completed'"
    ]
    
    print(f"Spawning {len(tasks)} tasks...")
    start = time.time()
    
    # This SHOULD spawn in parallel but currently doesn't
    result = await claude_run_batch_async(
        tasks=tasks,
        outputFormat="text",
        permissionMode="bypassPermissions"
    )
    
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f} seconds")
    
    # If truly parallel, should complete in ~time of one task
    # If serial, will take ~time of all tasks combined
    if elapsed < len(tasks) * 2:  # Assuming each task takes ~2 sec
        print("✅ Tasks appear to run in PARALLEL")
    else:
        print("❌ Tasks appear to run SERIALLY")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_parallel_execution())
    print(f"\nResult: {result}")