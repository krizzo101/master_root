"""
Gemini Agent MCP Server

Provides MCP interface to Google's Gemini CLI for AI-powered coding assistance.
"""

import asyncio
import json
import os
import subprocess
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from fastmcp import FastMCP

from .config import GeminiConfig
from .models import GeminiRequest, GeminiResponse, GeminiTask, GeminiMode, GeminiMetrics


logger = logging.getLogger(__name__)


class GeminiAgentServer:
    """MCP Server for Gemini CLI integration"""

    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig.from_env()
        self.config.validate()

        self.mcp = FastMCP("gemini-agent")
        self.active_tasks: Dict[str, GeminiTask] = {}
        self.metrics = GeminiMetrics()

        # Setup logging
        if self.config.log_file:
            logging.basicConfig(
                level=self.config.log_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler(self.config.log_file),
                    logging.StreamHandler(),
                ],
            )

        # Setup MCP tools
        self._setup_tools()

    def _setup_tools(self):
        """Register MCP tools"""

        @self.mcp.tool()
        async def execute_gemini(
            task: str,
            mode: str = "react",
            context_files: Optional[List[str]] = None,
            working_directory: Optional[str] = None,
            timeout: int = 300,
            max_iterations: int = 10,
            enable_web_search: bool = True,
            enable_file_ops: bool = True,
            enable_shell: bool = True,
            metadata: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Execute a task using Gemini CLI.

            Args:
                task: Task description for Gemini to execute
                mode: Execution mode (react, code, analyze, debug, test, document, refactor, review, search)
                context_files: Optional list of files to include as context
                working_directory: Optional working directory for execution
                timeout: Timeout in seconds (default: 300)
                max_iterations: Maximum iterations for ReAct loop (default: 10)
                enable_web_search: Enable web search capability
                enable_file_ops: Enable file operations
                enable_shell: Enable shell command execution
                metadata: Optional metadata for the task
            """
            try:
                # Update metrics
                self.metrics.total_requests += 1
                self.metrics.requests_today += 1
                self.metrics.requests_this_minute += 1

                # Create request
                request = GeminiRequest(
                    task=task,
                    mode=GeminiMode(mode),
                    context_files=context_files or [],
                    working_directory=working_directory
                    or self.config.working_directory,
                    timeout=timeout,
                    max_iterations=max_iterations,
                    enable_web_search=enable_web_search,
                    enable_file_ops=enable_file_ops,
                    enable_shell=enable_shell,
                    metadata=metadata or {},
                )

                # Execute task
                response = await self._execute_task(request)

                # Update metrics based on response
                if response.status == "success":
                    self.metrics.successful_requests += 1
                elif response.status == "failure":
                    self.metrics.failed_requests += 1
                elif response.status == "timeout":
                    self.metrics.timeout_requests += 1

                self.metrics.total_tokens += response.tokens_used
                self.metrics.total_cost += response.cost_estimate

                return {
                    "success": response.status == "success",
                    "request_id": response.request_id,
                    "mode": response.mode.value,
                    "output": response.output,
                    "reasoning_steps": response.reasoning_steps,
                    "actions_taken": response.actions_taken,
                    "files_created": response.files_created,
                    "files_modified": response.files_modified,
                    "commands_executed": response.commands_executed,
                    "web_searches": response.web_searches,
                    "execution_time_ms": response.execution_time_ms,
                    "tokens_used": response.tokens_used,
                    "cost_estimate": response.cost_estimate,
                    "error": response.error,
                    "metadata": response.metadata,
                }

            except Exception as e:
                logger.error(f"Failed to execute Gemini task: {e}")
                self.metrics.failed_requests += 1
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def execute_gemini_async(
            task: str,
            mode: str = "react",
            context_files: Optional[List[str]] = None,
            working_directory: Optional[str] = None,
            timeout: int = 300,
            max_iterations: int = 10,
            enable_web_search: bool = True,
            enable_file_ops: bool = True,
            enable_shell: bool = True,
            metadata: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Execute a task asynchronously using Gemini CLI.
            Returns immediately with a task ID.
            """
            try:
                # Create request
                request = GeminiRequest(
                    task=task,
                    mode=GeminiMode(mode),
                    context_files=context_files or [],
                    working_directory=working_directory
                    or self.config.working_directory,
                    timeout=timeout,
                    max_iterations=max_iterations,
                    enable_web_search=enable_web_search,
                    enable_file_ops=enable_file_ops,
                    enable_shell=enable_shell,
                    metadata=metadata or {},
                )

                # Create task
                task_id = str(uuid.uuid4())
                gemini_task = GeminiTask(id=task_id, request=request, status="pending")

                self.active_tasks[task_id] = gemini_task

                # Start execution in background
                asyncio.create_task(self._execute_task_async(gemini_task))

                return {
                    "success": True,
                    "task_id": task_id,
                    "status": "started",
                    "message": "Task started in background. Use check_gemini_status to monitor.",
                }

            except Exception as e:
                logger.error(f"Failed to start async Gemini task: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def check_gemini_status(task_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Check status of Gemini tasks.

            Args:
                task_id: Optional specific task ID to check. If None, returns all active tasks.
            """
            try:
                if task_id:
                    if task_id not in self.active_tasks:
                        return {"success": False, "error": f"Task {task_id} not found"}

                    task = self.active_tasks[task_id]
                    return {
                        "success": True,
                        "task_id": task_id,
                        "status": task.status,
                        "duration_seconds": task.duration_seconds(),
                    }
                else:
                    # Return all active tasks
                    tasks_info = []
                    for tid, task in self.active_tasks.items():
                        tasks_info.append(
                            {
                                "task_id": tid,
                                "status": task.status,
                                "duration_seconds": task.duration_seconds(),
                            }
                        )

                    return {
                        "success": True,
                        "active_tasks": len(tasks_info),
                        "tasks": tasks_info,
                    }

            except Exception as e:
                logger.error(f"Failed to check Gemini status: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def get_gemini_result(task_id: str) -> Dict[str, Any]:
            """
            Get result of a completed Gemini task.

            Args:
                task_id: The task ID to retrieve results for
            """
            try:
                if task_id not in self.active_tasks:
                    return {"success": False, "error": f"Task {task_id} not found"}

                task = self.active_tasks[task_id]

                if task.status != "completed":
                    return {
                        "success": False,
                        "error": f"Task {task_id} is not completed yet. Status: {task.status}",
                    }

                # Read output file
                if task.output_file and os.path.exists(task.output_file):
                    with open(task.output_file, "r") as f:
                        output = json.load(f)

                    # Clean up
                    os.remove(task.output_file)
                    if task.error_file and os.path.exists(task.error_file):
                        os.remove(task.error_file)

                    del self.active_tasks[task_id]

                    return output
                else:
                    return {"success": False, "error": "Output file not found"}

            except Exception as e:
                logger.error(f"Failed to get Gemini result: {e}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        async def get_gemini_metrics() -> Dict[str, Any]:
            """
            Get metrics for Gemini agent usage.
            """
            return {
                "success": True,
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "timeout_requests": self.metrics.timeout_requests,
                    "success_rate": self.metrics.success_rate(),
                    "total_tokens": self.metrics.total_tokens,
                    "total_cost": self.metrics.total_cost,
                    "average_response_time_ms": self.metrics.average_response_time_ms,
                    "requests_today": self.metrics.requests_today,
                    "requests_this_minute": self.metrics.requests_this_minute,
                    "daily_quota_remaining": 1000 - self.metrics.requests_today,
                    "minute_quota_remaining": 60 - self.metrics.requests_this_minute,
                },
            }

        @self.mcp.tool()
        async def list_gemini_capabilities() -> Dict[str, Any]:
            """
            List available Gemini capabilities and modes.
            """
            return {
                "success": True,
                "capabilities": {
                    "modes": [mode.value for mode in GeminiMode],
                    "features": {
                        "web_search": self.config.enable_web_search,
                        "file_operations": self.config.enable_file_operations,
                        "shell_commands": self.config.enable_shell_commands,
                        "mcp_servers": self.config.enable_mcp_servers,
                        "github_integration": bool(self.config.github_token),
                        "google_cloud": bool(self.config.google_cloud_project),
                    },
                    "limits": {
                        "context_window": self.config.context_window,
                        "max_iterations": self.config.max_iterations,
                        "timeout_seconds": self.config.timeout_seconds,
                        "requests_per_minute": self.config.max_requests_per_minute,
                        "requests_per_day": self.config.max_requests_per_day,
                    },
                    "model": self.config.model,
                },
            }

    async def _execute_task(self, request: GeminiRequest) -> GeminiResponse:
        """Execute a Gemini task synchronously"""
        start_time = datetime.now()
        request_id = str(uuid.uuid4())

        try:
            # Prepare command - use prompt flag for non-interactive mode
            cmd = ["gemini", "--prompt", request.task]

            # Add model if specified
            if self.config.model:
                cmd.extend(["--model", self.config.model])

            # Add approval mode based on settings
            if request.enable_file_ops or request.enable_shell:
                cmd.extend(
                    ["--approval-mode", "yolo"]
                )  # Auto-approve for programmatic use

            # Create temp file for output
            output_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            output_file.close()

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=request.working_directory,
                env={**os.environ, "GEMINI_API_KEY": self.config.api_key},
            )

            # No input needed since we're using --prompt
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=request.timeout
            )

            # Parse output
            output_text = stdout.decode()
            error_text = stderr.decode() if stderr else None

            # Calculate execution time
            execution_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            # Create response
            response = GeminiResponse(
                request_id=request_id,
                status="success" if process.returncode == 0 else "failure",
                mode=request.mode,
                output=output_text,
                execution_time_ms=execution_time_ms,
                error=error_text if process.returncode != 0 else None,
                metadata=request.metadata,
            )

            # Parse structured output if available
            self._parse_structured_output(response, output_text)

            # Estimate tokens and cost
            response.tokens_used = len(output_text.split()) * 1.3  # Rough estimate
            response.cost_estimate = (
                response.tokens_used * 0.000001
            )  # Placeholder pricing

            return response

        except asyncio.TimeoutError:
            return GeminiResponse(
                request_id=request_id,
                status="timeout",
                mode=request.mode,
                output="",
                error=f"Task timed out after {request.timeout} seconds",
                execution_time_ms=request.timeout * 1000,
                metadata=request.metadata,
            )
        except Exception as e:
            return GeminiResponse(
                request_id=request_id,
                status="failure",
                mode=request.mode,
                output="",
                error=str(e),
                execution_time_ms=int(
                    (datetime.now() - start_time).total_seconds() * 1000
                ),
                metadata=request.metadata,
            )
        finally:
            # Clean up temp file
            if "output_file" in locals():
                try:
                    os.unlink(output_file.name)
                except:
                    pass

    async def _execute_task_async(self, task: GeminiTask):
        """Execute a Gemini task asynchronously"""
        task.status = "running"
        task.start_time = datetime.now()

        try:
            response = await self._execute_task(task.request)

            # Save output to file
            task.output_file = f"/tmp/gemini_result_{task.id}.json"
            with open(task.output_file, "w") as f:
                json.dump(
                    {
                        "success": response.status == "success",
                        "request_id": response.request_id,
                        "mode": response.mode.value,
                        "output": response.output,
                        "reasoning_steps": response.reasoning_steps,
                        "actions_taken": response.actions_taken,
                        "files_created": response.files_created,
                        "files_modified": response.files_modified,
                        "commands_executed": response.commands_executed,
                        "web_searches": response.web_searches,
                        "execution_time_ms": response.execution_time_ms,
                        "tokens_used": response.tokens_used,
                        "cost_estimate": response.cost_estimate,
                        "error": response.error,
                        "metadata": response.metadata,
                    },
                    f,
                    indent=2,
                )

            task.status = "completed"

        except Exception as e:
            task.status = "failed"
            task.error_file = f"/tmp/gemini_error_{task.id}.txt"
            with open(task.error_file, "w") as f:
                f.write(str(e))

        finally:
            task.end_time = datetime.now()

    def _parse_structured_output(self, response: GeminiResponse, output_text: str):
        """Parse structured output from Gemini CLI"""
        lines = output_text.split("\n")

        for line in lines:
            line = line.strip()

            # Parse reasoning steps (if in ReAct mode)
            if line.startswith("THOUGHT:"):
                response.reasoning_steps.append(line[8:].strip())
            elif line.startswith("ACTION:"):
                action_text = line[7:].strip()
                response.actions_taken.append({"action": action_text})

            # Parse file operations
            elif "created file:" in line.lower():
                file_path = line.split("created file:")[-1].strip()
                response.files_created.append(file_path)
            elif "modified file:" in line.lower():
                file_path = line.split("modified file:")[-1].strip()
                response.files_modified.append(file_path)

            # Parse commands
            elif line.startswith("$") or line.startswith(">"):
                response.commands_executed.append(line[1:].strip())

            # Parse web searches
            elif "searching for:" in line.lower():
                query = line.split("searching for:")[-1].strip()
                response.web_searches.append(query)

    def run(self):
        """Run the MCP server"""
        logger.info(f"Starting Gemini Agent MCP Server with model: {self.config.model}")
        logger.info(f"Context window: {self.config.context_window} tokens")
        logger.info(f"Daily quota: {self.config.max_requests_per_day} requests")

        # FastMCP's run() method handles the event loop
        self.mcp.run()


def main():
    """Main entry point"""
    import logging
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        # Create config
        config = GeminiConfig.from_env()
        config.validate()

        # Create server
        server = GeminiAgentServer(config)

        logger.info("Starting Gemini Agent MCP Server...")
        logger.info(f"Model: {config.model}")
        logger.info(f"Context window: {config.context_window:,} tokens")
        logger.info(f"Working directory: {config.working_directory}")

        # Run server - FastMCP handles the event loop
        server.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
