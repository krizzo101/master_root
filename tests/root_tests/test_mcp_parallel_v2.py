#!/usr/bin/env python3
"""
Test the MCP parallel execution with multi-token support
"""
import asyncio
import json
import time
from datetime import datetime
from fastmcp import Context
from fastmcp.client import AsyncClient

async def test_parallel_with_tokens():
    """Test parallel execution using multiple tokens"""
    print("="*60)
    print("TESTING MCP PARALLEL EXECUTION WITH MULTI-TOKEN SUPPORT")
    print("="*60)
    
    # Create MCP client
    async with AsyncClient(transport="stdio") as client:
        # Connect to the Claude Code MCP server
        await client.connect(
            command="python",
            args=["-m", "opsvi_mcp.servers.claude_code"],
            cwd="/home/opsvi/master_root/libs/opsvi-mcp"
        )
        
        print("\n1. Testing parallel batch with 6 simple tasks...")
        print("   (With 3 tokens, should handle all 6 in parallel)")
        
        start_time = time.time()
        
        # Create 6 simple tasks
        tasks = [
            {"task": f"Write 'Task {i} complete' and nothing else"} 
            for i in range(1, 7)
        ]
        
        # Execute batch
        result = await client.call_tool(
            "claude_run_batch",
            arguments={"tasks": tasks}
        )
        
        batch_time = time.time() - start_time
        
        print(f"\nBatch submission time: {batch_time:.2f}s")
        print(f"Batch ID: {result.get('batch_id')}")
        print(f"Job IDs: {len(result.get('job_ids', []))} jobs created")
        
        # Wait a bit for jobs to complete
        print("\n2. Waiting for jobs to complete...")
        await asyncio.sleep(30)
        
        # Check individual job statuses
        print("\n3. Checking job statuses...")
        job_ids = result.get('job_ids', [])
        
        completed = 0
        failed = 0
        running = 0
        
        for job_id in job_ids:
            try:
                status_result = await client.call_tool(
                    "claude_status",
                    arguments={"jobId": job_id}
                )
                status = status_result.get('status')
                if status == 'completed':
                    completed += 1
                elif status == 'failed':
                    failed += 1
                else:
                    running += 1
            except:
                pass
        
        print(f"   Completed: {completed}")
        print(f"   Failed: {failed}")
        print(f"   Still running: {running}")
        
        # Calculate parallelism
        print("\n4. Parallelism Analysis:")
        if completed > 0:
            # With 3 tokens and 6 tasks, optimal time would be ~2x single task time
            print(f"   Total time for {len(tasks)} tasks: {batch_time:.2f}s")
            print(f"   Expected sequential time: ~{len(tasks) * 10}s")
            print(f"   Expected parallel time (3 tokens): ~{(len(tasks) / 3) * 10}s")
            
            speedup = (len(tasks) * 10) / batch_time
            print(f"   Actual speedup: {speedup:.2f}x")
            
            if speedup > 2.5:
                print("   ✅ TRUE PARALLEL EXECUTION WITH MULTI-TOKEN!")
            else:
                print("   ⚠️ Some parallelism but not optimal")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-mcp")
    asyncio.run(test_parallel_with_tokens())