#!/usr/bin/env python3
"""
Recursive Claude Code task to analyze Python environment.
This script spawns another Claude Code instance to list installed packages.
"""

import asyncio
import json
import sys

# Add the libs directory to Python path for MCP imports
sys.path.insert(0, "/home/opsvi/master_root/libs")

from opsvi_mcp.servers.claude_code.job_manager import JobManager
from opsvi_mcp.servers.claude_code.models import ClaudeCodeTask


async def main():
    """Main function to create and execute recursive task."""

    # Initialize the job manager
    job_manager = JobManager()

    # Define the recursive task for environment analysis
    recursive_task = """
    Analyze the current Python environment and provide a comprehensive report including:
    1. Python version and executable path
    2. List all installed packages with versions (using pip list)
    3. Check which key AI/ML packages are available (openai, anthropic, langchain, etc.)
    4. Report the current working directory and Python path
    5. Check if FastMCP is properly installed and accessible
    
    Format the output as a structured JSON report.
    """

    print("=" * 60)
    print("RECURSIVE CLAUDE CODE TASK: Python Environment Analysis")
    print("=" * 60)
    print("\nSpawning Claude Code instance to analyze environment...")
    print(f"\nTask: {recursive_task}")
    print("\n" + "-" * 60)

    # Create the task
    task = ClaudeCodeTask(
        task=recursive_task,
        cwd="/home/opsvi/master_root",
        output_format="json",
        permission_mode="bypassPermissions",
        verbose=True,
    )

    # Submit the job asynchronously
    job_id = await job_manager.submit_job(task)
    print(f"\nJob submitted with ID: {job_id}")
    print("Waiting for completion...")

    # Wait for the job to complete with status updates
    max_wait = 120  # Maximum 2 minutes
    check_interval = 2  # Check every 2 seconds
    elapsed = 0

    while elapsed < max_wait:
        status = await job_manager.get_status(job_id)

        if status["status"] == "completed":
            print("\n✅ Job completed successfully!")
            result = await job_manager.get_result(job_id)

            print("\n" + "=" * 60)
            print("ENVIRONMENT ANALYSIS RESULTS")
            print("=" * 60)

            # Try to parse and pretty print the result
            try:
                if isinstance(result, str):
                    result_data = json.loads(result)
                else:
                    result_data = result

                print(json.dumps(result_data, indent=2))
            except:
                # If not JSON, print as-is
                print(result)

            break

        elif status["status"] == "failed":
            print(f"\n❌ Job failed with error: {status.get('error', 'Unknown error')}")
            break

        elif status["status"] == "running":
            # Show progress indicator
            dots = "." * ((elapsed // 2) % 4)
            print(f"\r⏳ Job running{dots:<4} ({elapsed}s elapsed)", end="", flush=True)

        await asyncio.sleep(check_interval)
        elapsed += check_interval
    else:
        print(f"\n⚠️ Job timed out after {max_wait} seconds")
        print("Attempting to kill the job...")
        await job_manager.kill_job(job_id)

    # Show final dashboard stats
    print("\n" + "=" * 60)
    print("RECURSION STATISTICS")
    print("=" * 60)
    dashboard = await job_manager.get_dashboard()
    print(json.dumps(dashboard, indent=2))

    # Cleanup
    await job_manager.cleanup()
    print("\n✅ Task completed and cleaned up")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
