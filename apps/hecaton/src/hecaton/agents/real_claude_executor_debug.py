"""
Real Claude Code Executor with comprehensive debug logging
This spawns REAL Claude Code processes using the CLI with full debugging
"""

import asyncio
import json
import os

# import subprocess  # unused
import sys

# import tempfile  # unused
import traceback

# import uuid  # unused
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hecaton.utils.debug_logger import get_logger, set_debug_mode  # noqa: E402

# Enable debug mode for development
set_debug_mode(True)


@dataclass
class ClaudeProcess:
    """Represents a real Claude Code subprocess"""

    id: str
    task: str
    token: str
    worktree: Path
    process: Optional[asyncio.subprocess.Process] = None
    stdout: str = ""
    stderr: str = ""
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


class RealClaudeSubprocessExecutor:
    """
    Executes tasks using REAL Claude Code subprocesses with full debug logging.
    This spawns actual 'claude' CLI processes with proper tokens.
    """

    def __init__(self, token_pool, worktree_manager):
        """Initialize with token pool and worktree manager"""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug_enter(
            "__init__", token_pool=token_pool, worktree_manager=worktree_manager
        )

        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.active_processes: Dict[str, ClaudeProcess] = {}

        self.logger.info(f"Initialized with {self.token_pool.get_token_count()} tokens")
        self.logger.debug_exit("__init__")

    async def execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with a real Claude Code subprocess"""

        self.logger.debug_enter("execute_single_task", task_id=task.get("id"))
        self.logger.debug_data("task", task)

        try:
            # Get resources
            self.logger.debug_step("Acquiring token from pool")
            token, token_idx = self.token_pool.acquire()
            self.logger.debug_data(
                "token_acquired", {"index": token_idx, "token_prefix": token[:10] + "..."}
            )

            self.logger.debug_step("Creating worktree")
            worktree = self.worktree_manager.create(task["id"])
            self.logger.debug_data("worktree", str(worktree))

            # Create process tracking
            process = ClaudeProcess(
                id=task["id"],
                task=task.get("prompt", task.get("description", "")),
                token=token,
                worktree=worktree,
            )
            self.active_processes[process.id] = process
            self.logger.debug_step("Process tracking created", process.id)

            # Write task to temporary file (for complex prompts)
            task_file = Path(worktree) / "task.txt"
            self.logger.debug_step(f"Writing task to {task_file}")
            with open(task_file, "w") as f:
                f.write(process.task)
            self.logger.debug_data("task_content_length", len(process.task))

            # Prepare environment
            self.logger.debug_step("Preparing environment")
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token
            env["ANTHROPIC_API_KEY"] = ""  # Must be null as instructed
            self.logger.debug_data("env_keys", list(env.keys())[:10])

            # Build Claude command (order matters!)
            cmd = [
                "claude",
                "--dangerously-skip-permissions",  # Skip permission prompts
                "-p",  # Prompt mode
                f"@{task_file}",  # Read prompt from file
            ]

            self.logger.info(f"🤖 Starting Claude process for {process.id} with token {token_idx}")
            self.logger.debug_data("command", " ".join(cmd))
            self.logger.debug_data("cwd", str(worktree))

            # Start the subprocess
            self.logger.debug_step("Creating subprocess")
            try:
                process.process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(worktree),
                    env=env,
                )
                self.logger.debug_data("process_pid", process.process.pid)
            except Exception as e:
                self.logger.debug_error(e, "subprocess creation")
                raise

            process.status = "running"
            self.logger.debug_step("Process started, waiting for completion")

            # Wait for completion and capture output
            try:
                stdout, stderr = await process.process.communicate()
                self.logger.debug_step("Process completed")
            except Exception as e:
                self.logger.debug_error(e, "process communication")
                raise

            process.stdout = stdout.decode() if stdout else ""
            process.stderr = stderr.decode() if stderr else ""

            self.logger.debug_data("stdout_length", len(process.stdout))
            self.logger.debug_data("stderr_length", len(process.stderr))
            self.logger.debug_data("return_code", process.process.returncode)

            if process.stdout:
                self.logger.debug_data("stdout_preview", process.stdout[:500])
            if process.stderr:
                self.logger.debug_data("stderr_preview", process.stderr[:500])

            if process.process.returncode == 0:
                process.status = "completed"

                # Try to parse JSON output
                try:
                    process.result = json.loads(process.stdout)
                    self.logger.debug_step("Parsed JSON output successfully")
                except json.JSONDecodeError:
                    process.result = {"output": process.stdout}
                    self.logger.debug_step("Could not parse JSON, storing as text")

                self.logger.info(f"✅ Claude process {process.id} completed successfully")

                result = {
                    "task_id": task["id"],
                    "status": "completed",
                    "process_id": process.id,
                    "output": process.stdout,
                    "result": process.result,
                }
                self.logger.debug_exit("execute_single_task", result={"status": "completed"})
                return result
            else:
                process.status = "failed"
                error_msg = (
                    process.stderr or f"Process exited with code {process.process.returncode}"
                )
                self.logger.error(f"❌ Claude process {process.id} failed: {error_msg}")

                result = {
                    "task_id": task["id"],
                    "status": "failed",
                    "process_id": process.id,
                    "error": error_msg,
                    "stderr": process.stderr,
                }
                self.logger.debug_exit(
                    "execute_single_task", result={"status": "failed", "error": error_msg}
                )
                return result

        except Exception as e:
            self.logger.debug_error(e, "execute_single_task")
            process.status = "error"
            error_msg = str(e)
            self.logger.error(
                f"❌ Error executing Claude process {task.get('id', 'unknown')}: {error_msg}"
            )

            result = {
                "task_id": task.get("id", "unknown"),
                "status": "error",
                "error": error_msg,
                "traceback": traceback.format_exc(),
            }
            self.logger.debug_exit(
                "execute_single_task", result={"status": "error", "error": error_msg}
            )
            return result

        finally:
            # Cleanup worktree
            try:
                self.logger.debug_step("Cleaning up worktree")
                self.worktree_manager.cleanup(task["id"])
            except Exception as e:
                self.logger.debug_error(e, "worktree cleanup")

    async def execute_parallel_tasks(
        self, tasks: List[Dict[str, Any]], max_parallel: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with real Claude Code processes"""

        self.logger.debug_enter(
            "execute_parallel_tasks", num_tasks=len(tasks), max_parallel=max_parallel
        )

        # Limit parallel execution to available tokens
        max_parallel = max_parallel or self.token_pool.get_token_count()

        self.logger.info(
            f"\n🚀 Starting {len(tasks)} Claude processes with up to {max_parallel} parallel"
        )
        print("=" * 60)

        # Create semaphore for rate limiting
        self.logger.debug_step(f"Creating semaphore with limit {max_parallel}")
        semaphore = asyncio.Semaphore(max_parallel)

        async def execute_with_semaphore(task):
            self.logger.debug_step(f"Acquiring semaphore for task {task.get('id')}")
            async with semaphore:
                self.logger.debug_step(f"Semaphore acquired for task {task.get('id')}")
                return await self.execute_single_task(task)

        # Execute all tasks in parallel (limited by semaphore)
        self.logger.debug_step("Starting parallel execution with asyncio.gather")
        try:
            results = await asyncio.gather(
                *[execute_with_semaphore(task) for task in tasks], return_exceptions=True
            )
            self.logger.debug_step(f"All tasks completed, got {len(results)} results")
        except Exception as e:
            self.logger.debug_error(e, "asyncio.gather")
            raise

        # Process results
        self.logger.debug_step("Processing results")
        processed_results = []
        for i, result in enumerate(results):
            self.logger.debug_data(f"result_{i}_type", type(result).__name__)

            if isinstance(result, Exception):
                error_msg = str(result)
                self.logger.debug_error(result, f"task {i}")
                processed_results.append(
                    {
                        "task_id": tasks[i]["id"] if i < len(tasks) else f"unknown_{i}",
                        "status": "exception",
                        "error": error_msg,
                        "traceback": traceback.format_exception(
                            type(result), result, result.__traceback__
                        ),
                    }
                )
            else:
                processed_results.append(result)

        # Summary
        successful = sum(1 for r in processed_results if r.get("status") == "completed")
        failed = len(processed_results) - successful

        print("=" * 60)
        self.logger.info(f"📊 All Claude processes complete: {successful}/{len(tasks)} successful")

        self.logger.debug_data(
            "summary",
            {
                "total": len(tasks),
                "successful": successful,
                "failed": failed,
                "results": [
                    {"id": r.get("task_id"), "status": r.get("status")} for r in processed_results
                ],
            },
        )

        self.logger.debug_exit(
            "execute_parallel_tasks", result=f"{successful}/{len(tasks)} successful"
        )
        return processed_results


