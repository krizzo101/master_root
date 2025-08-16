"""
Claude Code MCP Client with comprehensive error handling
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import uuid
import os
from datetime import datetime
import backoff

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClaudeTask:
    prompt: str
    mode: str = "sync"  # sync, async, batch
    permission: str = "bypassPermissions"
    output_format: str = "json"
    timeout: int = 300
    max_retries: int = 3
    retry_count: int = 0
    cwd: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times = []

    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()

        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if (now - t).total_seconds() < 60]

        # If at limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]).total_seconds()
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self.request_times.append(now)


class ClaudeClient:
    """Robust Claude Code MCP client"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_jobs = {}
        self.token_usage = 0
        self.request_count = 0
        self.rate_limiter = RateLimiter(
            config.get("rate_limits", {}).get("requests_per_minute", 60)
        )
        self.mcp_available = self._check_mcp_availability()

    def _check_mcp_availability(self) -> bool:
        """Check if MCP is available"""
        try:
            # Check for MCP environment or configuration
            if os.environ.get("CLAUDE_CODE_TOKEN"):
                return True
            # In real implementation, would check for actual MCP availability
            return False
        except:
            return False

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30,
        on_backoff=lambda d: logger.warning(f"Retrying Claude call, attempt {d['tries']}"),
    )
    async def execute(self, prompt: str, mode: str = "sync") -> Dict[str, Any]:
        """Execute prompt with Claude Code"""

        await self.rate_limiter.acquire()

        task = ClaudeTask(prompt=prompt, mode=mode)

        try:
            if mode == "sync":
                return await self._execute_sync(task)
            elif mode == "async":
                return await self._execute_async(task)
            elif mode == "batch":
                return await self._execute_batch([task])
            else:
                raise ValueError(f"Unknown mode: {mode}")

        except asyncio.TimeoutError:
            logger.error(f"Claude execution timed out after {task.timeout}s")
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying ({task.retry_count}/{task.max_retries})")
                return await self.execute(prompt, mode)
            raise

        except Exception as e:
            logger.error(f"Claude execution failed: {e}")
            raise

    async def execute_batch(self, tasks: List[ClaudeTask]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in batch"""

        await self.rate_limiter.acquire()

        if self.mcp_available:
            return await self._execute_batch_mcp(tasks)
        else:
            # Fallback to sequential execution
            results = []
            for task in tasks:
                result = await self._execute_sync(task)
                results.append(result)
            return results

    async def _execute_sync(self, task: ClaudeTask) -> Dict[str, Any]:
        """Synchronous execution via MCP"""

        logger.debug(f"Executing sync task: {task.prompt[:100]}...")

        if self.mcp_available:
            try:
                # Import and use actual MCP
                # from mcp__claude_code import claude_run
                # result = await claude_run(
                #     task=task.prompt,
                #     outputFormat=task.output_format,
                #     permissionMode=task.permission,
                #     cwd=task.cwd
                # )
                result = await self._simulate_mcp_call(
                    "claude_run",
                    task=task.prompt,
                    outputFormat=task.output_format,
                    permissionMode=task.permission,
                )
            except Exception as e:
                logger.error(f"MCP call failed: {e}")
                result = await self._fallback_execution(task)
        else:
            result = await self._fallback_execution(task)

        self.token_usage += result.get("token_usage", 100)
        self.request_count += 1

        return self._parse_result(result)

    async def _execute_async(self, task: ClaudeTask) -> Dict[str, Any]:
        """Asynchronous execution with polling"""

        logger.debug(f"Starting async task: {task.prompt[:100]}...")

        if self.mcp_available:
            try:
                # Start job
                job_id = await self._simulate_mcp_call(
                    "claude_run_async",
                    task=task.prompt,
                    outputFormat=task.output_format,
                    permissionMode=task.permission,
                )

                self.active_jobs[job_id] = task

                # Poll for completion
                result = await self._poll_job(job_id, task.timeout)

                del self.active_jobs[job_id]
                return self._parse_result(result)

            except Exception as e:
                logger.error(f"Async execution failed: {e}")
                return await self._fallback_execution(task)
        else:
            return await self._fallback_execution(task)

    async def _poll_job(self, job_id: str, timeout: int) -> Dict[str, Any]:
        """Poll for job completion"""

        max_polls = timeout // 2  # Poll every 2 seconds

        for poll_count in range(max_polls):
            status = await self._simulate_mcp_call("claude_status", jobId=job_id)

            if status["status"] == "completed":
                result = await self._simulate_mcp_call("claude_result", jobId=job_id)
                return result

            elif status["status"] == "failed":
                raise Exception(f"Job {job_id} failed: {status.get('error')}")

            # Log progress periodically
            if poll_count % 10 == 0:
                logger.debug(f"Job {job_id} still running... ({poll_count * 2}s)")

            await asyncio.sleep(2)

        raise asyncio.TimeoutError(f"Job {job_id} timed out after {timeout}s")

    async def _execute_batch_mcp(self, tasks: List[ClaudeTask]) -> List[Dict[str, Any]]:
        """Batch execution via MCP"""

        logger.debug(f"Executing batch of {len(tasks)} tasks")

        batch_tasks = [
            {"task": t.prompt, "output_format": t.output_format, "permission_mode": t.permission}
            for t in tasks
        ]

        try:
            result = await self._simulate_mcp_call(
                "claude_run_batch",
                tasks=batch_tasks,
                max_concurrent=self.config.get("max_concurrent", 5),
            )

            return [self._parse_result(r) for r in result.get("results", [])]

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            # Fallback to sequential
            results = []
            for task in tasks:
                result = await self._execute_sync(task)
                results.append(result)
            return results

    async def _simulate_mcp_call(self, function: str, **kwargs) -> Any:
        """Simulate MCP call for development"""

        # In production, this would be replaced with actual MCP calls:
        # if function == "claude_run":
        #     from mcp__claude_code import claude_run
        #     return await claude_run(**kwargs)

        # Simulation for development
        await asyncio.sleep(0.5)  # Simulate network delay

        if function == "claude_run":
            # Simulate intelligent response based on prompt
            prompt = kwargs.get("task", "")

            if "assess" in prompt.lower():
                response = {
                    "progress": 25,
                    "bottlenecks": ["learning_rate", "capability_discovery"],
                    "missing_capabilities": ["advanced_reasoning", "web_search"],
                    "metrics": {"iteration_time": 3.2, "success_rate": 0.75},
                    "recommendations": ["increase_learning_rate", "expand_search"],
                }
            elif "execute" in prompt.lower() or "plan" in prompt.lower():
                response = {
                    "actions": ["analyze_patterns", "optimize_performance"],
                    "expected_outcomes": ["improved_efficiency", "better_accuracy"],
                    "success_criteria": {"min_improvement": 0.1},
                }
            else:
                response = {"result": "Task completed successfully", "data": {}}

            return {
                "success": True,
                "content": [{"type": "text", "text": json.dumps(response)}],
                "token_usage": len(prompt) // 4,  # Rough estimate
            }

        elif function == "claude_run_async":
            return f"job_{uuid.uuid4().hex[:8]}"

        elif function == "claude_status":
            # Simulate job progress
            return {"status": "completed", "progress": 100}

        elif function == "claude_result":
            return {
                "success": True,
                "content": [{"type": "text", "text": '{"result": "async task completed"}'}],
                "token_usage": 50,
            }

        elif function == "claude_run_batch":
            results = []
            for task in kwargs.get("tasks", []):
                results.append(
                    {
                        "success": True,
                        "content": [{"type": "text", "text": '{"result": "batch item completed"}'}],
                    }
                )
            return {"results": results}

        return {}

    async def _fallback_execution(self, task: ClaudeTask) -> Dict[str, Any]:
        """Fallback execution when MCP is not available"""

        logger.warning("Using fallback execution (MCP not available)")

        # Simulate intelligent processing
        await asyncio.sleep(1)

        # Generate mock response based on prompt analysis
        prompt_lower = task.prompt.lower()

        if "assess" in prompt_lower or "analyze" in prompt_lower:
            response = {
                "progress": 30,
                "bottlenecks": ["resource_limits"],
                "missing_capabilities": ["mcp_integration"],
                "metrics": {"success_rate": 0.6},
                "recommendations": ["enable_mcp", "increase_resources"],
            }
        else:
            response = {
                "result": "Fallback execution completed",
                "warning": "MCP not available, using limited capabilities",
            }

        return {
            "success": True,
            "content": [{"type": "text", "text": json.dumps(response)}],
            "token_usage": 50,
        }

    def _parse_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude response"""

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Claude execution failed: {error_msg}")
            return {"error": error_msg, "success": False}

        content = result.get("content", [])
        if not content:
            return {"result": None}

        # Extract text content
        text_content = ""
        for item in content:
            if item.get("type") == "text":
                text_content += item.get("text", "")

        # Try to parse as JSON
        try:
            parsed = json.loads(text_content)
            return parsed
        except json.JSONDecodeError:
            # Return as text if not JSON
            return {"text": text_content}

    async def wait_for_job(self, job_id: str) -> Dict[str, Any]:
        """Wait for an async job to complete"""

        if job_id not in self.active_jobs:
            raise ValueError(f"Unknown job ID: {job_id}")

        task = self.active_jobs[job_id]
        return await self._poll_job(job_id, task.timeout)

    async def close(self):
        """Cleanup resources"""

        # Cancel any active jobs
        for job_id in list(self.active_jobs.keys()):
            logger.warning(f"Cancelling active job: {job_id}")
            try:
                # In production: await mcp__claude_code__claude_kill_job(jobId=job_id)
                pass
            except:
                pass

        self.active_jobs.clear()
        logger.info(
            f"Claude client closed. Total requests: {self.request_count}, Tokens used: {self.token_usage}"
        )
