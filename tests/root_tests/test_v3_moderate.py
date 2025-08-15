#!/usr/bin/env python3
"""
Moderate complexity test for V3 - Should decompose but execute quickly
"""

import os
import sys
import json
import asyncio
from datetime import datetime

sys.path.insert(0, '/home/opsvi/master_root/libs')

from opsvi_mcp.servers.claude_code_v3.server import claude_run_v3

async def test_moderate_complexity():
    """Test with a task that's complex enough to decompose but quick to execute"""
    
    print("V3 MODERATE COMPLEXITY TEST")
    print("=" * 60)
    
    # Task that should trigger decomposition (has "create", "implement", "server")
    # but is simple enough to execute quickly
    moderate_task = """Create a simple Python server with two functions:
    1. A hello function that returns a greeting
    2. A goodbye function that returns a farewell
    Just the functions, no actual server needed."""
    
    print(f"Task: {moderate_task}")
    print("\nExecuting with V3...")
    print("(Checking if this triggers decomposition...)\n")
    
    start_time = datetime.now()
    
    try:
        result = await claude_run_v3(
            task=moderate_task,
            mode="CODE",  # Standard code mode
            auto_detect=False,
            quality_level="normal"
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print("RESULTS:")
        print("-" * 40)
        print(f"Execution Time: {execution_time:.2f} seconds")
        print(f"Status: {result.get('status')}")
        print(f"Success: {result.get('success')}")
        print(f"Complexity: {result.get('complexity')}")
        
        # The key indicator: did it decompose?
        if 'subtasks_executed' in result:
            print(f"\n🎯 DECOMPOSITION OCCURRED!")
            print(f"   Subtasks Executed: {result['subtasks_executed']}")
            print(f"   Total Subtasks: {result['subtasks_total']}")
            print(f"   Total Cost: ${result.get('total_cost', 0):.4f}")
            
            if result.get('results'):
                print(f"\n   Individual Executions:")
                for i, r in enumerate(result['results'], 1):
                    print(f"   {i}. {r.get('status')} - Cost: ${r.get('cost', 0):.4f}")
            
            print(f"\n✅ V3 spawned {result['subtasks_executed']} Claude instances!")
            
        else:
            print(f"\n❌ No decomposition - Single execution")
            print(f"   Cost: ${result.get('cost', 0):.4f}")
        
        # Save for inspection
        with open("/tmp/v3_moderate_result.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print(f"CLAUDE_CODE_TOKEN: {'SET' if os.environ.get('CLAUDE_CODE_TOKEN') else 'NOT SET'}\n")
    asyncio.run(test_moderate_complexity())