async def demo_real_claude_execution():
    """Demonstrate real Claude Code execution with HECATON"""

    logger = get_logger("demo")
    logger.debug_enter("demo_real_claude_execution")

    # Import HECATON components
    from hecaton.resources.token_pool import TokenPool
    from hecaton.resources.worktree_fixed import WorktreeManager

    print("\n" + "=" * 60)
    print("HECATON REAL CLAUDE CODE EXECUTION DEMO (DEBUG MODE)")
    print("=" * 60)

    # Initialize resources
    logger.debug_step("Initializing resources")
    token_pool = TokenPool()
    worktree_manager = WorktreeManager()

    print("\n📦 Resources initialized:")
    print(f"   - Tokens available: {token_pool.get_token_count()}")
    print(f"   - Worktree base: {worktree_manager.base_path}")

    # Create executor
    logger.debug_step("Creating executor")
    executor = RealClaudeSubprocessExecutor(token_pool, worktree_manager)

    # Define demo tasks
    demo_tasks = [
        {
            "id": "task-1",
            "prompt": (
                "Create a simple Python function that calculates "
                "fibonacci numbers and save it to fib.py"
            ),
        },
        {
            "id": "task-2",
            "prompt": "Create a test file test_fib.py that tests the fibonacci function",
        },
        {"id": "task-3", "prompt": "Create a README.md explaining the fibonacci implementation"},
    ]

    print(f"\n🎯 Executing {len(demo_tasks)} tasks with real Claude processes...")

    # Execute in parallel
    results = await executor.execute_parallel_tasks(demo_tasks, max_parallel=3)

    # Show results
    print("\n📋 Results:")
    for result in results:
        status_icon = "✅" if result["status"] == "completed" else "❌"
        print(f"{status_icon} {result['task_id']}: {result['status']}")
        if result.get("error"):
            print(f"   Error: {result['error']}")

    logger.debug_exit("demo_real_claude_execution")
    return results


if __name__ == "__main__":
    # Run the demo
    print("🔧 Debug mode enabled - check logs for detailed execution trace")
    asyncio.run(demo_real_claude_execution())
