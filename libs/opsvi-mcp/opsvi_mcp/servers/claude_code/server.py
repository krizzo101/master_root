"""
Claude Code MCP Server - Main server implementation
"""

import asyncio
import json
from typing import Optional

from fastmcp import FastMCP

from .config import config
from .job_manager import JobManager
from .parallel_logger import logger
from .parallel_enhancement import enhance_job_manager_with_parallel


# Initialize FastMCP server
mcp = FastMCP("claude-code-server")

# Initialize job manager globally
job_manager = JobManager()

# Log server initialization
logger.log(
    "INFO",
    "SERVER",
    "Claude Code MCP Server initialized",
    {
        "recursion_limits": {
            "max_depth": config.recursion.max_depth,
            "max_concurrent_at_depth": config.recursion.max_concurrent_at_depth,
            "max_total_jobs": config.recursion.max_total_jobs,
        }
    },
)


@mcp.tool()
async def claude_run(
    task: str,
    cwd: Optional[str] = None,
    outputFormat: str = "json",
    permissionMode: str = "bypassPermissions",
    verbose: bool = False,
    parentJobId: Optional[str] = None,
) -> str:
    """
    Run Claude Code task (headless) - synchronous execution

    Args:
        task: The task description for Claude Code
        cwd: Working directory for the task
        outputFormat: Output format (json or text)
        permissionMode: Permission mode (acceptEdits, bypassPermissions, default, plan)
        verbose: Enable verbose output
        parentJobId: Parent job ID for recursion tracking

    Returns:
        The result of the Claude Code execution
    """
    logger.log_debug(
        "API",
        "claude_run called",
        {
            "task_preview": task[:100] if task else None,
            "cwd": cwd,
            "outputFormat": outputFormat,
            "permissionMode": permissionMode,
            "verbose": verbose,
            "parentJobId": parentJobId,
        },
    )

    try:
        # Create job
        job = job_manager.create_job(
            task=task,
            cwd=cwd,
            output_format=outputFormat,
            permission_mode=permissionMode,
            verbose=verbose,
            parent_job_id=parentJobId,
        )

        # Execute synchronously
        logger.log_debug(job.id, "Executing job synchronously")
        await job_manager.execute_job_async(job)

        # Get result
        logger.log_debug(job.id, "Fetching job result")
        result = job_manager.get_job_result(job.id)

        if result and "error" not in result:
            # Return the content as string
            content = result.get("content", [])
            logger.log_debug(
                job.id,
                "Job completed successfully",
                {"content_items": len(content), "result_size": len(json.dumps(result))},
            )
            if content and len(content) > 0:
                return content[0].get("text", json.dumps(result))
            return json.dumps(result)
        else:
            error_msg = (
                result.get("error", "Unknown error")
                if result
                else "Job execution failed"
            )
            logger.log_error(job.id, "Job execution failed", data={"error": error_msg})
            raise Exception(error_msg)

    except Exception as e:
        logger.log_error("API", "claude_run failed", e)
        raise Exception(f"Execution error: {str(e)}")


@mcp.tool()
async def claude_run_async(
    task: str,
    cwd: Optional[str] = None,
    outputFormat: str = "json",
    permissionMode: str = "bypassPermissions",
    verbose: bool = False,
    parentJobId: Optional[str] = None,
) -> str:
    """
    Run Claude Code task asynchronously - returns job ID immediately for parallel execution

    Args:
        task: The task description for Claude Code
        cwd: Working directory for the task
        outputFormat: Output format (json or text)
        permissionMode: Permission mode (acceptEdits, bypassPermissions, default, plan)
        verbose: Enable verbose output
        parentJobId: Parent job ID for recursion tracking

    Returns:
        JSON with job ID and status
    """
    logger.log_debug(
        "API",
        "claude_run_async called",
        {
            "task_preview": task[:100] if task else None,
            "cwd": cwd,
            "outputFormat": outputFormat,
            "permissionMode": permissionMode,
            "verbose": verbose,
            "parentJobId": parentJobId,
        },
    )

    try:
        # Create job
        job = job_manager.create_job(
            task=task,
            cwd=cwd,
            output_format=outputFormat,
            permission_mode=permissionMode,
            verbose=verbose,
            parent_job_id=parentJobId,
        )

        # Start execution asynchronously
        logger.log_debug(job.id, "Creating async task for job execution")
        task_obj = asyncio.create_task(job_manager.execute_job_async(job))
        logger.log_trace(
            job.id, "Async task created", {"task_name": task_obj.get_name()}
        )

        # Return job ID immediately
        response = {
            "jobId": job.id,
            "status": "started",
            "message": "Job started successfully",
        }
        logger.log_debug(job.id, "Returning job ID to client", response)
        return json.dumps(response, indent=2)

    except Exception as e:
        logger.log_error("API", "claude_run_async failed", e)
        raise Exception(f"Execution error: {str(e)}")


