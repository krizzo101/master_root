#!/usr/bin/env python3
"""
Test script for claude-code MCP server with enhanced logging
"""

import asyncio
import json
import os
import sys

# Add the libs directory to the path
sys.path.insert(0, "/home/opsvi/master_root/libs")

from opsvi_mcp.servers.claude_code.parallel_logger import logger
from opsvi_mcp.servers.claude_code.server import mcp


async def test_logging():
    """Test the enhanced logging capabilities"""
    print("=" * 60)
    print("TESTING CLAUDE-CODE MCP SERVER WITH ENHANCED LOGGING")
    print("=" * 60)

    # Test 1: Simple synchronous execution
    print("\n[TEST 1] Simple synchronous task...")
    try:
        result = await mcp.tools["claude_run"].fn(
            task="Write a simple hello world Python function",
            outputFormat="json",
            permissionMode="bypassPermissions",
            verbose=True,
        )
        print(f"✓ Test 1 passed: Got result with length {len(result)}")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")

    # Test 2: Async execution with status checking
    print("\n[TEST 2] Async task with status checking...")
    try:
        # Start async job
        job_response = await mcp.tools["claude_run_async"].fn(
            task="Calculate factorial of 5 in Python",
            outputFormat="json",
            permissionMode="bypassPermissions",
        )
        job_data = json.loads(job_response)
        job_id = job_data["jobId"]
        print(f"  Job started with ID: {job_id}")

        # Check status
        await asyncio.sleep(1)
        status_response = await mcp.tools["claude_status"].fn(jobId=job_id)
        status_data = json.loads(status_response)
        print(f"  Job status: {status_data['status']}")

        # Wait for completion
        max_wait = 10
        for i in range(max_wait):
            status_response = await mcp.tools["claude_status"].fn(jobId=job_id)
            status_data = json.loads(status_response)
            if status_data["status"] != "running":
                break
            await asyncio.sleep(1)

        # Get result
        if status_data["status"] == "completed":
            result = await mcp.tools["claude_result"].fn(jobId=job_id)
            print("✓ Test 2 passed: Job completed successfully")
        else:
            print(f"✗ Test 2 failed: Job status is {status_data['status']}")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")

    # Test 3: Error handling
    print("\n[TEST 3] Error handling and logging...")
    try:
        result = await mcp.tools["claude_run"].fn(
            task="This should trigger an error: /nonexistent/path",
            cwd="/nonexistent/directory",
            outputFormat="json",
        )
        print("✗ Test 3 unexpected: Should have failed but didn't")
    except Exception as e:
        print(f"✓ Test 3 passed: Error properly logged and raised: {str(e)[:100]}...")

    # Test 4: List jobs
    print("\n[TEST 4] List all jobs...")
    try:
        jobs_response = await mcp.tools["claude_list_jobs"].fn()
        jobs_data = json.loads(jobs_response)
        print(f"✓ Test 4 passed: Found {len(jobs_data)} jobs")
        for job in jobs_data[:3]:  # Show first 3 jobs
            print(f"  - Job {job['jobId']}: {job['status']}")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}")

    # Test 5: Dashboard metrics
    print("\n[TEST 5] Dashboard metrics...")
    try:
        dashboard_response = await mcp.tools["claude_dashboard"].fn()
        dashboard_data = json.loads(dashboard_response)
        print("✓ Test 5 passed: Dashboard data retrieved")
        print(f"  - Active jobs: {dashboard_data['activeJobs']}")
        print(f"  - Completed jobs: {dashboard_data['completedJobs']}")
        print(f"  - Failed jobs: {dashboard_data['failedJobs']}")
    except Exception as e:
        print(f"✗ Test 5 failed: {e}")

    print("\n" + "=" * 60)
    print("LOGGING TEST COMPLETE")
    print(f"Log file location: {logger.log_file}")
    print("=" * 60)

    # Show sample log entries
    if logger.log_file.exists():
        print("\n[SAMPLE LOG ENTRIES]")
        with open(logger.log_file) as f:
            lines = f.readlines()
            # Show last 10 log entries
            for line in lines[-10:]:
                try:
                    log_entry = json.loads(line)
                    print(f"  [{log_entry['level']}] {log_entry['message'][:50]}...")
                except:
                    pass


if __name__ == "__main__":
    # Set environment for testing
    os.environ["CLAUDE_LOG_LEVEL"] = "DEBUG"
    os.environ["CLAUDE_PERF_LOGGING"] = "true"
    os.environ["CLAUDE_CHILD_LOGGING"] = "true"
    os.environ["CLAUDE_RECURSION_LOGGING"] = "true"

    # Run tests
    asyncio.run(test_logging())
