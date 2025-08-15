#!/usr/bin/env python3
"""
Test claude-code MCP server with timeout to diagnose hanging issues
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the libs directory to the path
sys.path.insert(0, "/home/opsvi/master_root/libs")

# Set up environment with DEBUG logging
os.environ["CLAUDE_LOG_LEVEL"] = "DEBUG"
os.environ["CLAUDE_PERF_LOGGING"] = "true"
os.environ["CLAUDE_CHILD_LOGGING"] = "true"
os.environ["CLAUDE_RECURSION_LOGGING"] = "true"
os.environ["PYTHONPATH"] = "/home/opsvi/master_root/libs"

from opsvi_mcp.servers.claude_code.server import job_manager


async def test_with_timeout():
    """Test the claude-code execution with various timeouts"""
    print("=" * 60)
    print("TESTING CLAUDE-CODE MCP WITH TIMEOUT")
    print("=" * 60)

    # Test 1: Very simple task with short timeout
    print("\n[TEST 1] Simple task with 5 second timeout...")
    try:
        job = job_manager.create_job(
            task="echo 'Hello World'",
            output_format="text",
            permission_mode="bypassPermissions",
            verbose=True,
        )
        print(f"  Created job: {job.id}")
        print(
            "  Command will be: claude --print --dangerously-skip-permissions --verbose \"echo 'Hello World'\""
        )

        # Execute with timeout
        try:
            await asyncio.wait_for(job_manager.execute_job_async(job), timeout=5.0)
            print("  ✓ Job completed within timeout")

            # Get result
            result = job_manager.get_job_result(job.id)
            if result:
                print(f"  Result: {json.dumps(result, indent=2)[:200]}...")

        except asyncio.TimeoutError:
            print("  ✗ Job timed out after 5 seconds")
            print(f"  Job status: {job.status.value if job else 'Unknown'}")

            # Check if process is running
            if hasattr(job, "process") and job.process:
                print(f"  Process PID: {job.process.pid}")
                print(f"  Process poll: {job.process.poll()}")

                # Try to kill the process
                job.process.kill()
                print("  Killed hanging process")

    except Exception as e:
        print(f"  ✗ Error creating job: {e}")

    # Test 2: Test with direct subprocess call
    print("\n[TEST 2] Direct subprocess test with timeout...")
    import subprocess

    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--verbose",
        "echo 'test'",
    ]
    print(f"  Command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )

        print(f"  Process started with PID: {process.pid}")

        # Wait with timeout
        try:
            stdout, stderr = process.communicate(timeout=5)
            print("  ✓ Process completed")
            print(f"  Return code: {process.returncode}")
            if stdout:
                print(f"  STDOUT: {stdout[:200]}...")
            if stderr:
                print(f"  STDERR: {stderr[:200]}...")
        except subprocess.TimeoutExpired:
            print("  ✗ Process timed out after 5 seconds")
            process.kill()
            stdout, stderr = process.communicate()
            print("  Killed process")
            if stdout:
                print(f"  Partial STDOUT: {stdout[:200]}...")
            if stderr:
                print(f"  Partial STDERR: {stderr[:200]}...")

    except Exception as e:
        print(f"  ✗ Error running subprocess: {e}")

    # Test 3: Check if claude CLI is accessible
    print("\n[TEST 3] Check claude CLI availability...")
    try:
        result = subprocess.run(
            ["which", "claude"], capture_output=True, text=True, timeout=2
        )
        print(f"  Claude location: {result.stdout.strip()}")

        # Check version
        result = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=2
        )
        print(f"  Claude version: {result.stdout.strip()}")

    except subprocess.TimeoutExpired:
        print("  ✗ Command timed out")
    except Exception as e:
        print(f"  ✗ Error checking claude: {e}")

    # Check log files
    print("\n[LOG CHECK]")
    log_dir = Path("/home/opsvi/master_root/logs/claude-code")
    if log_dir.exists():
        log_files = sorted(log_dir.glob("parallel-execution-*.log"))
        if log_files:
            latest_log = log_files[-1]
            print(f"  Latest log: {latest_log.name}")
            with open(latest_log) as f:
                lines = f.readlines()
                print("  Last 5 log entries:")
                for line in lines[-5:]:
                    try:
                        entry = json.loads(line)
                        print(f"    [{entry['level']}] {entry['message']}")
                    except:
                        pass

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Run with asyncio
    asyncio.run(test_with_timeout())
