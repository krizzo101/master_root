"""
Real Claude Code Executor using subprocess to spawn actual Claude instances
This spawns REAL Claude Code processes using the CLI
"""

import asyncio
import json
import os
import subprocess
import uuid

# Unused imports kept for future use
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import required components for parallel execution
from ..resources.secure_token_pool import SecureTokenPool
from ..resources.worktree import WorktreeManager

# Import comprehensive command factory
from .claude_command_factory import (
    AgentProfile,
    ClaudeCommandFactory,
    CommandConfig,
    PermissionMode,
    TaskComplexity,
)


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
    Executes tasks using REAL Claude Code subprocesses.
    This spawns actual 'claude' CLI processes with proper tokens.
    """

    def __init__(
        self, token_pool, worktree_manager, debug_mode: bool = False, debug_logger=None
    ):
        """
        Initialize with token pool and worktree manager.

        Args:
            token_pool: Token pool for managing Claude tokens
            worktree_manager: Manager for git worktrees
            debug_mode: Enable debug mode for Claude agents (30% slower but detailed logs)
            debug_logger: Logger instance for capturing debug output
        """
        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.active_processes: Dict[str, ClaudeProcess] = {}
        self.command_factory = ClaudeCommandFactory()
        self.debug_mode = debug_mode
        self.debug_logger = debug_logger

        # Check if app-wide debug is enabled via environment
        if os.environ.get("HECATON_DEBUG", "").lower() in ["true", "1", "yes"]:
            self.debug_mode = True
            if self.debug_logger:
                self.debug_logger.info(
                    "HECATON_DEBUG enabled - Claude agents will run with -d flag"
                )

    async def execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with a real Claude Code subprocess"""

        # Get resources
        token, token_idx = self.token_pool.acquire()
        # Use provided worktree if available, otherwise create new one
        worktree = task.get("worktree") or self.worktree_manager.create(task["id"])

        # Create process tracking
        process = ClaudeProcess(
            id=task["id"],
            task=task.get("prompt", task.get("description", "")),
            token=token,
            worktree=worktree,
        )
        self.active_processes[process.id] = process

        try:
            # Determine task complexity and profile
            prompt_length = len(process.task)
            complexity = TaskComplexity.SIMPLE
            profile = AgentProfile.SPEED_DEMON

            if (
                prompt_length > 500
                or "implement" in process.task.lower()
                or "create" in process.task.lower()
            ):
                complexity = TaskComplexity.NORMAL
                profile = AgentProfile.PRODUCTION

            if (
                "architecture" in process.task.lower()
                or "design" in process.task.lower()
                or prompt_length > 2000
            ):
                complexity = TaskComplexity.COMPLEX
                profile = AgentProfile.QUALITY_CHAMPION

            # Override with explicit task settings
            if task.get("complexity"):
                complexity = TaskComplexity[task["complexity"].upper()]
            if task.get("profile"):
                profile = AgentProfile[task["profile"].upper()]

            # Build command configuration
            # Generate proper UUID for Claude session ID
            session_uuid = str(uuid.uuid4())

            config = CommandConfig(
                model=task.get(
                    "model", "sonnet" if complexity == TaskComplexity.SIMPLE else "opus"
                ),
                profile=profile,
                complexity=complexity,
                session_id=session_uuid,  # Use proper UUID
                agent_role=task.get("role", task.get("agent_type")),
                system_prompt=task.get("system_prompt"),
                workspace_dirs=[Path(worktree)],
                allowed_tools=task.get(
                    "allowed_tools", ["Write", "Read", "Edit", "Bash", "TodoWrite"]
                ),
                debug=self.debug_mode
                or task.get(
                    "debug", False
                ),  # Enable debug if app-wide or task-specific
                capture_debug_output=self.debug_logger is not None,
            )

            # Build optimized command using factory
            cmd = self.command_factory.build_command(process.task, config)

            # Handle long prompts via stdin or file
            use_stdin = len(process.task) > 1000 or "\n" in process.task
            if use_stdin:
                # Remove the "@-" sentinel from command - we'll pipe via stdin
                cmd = [arg for arg in cmd if arg != "@-"]
                # Will provide prompt via stdin
            # else: short prompt already added by command factory

            # Prepare environment
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token
            # CRITICAL: Remove ANTHROPIC_API_KEY entirely
            env.pop("ANTHROPIC_API_KEY", None)

            # Log execution details
            print(f"🤖 Starting Claude process for {process.id} with token {token_idx}")
            print(
                f"   Profile: {config.profile.value} (est. {self.command_factory.get_performance_estimate(config)})"
            )
            print(f"   Command: {' '.join(cmd)}")
            print(f"   Working directory: {worktree}")
            if config.debug:
                print(f"   🐛 Debug mode enabled (30% slower)")

            # Log to debug logger if available
            if self.debug_logger:
                self.debug_logger.info(f"Starting Claude agent {process.id}")
                self.debug_logger.debug(f"Command: {' '.join(cmd)}")
                self.debug_logger.debug(f"Profile: {config.profile.value}")
                self.debug_logger.debug(f"Complexity: {config.complexity.value}")
                self.debug_logger.debug(f"Model: {config.model}")
                self.debug_logger.debug(f"Debug mode: {config.debug}")

            # Start the subprocess
            process.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if use_stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(worktree),
                env=env,
            )

            process.status = "running"

            # If debug logging is enabled, capture output in real-time
            if config.debug and self.debug_logger:
                # Create tasks for reading stdout and stderr concurrently
                async def read_stream(stream, stream_name):
                    output_lines = []
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        decoded_line = line.decode("utf-8", errors="replace")
                        output_lines.append(decoded_line)
                        self.debug_logger.debug(
                            f"[{process.id}/{stream_name}] {decoded_line.rstrip()}"
                        )
                    return "".join(output_lines)

                # Read both streams concurrently
                stdout_task = asyncio.create_task(
                    read_stream(process.process.stdout, "stdout")
                )
                stderr_task = asyncio.create_task(
                    read_stream(process.process.stderr, "stderr")
                )

                # Wait for process completion with timeout
                try:
                    await asyncio.wait_for(process.process.wait(), timeout=1800)
                    process.stdout = await stdout_task
                    process.stderr = await stderr_task
                except asyncio.TimeoutError:
                    process.process.terminate()
                    await process.process.wait()
                    raise TimeoutError(f"Task timed out after 1800s")
            else:
                # Standard execution without real-time capture
                if use_stdin:
                    stdout, stderr = await asyncio.wait_for(
                        process.process.communicate(input=process.task.encode()),
                        timeout=1800,  # 30 minutes
                    )
                else:
                    stdout, stderr = await asyncio.wait_for(
                        process.process.communicate(), timeout=1800  # 30 minutes
                    )
                process.stdout = stdout.decode() if stdout else ""
                process.stderr = stderr.decode() if stderr else ""

            if process.process.returncode == 0:
                process.status = "completed"

                # Try to parse JSON output
                try:
                    process.result = json.loads(process.stdout)
                except json.JSONDecodeError:
                    process.result = {"output": process.stdout}

                print(f"✅ Claude process {process.id} completed successfully")

                return {
                    "task_id": task["id"],
                    "status": "completed",
                    "process_id": process.id,
                    "output": process.stdout,
                    "result": process.result,
                }
            else:
                process.status = "failed"
                error_msg = (
                    process.stderr
                    or f"Process exited with code {process.process.returncode}"
                )
                print(f"❌ Claude process {process.id} failed: {error_msg}")

                return {
                    "task_id": task["id"],
                    "status": "failed",
                    "process_id": process.id,
                    "error": error_msg,
                    "stderr": process.stderr,
                }

        except Exception as e:
            process.status = "error"
            print(f"❌ Error executing Claude process {process.id}: {e}")

            return {
                "task_id": task["id"],
                "status": "error",
                "process_id": process.id,
                "error": str(e),
            }

        finally:
            # Cleanup worktree
            self.worktree_manager.cleanup(task["id"])

    async def execute_parallel_tasks(
        self, tasks: List[Dict[str, Any]], max_parallel: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with real Claude Code processes"""

        # Limit parallel execution to available tokens
        max_parallel = max_parallel or self.token_pool.get_token_count()

        print(
            f"\n🚀 Starting {len(tasks)} Claude processes with up to {max_parallel} parallel"
        )
        print("=" * 60)

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_parallel)

        async def execute_with_semaphore(task):
            async with semaphore:
                return await self.execute_single_task(task)

        # Execute all tasks in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks], return_exceptions=True
        )

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "task_id": tasks[i]["id"],
                        "status": "exception",
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)

        # Summary
        successful = sum(1 for r in processed_results if r.get("status") == "completed")
        # failed = len(processed_results) - successful  # For future use

        print("=" * 60)
        print(f"📊 All Claude processes complete: {successful}/{len(tasks)} successful")

        return processed_results

    async def execute_parallel_improvements(
        self, improvement_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute parallel improvements with real Claude Code instances.
        Supports up to 15 parallel agents.

        Args:
            improvement_tasks: List of improvement task dictionaries with 'id' and 'prompt'

        Returns:
            Dictionary mapping task_id to output/results
        """
        # Validate we can handle the requested parallel execution
        max_agents = 15
        if len(improvement_tasks) > max_agents:
            print(
                f"⚠️ Warning: Limiting to {max_agents} agents (got {len(improvement_tasks)} tasks)"
            )
            improvement_tasks = improvement_tasks[:max_agents]

        print(
            f"\n🚀 Starting parallel improvements with {len(improvement_tasks)} Claude agents"
        )
        print("=" * 60)

        # Initialize resources if not already done
        if not hasattr(self, "token_pool") or not hasattr(self, "worktree_manager"):
            print("Initializing SecureTokenPool and WorktreeManager...")
            self.token_pool = SecureTokenPool()
            self.worktree_manager = WorktreeManager()

        # Prepare results dictionary
        results_dict = {}

        # Create async tasks for parallel execution
        async_tasks = []

        for task in improvement_tasks:
            # Ensure task has required fields
            if "id" not in task:
                task["id"] = f"task-{len(async_tasks)+1}"
            if "prompt" not in task and "description" in task:
                task["prompt"] = task["description"]

            # Add system prompt for specialization if not provided
            if "system_prompt" not in task and "agent_type" in task:
                agent_prompts = {
                    "researcher": "You are a research specialist. Find and analyze relevant information thoroughly.",
                    "coder": "You are an expert developer. Write clean, efficient, production-ready code.",
                    "tester": "You are a QA specialist. Write comprehensive tests covering edge cases.",
                    "reviewer": "You are a senior reviewer. Provide detailed, constructive feedback.",
                    "architect": "You are a system architect. Design scalable, maintainable solutions.",
                }
                task["system_prompt"] = agent_prompts.get(
                    task["agent_type"], "You are an expert assistant."
                )

            # Get token and worktree for this agent
            token = self.token_pool.acquire()
            worktree = self.worktree_manager.create(task["id"])

            # Create async task for subprocess execution
            async_task = self._execute_claude_subprocess(
                task_id=task["id"],
                prompt=task.get("prompt", ""),
                token=token,
                worktree=worktree,
                system_prompt=task.get("system_prompt"),
                model=task.get("model", "sonnet"),
            )
            async_tasks.append(async_task)

        try:
            # Execute all tasks in parallel with 30-minute timeout
            results = await asyncio.wait_for(
                asyncio.gather(*async_tasks, return_exceptions=True),
                timeout=1800,  # 30 minutes
            )

            # Process results into dictionary
            for i, result in enumerate(results):
                task_id = improvement_tasks[i]["id"]

                if isinstance(result, Exception):
                    results_dict[task_id] = {
                        "status": "error",
                        "error": str(result),
                        "output": None,
                    }
                    print(f"❌ Agent {task_id} failed with exception: {result}")
                else:
                    results_dict[task_id] = result
                    status_icon = "✅" if result.get("status") == "completed" else "❌"
                    print(
                        f"{status_icon} Agent {task_id}: {result.get('status', 'unknown')}"
                    )

        except asyncio.TimeoutError:
            print("⏰ Timeout reached for parallel execution (30 minutes)")
            results_dict["_timeout"] = True

        except Exception as e:
            print(f"❌ Error during parallel execution: {e}")
            results_dict["_error"] = str(e)

        finally:
            # Cleanup all worktrees
            for task in improvement_tasks:
                try:
                    self.worktree_manager.cleanup(task["id"])
                except:
                    pass  # Best effort cleanup

        # Summary
        successful = sum(
            1
            for v in results_dict.values()
            if isinstance(v, dict) and v.get("status") == "completed"
        )
        total = len([k for k in results_dict.keys() if not k.startswith("_")])

        print("=" * 60)
        print(f"📊 Parallel execution complete: {successful}/{total} agents successful")

        return results_dict

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for executing a task with real Claude.
        This is the method called by other components.

        Args:
            task: Dictionary with 'id', 'prompt' or 'description', and optional 'model'

        Returns:
            Dictionary with execution results
        """
        return await self.execute_single_task(task)

    async def _execute_claude_subprocess(
        self,
        task_id: str,
        prompt: str,
        token: str,
        worktree: Path,
        system_prompt: str = None,
        model: str = "sonnet",
    ) -> Dict[str, Any]:
        """
        Helper method to execute a single Claude subprocess.

        Args:
            task_id: Unique identifier for the task
            prompt: The prompt/task description
            token: Claude Code API token
            worktree: Working directory for this agent
            system_prompt: Optional system prompt to append for agent specialization
            model: Model to use (sonnet for speed, opus for quality)

        Returns:
            Dictionary with execution results
        """
        try:
            # Write task to file
            task_file = Path(worktree) / "task.txt"
            with open(task_file, "w") as f:
                f.write(prompt)

            # Prepare environment
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token
            # CRITICAL: Remove ANTHROPIC_API_KEY entirely
            env.pop("ANTHROPIC_API_KEY", None)

            # Build optimized headless command
            cmd = [
                "claude",
                "-p",  # Print/headless mode (non-interactive)
                f"@{task_file}",
                "--output-format",
                "json",
                "--model",
                model,  # Use specified model
                "--session-id",
                str(uuid.uuid4()),  # Valid UUID for session
            ]

            # Add permission mode (always use plan for safety in headless)
            permission_mode = task.get("permission_mode", "plan")
            cmd.extend(["--permission-mode", permission_mode])

            # Add MCP config if specified (e.g., for research agents)
            mcp_profile = task.get("mcp_profile")
            if mcp_profile:
                mcp_config_path = (
                    Path(__file__).parent.parent
                    / "config"
                    / "minimal_profiles"
                    / f"{mcp_profile}.json"
                )
                if mcp_config_path.exists():
                    cmd.extend(["--mcp-config", str(mcp_config_path)])

            # Add allowed tools (constrain what agents can do)
            allowed_tools = task.get("allowed_tools", ["Read", "Write", "Edit"])
            if allowed_tools:
                cmd.extend(["--allowedTools", ",".join(allowed_tools)])

            # Add system prompt if provided
            if system_prompt:
                cmd.extend(["--append-system-prompt", system_prompt])
            else:
                # Default concise behavior for speed
                cmd.extend(
                    [
                        "--append-system-prompt",
                        "Be concise. Focus on the task. Include error handling.",
                    ]
                )

            print(f"🤖 Starting Claude agent {task_id} in {worktree}")

            # Run subprocess (using asyncio's subprocess for async execution)
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                cwd=str(worktree),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion
            stdout, stderr = await process.communicate()

            # Process results
            if process.returncode == 0:
                return {
                    "status": "completed",
                    "output": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "returncode": 0,
                }
            else:
                return {
                    "status": "failed",
                    "output": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "returncode": process.returncode,
                    "error": f"Process exited with code {process.returncode}",
                }

        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}


async def demo_real_claude_execution():
    """Demonstrate real Claude Code execution with HECATON"""

    # Import HECATON components
    from hecaton.resources.token_pool import TokenPool
    from hecaton.resources.worktree import WorktreeManager

    print("\n" + "=" * 60)
    print("HECATON REAL CLAUDE CODE EXECUTION DEMO")
    print("=" * 60)

    # Initialize resources
    token_pool = TokenPool()
    worktree_manager = WorktreeManager()

    print("\n📦 Resources initialized:")
    print(f"   - Tokens available: {token_pool.get_token_count()}")
    print(f"   - Worktree base: {worktree_manager.base_path}")

    # Create executor
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
        {
            "id": "task-3",
            "prompt": "Create a README.md explaining the fibonacci implementation",
        },
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

    return results


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_real_claude_execution())
