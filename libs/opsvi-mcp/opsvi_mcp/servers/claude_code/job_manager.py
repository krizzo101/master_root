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
from threading import Lock

from .config import config
from .models import ClaudeJob, JobStatus, DashboardData
from .parallel_logger import logger
from .recursion_manager import RecursionManager
from .performance_monitor import PerformanceMonitor


class JobManager:
    """Manages Claude Code job execution and lifecycle"""

    def __init__(self):
        self.active_jobs: Dict[str, ClaudeJob] = {}
        self.completed_jobs: Dict[str, ClaudeJob] = {}
        self.recursion_manager = RecursionManager()
        self.performance_monitor = PerformanceMonitor()
        self.job_lock = Lock()

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
        permission_mode: str = "bypassPermissions",
        verbose: bool = False,
        parent_job_id: Optional[str] = None,
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

        job = ClaudeJob(
            id=job_id,
            task=task,
            cwd=cwd or os.getcwd(),
            output_format=output_format,
            permission_mode=permission_mode,
            verbose=verbose,
            recursion_context=recursion_context,
            parent_job_id=parent_job_id,
        )

        # Create performance metrics
        self.performance_monitor.create_metrics(job_id)

        with self.job_lock:
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

    def execute_job(self, job: ClaudeJob) -> None:
        """Execute a Claude Code job"""
        logger.log_debug(
            job.id,
            "Starting job execution",
            {"job_status": job.status.value, "start_time": job.start_time.isoformat()},
        )

        # Analyze task to determine required MCP servers
        from ..claude_code_v2.mcp_manager import MCPRequirementAnalyzer, MCPConfigManager
        
        required_servers = MCPRequirementAnalyzer.analyze_task(job.task)
        
        # Build command
        cmd = ["claude"]
        
        # Add MCP configuration if needed
        if required_servers:
            # Create minimal MCP config for this job
            config_path = MCPConfigManager.create_instance_config(
                instance_id=job.id,
                custom_servers=list(required_servers)
            )
            cmd.extend(["--mcp-config", config_path])
            cmd.append("--strict-mcp-config")  # Only use our specified servers
            logger.log_debug(
                job.id,
                "Using custom MCP configuration",
                {"required_servers": list(required_servers), "config_path": config_path}
            )
        else:
            logger.log_debug(job.id, "No MCP servers required for this task")

        # Always skip permission prompts for automation
        cmd.append("--dangerously-skip-permissions")

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
        if config.claude_code_token:
            env["CLAUDE_CODE_TOKEN"] = config.claude_code_token
            logger.log_trace(job.id, "Auth token set in environment")
        else:
            logger.log_debug(job.id, "No auth token configured")

        # Clean environment of potentially conflicting variables
        # IMPORTANT: Remove ANTHROPIC_API_KEY as it conflicts with CLAUDE_CODE_TOKEN
        # Since ANTHROPIC_API_KEY is set by default, we must override it
        removed_vars = []
        
        # First, explicitly handle ANTHROPIC_API_KEY
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            removed_vars.append("ANTHROPIC_API_KEY")
        # Set to empty string as double safety measure
        env["ANTHROPIC_API_KEY"] = ""
        
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

            # Start the process
            # Use DEVNULL for stdin to prevent hanging on CLI tools that might expect input
            process = subprocess.Popen(
                cmd,
                cwd=job.cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            job.process = process
            self.performance_monitor.update_metrics(job.id, "spawned")
            
            # If MCP servers are required, wait for them to be ready
            if required_servers:
                from ..claude_code_v2.mcp_manager import (
                    MCPInstanceConfig, 
                    MCPAvailabilityChecker
                )
                
                instance_config = MCPInstanceConfig(
                    instance_id=job.id,
                    config_path=config_path,
                    required_servers=required_servers,
                    max_wait_seconds=7,
                    exponential_backoff=True
                )
                
                checker = MCPAvailabilityChecker(instance_config)
                
                # Run async check in sync context
                import asyncio
                loop = asyncio.new_event_loop()
                try:
                    ready, metrics = loop.run_until_complete(
                        checker.wait_for_mcp_servers(required_servers=required_servers)
                    )
                finally:
                    loop.close()
                
                if not ready:
                    # MCP servers failed to initialize
                    process.terminate()
                    job.status = JobStatus.FAILED
                    job.error = "MCP servers failed to initialize within timeout"
                    
                    failed_servers = [
                        m.server_name for m in metrics.values() 
                        if m.status.value == "failed"
                    ]
                    
                    logger.log_error(
                        job.id,
                        "MCP initialization failed",
                        {"failed_servers": failed_servers}
                    )
                    
                    job.result = {
                        "error": "MCP server initialization timeout",
                        "failed_servers": failed_servers,
                        "metrics": {
                            s: {
                                "status": m.status.value,
                                "attempts": m.check_attempts,
                                "error": m.error_message
                            }
                            for s, m in metrics.items()
                        }
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
                        }
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

                stdout, stderr = process.communicate(
                    timeout=timeout / 1000
                )  # Convert to seconds

                job.stdout_buffer = stdout
                job.stderr_buffer = stderr

                logger.log_trace(
                    job.id,
                    "Process completed",
                    {
                        "return_code": process.returncode,
                        "stdout_size": len(stdout) if stdout else 0,
                        "stderr_size": len(stderr) if stderr else 0,
                    },
                )

                # Log child process outputs
                if stdout:
                    logger.log_child_output(job.id, "stdout", stdout)
                if stderr:
                    logger.log_child_output(job.id, "stderr", stderr)

                # Check for specific error conditions
                if stdout and "Credit balance is too low" in stdout:
                    error_msg = "Claude API error: Credit balance is too low. Please check your CLAUDE_CODE_TOKEN and account credits."
                    logger.log_error(job.id, error_msg, data={"stdout": stdout})
                    self._handle_job_failure(job, error_msg, stderr)
                elif process.returncode == 0:
                    self._handle_job_success(job, stdout)
                else:
                    # Include stdout in error message if stderr is empty
                    error_details = stderr if stderr else stdout
                    self._handle_job_failure(
                        job,
                        f"Process exited with code {process.returncode}",
                        error_details,
                    )

            except subprocess.TimeoutExpired:
                logger.log_debug(
                    job.id,
                    "Process timeout, killing process",
                    {"timeout_ms": timeout, "pid": process.pid},
                )
                process.kill()
                self._handle_job_timeout(job, timeout)

        except Exception as e:
            logger.log_error(job.id, "Exception during job execution", e)
            self._handle_job_failure(job, str(e))

    def _handle_job_success(self, job: ClaudeJob, output: str) -> None:
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

        self._complete_job(job)

        logger.log(
            "INFO",
            job.id,
            "Job completed successfully",
            {
                "duration": (job.end_time - job.start_time).total_seconds(),
                "output_size": len(output),
            },
        )

    def _handle_job_failure(
        self, job: ClaudeJob, error: str, stderr: Optional[str] = None
    ) -> None:
        """Handle job failure"""
        job.status = JobStatus.FAILED
        job.end_time = datetime.now()
        job.error = error
        if stderr:
            job.error += f"\n{stderr}"

        self.performance_monitor.update_metrics(job.id, "error")
        self._complete_job(job)

        logger.log("ERROR", job.id, "Job failed", {"error": error, "stderr": stderr})

    def _handle_job_timeout(self, job: ClaudeJob, timeout: int) -> None:
        """Handle job timeout"""
        job.status = JobStatus.TIMEOUT
        job.end_time = datetime.now()
        job.error = f"Job timeout at recursion depth {job.recursion_context.depth if job.recursion_context else 0}"

        self._complete_job(job)

        logger.log(
            "TIMEOUT",
            job.id,
            "Job timeout",
            {
                "depth": job.recursion_context.depth if job.recursion_context else 0,
                "timeout": timeout,
            },
        )

    def _complete_job(self, job: ClaudeJob) -> None:
        """Move job from active to completed"""
        with self.job_lock:
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            self.completed_jobs[job.id] = job

        # Cleanup recursion context
        self.recursion_manager.cleanup_job(job.id)

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

        try:
            loop = asyncio.get_event_loop()
            logger.log_trace(job.id, "Scheduling job in executor pool")
            await loop.run_in_executor(None, self.execute_job, job)
            logger.log_debug(job.id, "Async job execution completed")
        except Exception as e:
            logger.log_error(job.id, "Async job execution failed", e)
            raise

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

    def kill_job(self, job_id: str) -> bool:
        """Kill a running job"""
        job = self.active_jobs.get(job_id)

        if not job:
            return False

        if job.process and job.process.poll() is None:
            job.process.kill()
            self._handle_job_failure(job, "Job killed by user")
            return True

        return False

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