@mcp.tool()
async def claude_status(jobId: str) -> str:
    """
    Check the status of an asynchronous Claude Code job

    Args:
        jobId: The job ID returned by claude_run_async

    Returns:
        JSON with job status information
    """
    logger.log_trace("API", f"claude_status called for job {jobId}")
    status = job_manager.get_job_status(jobId)

    if status:
        return json.dumps(status, indent=2)
    else:
        raise Exception(f"Job {jobId} not found")


@mcp.tool()
async def claude_result(jobId: str) -> str:
    """
    Get the result of a completed Claude Code job

    Args:
        jobId: The job ID returned by claude_run_async

    Returns:
        The result of the completed job
    """
    logger.log_debug("API", f"claude_result called for job {jobId}")
    result = job_manager.get_job_result(jobId)

    if result:
        if "error" in result:
            raise Exception(f"Job error: {result['error']}")
        else:
            # Return the content as string
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", json.dumps(result))
            return json.dumps(result)
    else:
        raise Exception(f"Job {jobId} not found")


@mcp.tool()
async def claude_list_jobs() -> str:
    """
    List all active and recent jobs

    Returns:
        JSON array of all jobs with their status
    """
    jobs = job_manager.list_jobs()
    return json.dumps(jobs, indent=2)


@mcp.tool()
async def claude_kill_job(jobId: str) -> str:
    """
    Terminate a running job

    Args:
        jobId: The job ID to terminate

    Returns:
        JSON with success status
    """
    success = job_manager.kill_job(jobId)

    return json.dumps(
        {
            "success": success,
            "message": f"Job {jobId} {'killed' if success else 'not found or already completed'}",
        },
        indent=2,
    )


@mcp.tool()
async def claude_dashboard() -> str:
    """
    Get real-time system performance dashboard

    Returns:
        JSON with dashboard metrics and statistics
    """
    dashboard = job_manager.get_dashboard_data()

    dashboard_dict = {
        "activeJobs": dashboard.active_jobs,
        "completedJobs": dashboard.completed_jobs,
        "failedJobs": dashboard.failed_jobs,
        "averageDuration": dashboard.average_duration,
        "parallelEfficiency": dashboard.parallel_efficiency,
        "nestedDepth": dashboard.nested_depth,
        "systemLoad": dashboard.system_load,
        "recursionStats": dashboard.recursion_stats,
    }

    return json.dumps(dashboard_dict, indent=2)


@mcp.tool()
async def claude_recursion_stats() -> str:
    """
    Get recursion limits and statistics

    Returns:
        JSON with recursion configuration and current stats
    """
    stats = job_manager.recursion_manager.get_recursion_stats()
    return json.dumps(stats, indent=2)


@mcp.tool()
async def claude_run_batch(
    tasks: list,
    parent_job_id: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """
    Execute multiple Claude Code tasks in parallel

    Args:
        tasks: List of task configurations, each containing:
            - task: The task description (required)
            - cwd: Working directory (optional)
            - output_format: Output format (optional, default: "json")
            - permission_mode: Permission mode (optional, default: "bypassPermissions")
            - verbose: Enable verbose output (optional, default: false)
        parent_job_id: Parent job ID for recursion tracking (optional)
        max_concurrent: Maximum concurrent executions (optional, uses config default)

    Returns:
        JSON with batch execution information including:
        - batch_id: Unique batch identifier
        - job_ids: List of individual job IDs
        - execution_time_ms: Total execution time
        - results_summary: Summary of successful/failed jobs

    Example:
        tasks = [
            {"task": "Analyze security in auth.py", "cwd": "/project"},
            {"task": "Check performance in db.py", "cwd": "/project"},
            {"task": "Review code style in api.py", "cwd": "/project"}
        ]
        result = await claude_run_batch(tasks=tasks, max_concurrent=3)
    """
    logger.log(
        "API",
        "BATCH",
        f"claude_run_batch called with {len(tasks)} tasks",
        {
            "parent_job_id": parent_job_id,
            "max_concurrent": max_concurrent,
            "tasks_preview": [t.get("task", "")[:50] for t in tasks[:3]],
        },
    )

    try:
        # Execute batch in parallel
        result = await job_manager.execute_parallel_batch(
            tasks=tasks, parent_job_id=parent_job_id, max_concurrent=max_concurrent
        )

        logger.log("API", "BATCH", f"Batch execution completed", result)

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.log_error("API", "claude_run_batch failed", e)
        raise Exception(f"Batch execution error: {str(e)}")


@mcp.tool()
async def claude_batch_status(batch_id: str) -> str:
    """
    Get the status of a batch execution

    Args:
        batch_id: The batch ID returned by claude_run_batch

    Returns:
        JSON with batch status information
    """
    status = job_manager.get_batch_status(batch_id)

    if status:
        return json.dumps(status, indent=2)
    else:
        raise Exception(f"Batch {batch_id} not found")


@mcp.tool()
async def claude_list_batches() -> str:
    """
    List all batch executions

    Returns:
        JSON with information about all batch executions
    """
    batches = job_manager.get_all_batches()
    return json.dumps(batches, indent=2)


def main():
    """Main entry point for the MCP server"""
    import uvloop

    uvloop.install()
    mcp.run()


if __name__ == "__main__":
    main()
