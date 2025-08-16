"""
Job management for Claude Code parallel execution
"""

import asyncio
import json
import os
import subprocess
import shlex
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
import threading

from .config import config
from .models import ClaudeJob, JobStatus, DashboardData
from .parallel_logger import logger
from .recursion_manager import RecursionManager
from .performance_monitor import PerformanceMonitor


from .parallel_enhancement import enhance_job_manager_with_parallel


@enhance_job_manager_with_parallel
class JobManager:
    """Manages Claude Code job execution and lifecycle"""

    def __init__(self):
        self.active_jobs: Dict[str, ClaudeJob] = {}
        self.completed_jobs: Dict[str, ClaudeJob] = {}
        self.recursion_manager = RecursionManager()
        self.performance_monitor = PerformanceMonitor()
        self.job_lock = asyncio.Lock()
        self._sync_lock = threading.Lock()  # For sync operations only
        
        # Semaphores for concurrency control
        self._global_semaphore = asyncio.Semaphore(20)  # Max 20 total jobs
        self._depth_semaphores = {}
        for depth in range(10):  # Support up to depth 10
            self._depth_semaphores[depth] = asyncio.Semaphore(5)  # Max 5 per depth

        # Load authentication token
        self.load_auth_token()

    def load_auth_token(self) -> None:
        """Load Claude Code authentication token"""
        # Check if already in environment
        if os.environ.get("CLAUDE_CODE_TOKEN"):
            config.claude_code_token = os.environ["CLAUDE_CODE_TOKEN"]
            logger.log_debug("SYSTEM", "Using CLAUDE_CODE_TOKEN from environment")
            return

        # Try to load from .env file
        env_paths = [
            Path.cwd() / ".env",  # Current directory first
            Path.home() / ".env",  # Then home directory
        ]

        for env_path in env_paths:
            if env_path.exists():
                try:
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith("CLAUDE_CODE_TOKEN="):
                                token = line.split("=", 1)[1].strip()
                                os.environ["CLAUDE_CODE_TOKEN"] = token
                                config.claude_code_token = token
                                logger.log_debug(
                                    "SYSTEM",
                                    f"Loaded CLAUDE_CODE_TOKEN from {env_path}",
                                )
                                return
                except Exception as e:
                    logger.log_error(
                        "SYSTEM", f"Failed to load .env from {env_path}", e
                    )

        logger.log_debug(
            "SYSTEM", "No CLAUDE_CODE_TOKEN found - authentication may fail"
        )

    def create_job(
        self,
        task: str,
        cwd: Optional[str] = None,
        output_format: str = "json",
        permission_mode: str = "default",
        verbose: bool = False,
        parent_job_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ClaudeJob:
        """Create a new job"""
        job_id = str(uuid.uuid4())

        logger.log_debug(
            "SYSTEM",
            f"Creating job {job_id}",
            {"task_preview": task[:200], "cwd": cwd, "parent_job_id": parent_job_id},
        )

        # Create recursion context
        try:
            recursion_context = self.recursion_manager.create_recursion_context(
                job_id, parent_job_id, task
            )
        except ValueError as e:
            # Recursion limit exceeded
            raise e

        # Validate permission mode with security config
        validated_permission_mode = config.security.validate_permission_mode(permission_mode)
        
        job = ClaudeJob(
            id=job_id,
            task=task,
            cwd=cwd or os.getcwd(),
            output_format=output_format,
            permission_mode=validated_permission_mode,
            verbose=verbose,
            recursion_context=recursion_context,
            parent_job_id=parent_job_id,
            model=model,
        )

        # Create performance metrics
        self.performance_monitor.create_metrics(job_id)

        # Use sync lock for synchronous create_job method
        with self._sync_lock:
            self.active_jobs[job_id] = job
            logger.log_trace(
                job_id,
                "Job added to active jobs",
                {
                    "active_job_count": len(self.active_jobs),
                    "active_job_ids": list(self.active_jobs.keys()),
                },
            )

        logger.log(
            "INFO",
            job_id,
            "Job created",
            {
                "task": task[:100],
                "cwd": cwd,
                "permission_mode": permission_mode,
                "parent_job_id": parent_job_id,
                "recursion_depth": recursion_context.depth if recursion_context else 0,
            },
        )

        return job

    async def execute_job(self, job: ClaudeJob) -> None:
        """Execute a Claude Code job asynchronously"""
        logger.log_debug(
            job.id,
            "Starting job execution",
            {"job_status": job.status.value, "start_time": job.start_time.isoformat()},
        )

        # Analyze task to determine required MCP servers
        from opsvi_mcp.servers.claude_code_v2.mcp_manager import (
            MCPRequirementAnalyzer,
            MCPConfigManager,
        )

        required_servers = MCPRequirementAnalyzer.analyze_task(job.task)

        # Build command
        cmd = ["claude"]

        # Add model if specified
        if job.model:
            cmd.extend(["--model", job.model])
            logger.log_debug(job.id, f"Using model: {job.model}")

        # Add MCP configuration if needed
        if required_servers:
            # Create minimal MCP config for this job
            config_path = MCPConfigManager.create_instance_config(
                instance_id=job.id, custom_servers=list(required_servers)
            )
            job.mcp_config_path = config_path  # Store for cleanup
            cmd.extend(["--mcp-config", config_path])
            cmd.append("--strict-mcp-config")  # Only use our specified servers
            logger.log_debug(
                job.id,
                "Using custom MCP configuration",
                {
                    "required_servers": list(required_servers),
                    "config_path": config_path,
                },
            )
        else:
            logger.log_debug(job.id, "No MCP servers required for this task")

        # Handle permission mode with security validation
        validated_mode = config.security.validate_permission_mode(job.permission_mode)
        if validated_mode == "bypassPermissions" and config.security.allow_bypass_permissions:
            cmd.append("--dangerously-skip-permissions")
            logger.log_debug(job.id, "Using bypass permissions mode (allowed by config)")
        elif validated_mode != job.permission_mode:
            logger.log_debug(
                job.id,
                f"Permission mode overridden for security: {job.permission_mode} -> {validated_mode}"
            )

        # Add output format (omit when requesting plain text like your working example)
        if job.output_format in ("json", "stream-json"):
            cmd.extend(["--output-format", job.output_format])

        # Add verbose flag
        if job.verbose:
            cmd.append("--verbose")

        # Add the prompt. Order: -p then task, then skip-permissions.
        cmd.extend(["-p", job.task])

        # Set up environment
        env = os.environ.copy()

        # Check if job has custom environment variables (e.g., dedicated token)
        if job.env and "CLAUDE_CODE_TOKEN" in job.env:
            env["CLAUDE_CODE_TOKEN"] = job.env["CLAUDE_CODE_TOKEN"]
            logger.log_trace(
                job.id, "Using job-specific auth token for parallel execution"
            )
        elif config.claude_code_token:
            env["CLAUDE_CODE_TOKEN"] = config.claude_code_token
            logger.log_trace(job.id, "Auth token set in environment")
        else:
            logger.log_debug(job.id, "No auth token configured")

        # Clean environment of potentially conflicting variables
        # IMPORTANT: Remove ANTHROPIC_API_KEY as it conflicts with CLAUDE_CODE_TOKEN
        # The claude CLI uses CLAUDE_CODE_TOKEN for authentication
        removed_vars = []

        # Remove ANTHROPIC_API_KEY completely - don't set to empty string
        # as that could cause different behavior than not having it at all
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            removed_vars.append("ANTHROPIC_API_KEY")

        # Then clean other conflicting variables
        for key in list(env.keys()):
            if key.startswith("CLAUDE_") and key != "CLAUDE_CODE_TOKEN":
                del env[key]
                removed_vars.append(key)
            elif key.startswith("ANTHROPIC_") and key != "ANTHROPIC_API_KEY":
                del env[key]
                removed_vars.append(key)

        if removed_vars:
            logger.log_trace(
                job.id, "Cleaned environment variables", {"removed": removed_vars}
            )

        try:
            logger.log_debug(
                job.id,
                "Spawning subprocess",
                {
                    "command": " ".join(shlex.quote(part) for part in cmd),
                    "cwd": job.cwd,
                },
            )

            # Start the process asynchronously
            # Use DEVNULL for stdin to prevent hanging on CLI tools that might expect input
            process = await asyncio.create_subprocess_exec(
                *cmd,  # Unpack command list
                cwd=job.cwd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            job.process = process
            self.performance_monitor.update_metrics(job.id, "spawned")

            # If MCP servers are required, wait for them to be ready
            if required_servers:
                from opsvi_mcp.servers.claude_code_v2.mcp_manager import (
                    MCPInstanceConfig,
                    MCPAvailabilityChecker,
                )

                instance_config = MCPInstanceConfig(
                    instance_id=job.id,
                    config_path=config_path,
                    required_servers=required_servers,
                    max_wait_seconds=7,
                    exponential_backoff=True,
                )

                checker = MCPAvailabilityChecker(instance_config)

                # Run async check properly in existing event loop
                ready, metrics = await checker.wait_for_mcp_servers(
                    required_servers=required_servers
                )

                if not ready:
                    # MCP servers failed to initialize
                    process.terminate()
                    job.status = JobStatus.FAILED
                    job.error = "MCP servers failed to initialize within timeout"

                    failed_servers = [
                        m.server_name
                        for m in metrics.values()
                        if m.status.value == "failed"
                    ]

                    logger.log_error(
                        job.id,
                        "MCP initialization failed",
                        {"failed_servers": failed_servers},
                    )

                    job.result = {
                        "error": "MCP server initialization timeout",
                        "failed_servers": failed_servers,
                        "metrics": {
                            s: {
                                "status": m.status.value,
                                "attempts": m.check_attempts,
                                "error": m.error_message,
                            }
                            for s, m in metrics.items()
                        },
                    }
                    return
                else:
                    logger.log_debug(
                        job.id,
                        "MCP servers ready",
                        {
                            "initialization_times": {
                                s: m.initialization_duration_ms
                                for s, m in metrics.items()
                                if m.initialization_duration_ms
                            }
                        },
                    )

            logger.log(
                "INFO",
                job.id,
                "Claude Code process spawned",
                {
                    "command": " ".join(shlex.quote(part) for part in cmd),
                    "cwd": job.cwd,
                    "pid": process.pid,
                },
            )

            # Get timeout based on recursion depth
            timeout = self.recursion_manager.get_timeout_for_depth(
                job.recursion_context.depth if job.recursion_context else 0
            )

            # Wait for completion with timeout
            try:
                logger.log_debug(
                    job.id,
                    "Waiting for process completion",
                    {"timeout_ms": timeout, "timeout_seconds": timeout / 1000},
                )

                # Use asyncio timeout instead of process.communicate
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout / 1000  # Convert to seconds
                )

                # Decode bytes from async subprocess once
                stdout_str = stdout.decode('utf-8') if stdout else ''
                stderr_str = stderr.decode('utf-8') if stderr else ''
                
                # Store in job buffers
                job.stdout_buffer = stdout_str
                job.stderr_buffer = stderr_str

                logger.log_trace(
                    job.id,
                    "Process completed",
                    {
                        "return_code": process.returncode,
                        "stdout_size": len(stdout_str),
                        "stderr_size": len(stderr_str),
                    },
                )

                # Log child process outputs
                if stdout_str:
                    logger.log_child_output(job.id, "stdout", stdout_str)
                if stderr_str:
                    logger.log_child_output(job.id, "stderr", stderr_str)

                # Check for specific error conditions
                
                if stdout_str and "Credit balance is too low" in stdout_str:
                    error_msg = "Claude API error: Credit balance is too low. Please check your CLAUDE_CODE_TOKEN and account credits."
                    logger.log_error(job.id, error_msg, data={"stdout": stdout_str})
                    await self._handle_job_failure(job, error_msg, stderr_str)
                elif process.returncode == 0:
                    await self._handle_job_success(job, stdout_str)
                else:
                    # Include stdout in error message if stderr is empty
                    error_details = stderr_str if stderr_str else stdout_str
                    await self._handle_job_failure(
                        job,
                        f"Process exited with code {process.returncode}",
                        error_details,
                    )

            except asyncio.TimeoutError:
                logger.log_debug(
                    job.id,
                    "Process timeout, killing process",
                    {"timeout_ms": timeout, "pid": process.pid},
                )
                process.kill()
                await process.wait()  # Wait for process to terminate
                await self._handle_job_timeout(job, timeout)

        except Exception as e:
            logger.log_error(job.id, "Exception during job execution", e)
            await self._handle_job_failure(job, str(e))

    async def _handle_job_success(self, job: ClaudeJob, output: str) -> None:
        """Handle successful job completion"""
        job.status = JobStatus.COMPLETED
        job.end_time = datetime.now()

        # Parse output
        try:
            if job.output_format == "json":
                parsed = json.loads(output)
                job.result = {
                    "content": [{"type": "text", "text": json.dumps(parsed, indent=2)}]
                }
            else:
                job.result = {"content": [{"type": "text", "text": output}]}
        except json.JSONDecodeError:
            job.result = {"content": [{"type": "text", "text": output}]}

        self.performance_monitor.update_metrics(job.id, "output_size", len(output))
        self.performance_monitor.update_metrics(job.id, "completed")

        await self._complete_job(job)

        logger.log(
            "INFO",
            job.id,
            "Job completed successfully",
            {
                "duration": (job.end_time - job.start_time).total_seconds(),
                "output_size": len(output),
            },
        )

    async def _handle_job_failure(
        self, job: ClaudeJob, error: str, stderr: Optional[str] = None
    ) -> None:
        """Handle job failure"""
        job.status = JobStatus.FAILED
        job.end_time = datetime.now()
        job.error = error
        if stderr:
            job.error += f"\n{stderr}"

        self.performance_monitor.update_metrics(job.id, "error")
        await self._complete_job(job)

        logger.log("ERROR", job.id, "Job failed", {"error": error, "stderr": stderr})

    async def _handle_job_timeout(self, job: ClaudeJob, timeout: int) -> None:
        """Handle job timeout"""
        job.status = JobStatus.TIMEOUT
        job.end_time = datetime.now()
        job.error = f"Job timeout at recursion depth {job.recursion_context.depth if job.recursion_context else 0}"

        await self._complete_job(job)

        logger.log(
            "TIMEOUT",
            job.id,
            "Job timeout",
            {
                "depth": job.recursion_context.depth if job.recursion_context else 0,
                "timeout": timeout,
            },
        )

    async def _complete_job(self, job: ClaudeJob) -> None:
        """Move job from active to completed"""
        async with self.job_lock:
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            self.completed_jobs[job.id] = job

        # Cleanup recursion context
        self.recursion_manager.release_recursion_context(job.id)

        # Log parallel status
        self._log_parallel_status()

    def _log_parallel_status(self) -> None:
        """Log current parallel execution status"""
        active_count = len(self.active_jobs)
        if active_count > 1:
            job_ids = list(self.active_jobs.keys())
            logger.log_parallel(
                "SYSTEM",
                f"Running {active_count} jobs in parallel: {', '.join(job_ids)}",
            )

    async def execute_job_async(self, job: ClaudeJob) -> None:
        """Execute a job asynchronously"""
        logger.log_debug(
            job.id,
            "Starting async job execution",
            {
                "task_preview": job.task[:100],
                "recursion_depth": (
                    job.recursion_context.depth if job.recursion_context else 0
                ),
            },
        )

        # Acquire semaphores for concurrency control
        depth = job.recursion_context.depth if job.recursion_context else 0
        depth_semaphore = self._depth_semaphores.get(depth, self._depth_semaphores[0])
        
        async with self._global_semaphore:
            async with depth_semaphore:
                try:
                    logger.log_trace(job.id, "Executing job directly in async context")
                    await self.execute_job(job)
                    logger.log_debug(job.id, "Async job execution completed")
                except Exception as e:
                    logger.log_error(job.id, "Async job execution failed", e)
                    raise
                finally:
                    # Ensure cleanup happens even on error
                    if job.id in self.active_jobs or job.id in self.completed_jobs:
                        await self._ensure_cleanup(job)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a job"""
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)

        if not job:
            return None

        return {
            "jobId": job.id,
            "status": job.status.value,
            "task": job.task,
            "startTime": job.start_time.isoformat(),
            "endTime": job.end_time.isoformat() if job.end_time else None,
            "error": job.error,
            "recursionDepth": (
                job.recursion_context.depth if job.recursion_context else 0
            ),
            "parentJobId": job.parent_job_id,
        }

    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed job"""
        job = self.completed_jobs.get(job_id)

        if not job:
            # Check if it's still active
            if job_id in self.active_jobs:
                return {"error": "Job is still running"}
            return {"error": "Job not found"}

        if job.status != JobStatus.COMPLETED:
            return {"error": f"Job {job.status.value}: {job.error}"}

        return job.result

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs"""
        all_jobs = []

        for job in self.active_jobs.values():
            all_jobs.append(self.get_job_status(job.id))

        for job in self.completed_jobs.values():
            all_jobs.append(self.get_job_status(job.id))

        return all_jobs

    async def kill_job(self, job_id: str) -> bool:
        """Kill a running job"""
        job = self.active_jobs.get(job_id)

        if not job:
            return False

        if job.process and job.process.returncode is None:
            job.process.kill()
            await job.process.wait()  # Wait for process to terminate
            await self._handle_job_failure(job, "Job killed by user")
            return True

        return False

    async def _ensure_cleanup(self, job: ClaudeJob) -> None:
        """Ensure all resources are cleaned up for a job"""
        try:
            # Kill process if still running
            if hasattr(job, 'process') and job.process:
                if job.process.returncode is None:
                    job.process.kill()
                    await job.process.wait()
            
            # Clean up MCP config files if they exist
            if hasattr(job, 'mcp_config_path') and job.mcp_config_path:
                try:
                    Path(job.mcp_config_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.log_debug(job.id, f"Failed to clean up MCP config: {e}")
            
            # Clean up performance metrics
            self.performance_monitor.cleanup_metrics(job.id)
            
            # Release recursion context
            self.recursion_manager.release_recursion_context(job.id)
        except Exception as e:
            logger.log_error(job.id, f"Error during cleanup: {e}")

    def get_dashboard_data(self) -> DashboardData:
        """Generate dashboard data"""
        all_jobs = list(self.active_jobs.values()) + list(self.completed_jobs.values())
        failed_jobs = [j for j in all_jobs if j.status == JobStatus.FAILED]

        # Calculate average duration
        durations = []
        for job in self.completed_jobs.values():
            if job.end_time:
                duration = (job.end_time - job.start_time).total_seconds()
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Get max recursion depth
        max_depth = 0
        for ctx in self.recursion_manager.get_active_contexts():
            max_depth = max(max_depth, ctx.depth)

        # Get system load (memory usage in MB)
        import psutil

        process = psutil.Process()
        system_load = process.memory_info().rss / 1024 / 1024

        return DashboardData(
            active_jobs=len(self.active_jobs),
            completed_jobs=len(self.completed_jobs),
            failed_jobs=len(failed_jobs),
            average_duration=avg_duration,
            parallel_efficiency=self.performance_monitor.get_parallel_efficiency(
                len(self.active_jobs)
            ),
            nested_depth=max_depth,
            system_load=system_load,
            recursion_stats=self.recursion_manager.get_recursion_stats(),
        )
