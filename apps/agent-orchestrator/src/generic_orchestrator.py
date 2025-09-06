#!/usr/bin/env python3
"""
Generic Agent Orchestrator Framework
A simplified, reusable orchestrator for parallel Claude agent execution
Extracted and simplified from Hecaton patterns
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Generic agent task definition"""

    task_id: str
    task_type: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class TokenPool:
    """Manages Claude API tokens for parallel execution"""

    def __init__(self, tokens: List[str] = None):
        # Handle None, empty list, or list with empty strings
        if tokens is not None:
            self.tokens = [t for t in tokens if t]  # Filter empty strings
        else:
            # Fall back to environment variable
            env_token = os.environ.get("CLAUDE_CODE_TOKEN", "")
            self.tokens = [env_token] if env_token else []

        self.current_index = 0
        self.lock = asyncio.Lock()

        # Ensure we have at least one valid token
        if not self.tokens:
            raise ValueError(
                "No Claude tokens available. Please set CLAUDE_CODE_TOKEN environment variable"
            )

        logger.info(f"Token pool initialized with {len(self.tokens)} tokens")

    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin)"""
        async with self.lock:
            token = self.tokens[self.current_index]
            token_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(self.tokens)
            return token, token_idx

    def size(self) -> int:
        return len(self.tokens)


class DependencyManager:
    """Manages task dependencies"""

    def __init__(self):
        self.completed: set = set()
        self.running: set = set()
        self.failed: set = set()
        self.lock = asyncio.Lock()

    async def can_run(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        async with self.lock:
            # Can't run if already running or completed
            if task.task_id in self.running or task.task_id in self.completed:
                return False

            # Check all dependencies are completed
            for dep in task.dependencies:
                if dep not in self.completed:
                    return False

            return True

    async def mark_running(self, task_id: str):
        async with self.lock:
            self.running.add(task_id)

    async def mark_completed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.completed.add(task_id)

    async def mark_failed(self, task_id: str):
        async with self.lock:
            self.running.discard(task_id)
            self.failed.add(task_id)


class MessageBus:
    """Simple file-based message passing between agents"""

    def __init__(self, message_dir: Path):
        self.message_dir = message_dir
        self.message_dir.mkdir(parents=True, exist_ok=True)

    async def send(self, from_id: str, to_id: str, message: Dict):
        """Send message from one agent to another"""
        msg_file = self.message_dir / f"{to_id}_{datetime.now().timestamp()}.json"
        msg_data = {
            "from": from_id,
            "to": to_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        msg_file.write_text(json.dumps(msg_data, indent=2))

    async def receive(self, agent_id: str) -> List[Dict]:
        """Get all messages for an agent"""
        messages = []
        for msg_file in self.message_dir.glob(f"{agent_id}_*.json"):
            messages.append(json.loads(msg_file.read_text()))
            msg_file.unlink()  # Delete after reading
        return sorted(messages, key=lambda x: x["timestamp"])


class GenericOrchestrator:
    """
    Generic orchestrator for parallel Claude agent execution.
    Can be customized for any use case by providing task generator and result processor.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Ensure subdirectories exist
        (self.output_dir / "tasks").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Handle None and invalid values
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)

        # Try to load tokens from encrypted storage if not provided
        if tokens is None:
            try:
                # Add both current and parent directory to path for imports
                import sys

                current_dir = str(Path(__file__).parent)
                parent_dir = str(Path(__file__).parent.parent)

                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)

                try:
                    from .token_loader import TokenLoader
                except ImportError:
                    # Fall back to direct import when not running as package
                    from token_loader import TokenLoader

                # Determine orchestrator type from context
                orchestrator_type = getattr(self, "_orchestrator_type", None)
                loader = TokenLoader(orchestrator_type=orchestrator_type)
                loaded_tokens = loader.load_tokens()
                if (
                    loaded_tokens and len(loaded_tokens) > 0
                ):  # Any tokens are good for coordinated execution
                    tokens = loaded_tokens
                    logger.info(
                        f"Loaded {len(tokens)} tokens from secure storage (type: {orchestrator_type})"
                    )
                else:
                    logger.warning(
                        f"Only got {len(loaded_tokens) if loaded_tokens else 0} "
                        f"tokens from secure storage, using fallback"
                    )

            except Exception as e:
                logger.warning(f"Could not load tokens from secrets: {e}")
                pass  # Fall back to default TokenPool behavior

        self.token_pool = TokenPool(tokens)
        self.dep_manager = DependencyManager()
        self.message_bus = MessageBus(output_dir / "messages")

        # Setup Claude command
        self.claude_cmd = ["claude", "-p"]

        if use_optimizations:
            # Apply performance optimizations with research tools
            research_config = Path.home() / ".claude_research.json"
            if not research_config.exists():
                # Include essential MCP servers for research while optimizing startup
                research_mcp_config = {
                    "mcpServers": {
                        "mcp_web_search": {
                            "command": "python",
                            "args": ["-m", "mcp_web_search"],
                        },
                        "research_papers": {
                            "command": "python",
                            "args": ["-m", "research_papers"],
                        },
                        "firecrawl": {"command": "python", "args": ["-m", "firecrawl"]},
                    }
                }
                research_config.write_text(json.dumps(research_mcp_config, indent=2))

            self.claude_cmd.extend(
                [
                    "--model",
                    "opus",  # Better for research quality
                    "--strict-mcp-config",
                    "--mcp-config",
                    str(research_config),
                    "--dangerously-skip-permissions",
                    "--output-format",
                    "json",
                ]
            )

        # Metrics
        self.metrics = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "total_duration": 0,
            "start_time": None,
            "end_time": None,
        }

        # Hooks for customization
        self.pre_execute_hook: Optional[Callable] = None
        self.post_execute_hook: Optional[Callable] = None
        self.task_builder_hook: Optional[Callable] = None

    async def execute_agent(self, task: AgentTask) -> Dict:
        """Execute a single agent task"""

        session_id = str(uuid.uuid4())

        # Pre-execution hook
        if self.pre_execute_hook:
            await self.pre_execute_hook(task)

        # Build full prompt
        if self.task_builder_hook:
            prompt = await self.task_builder_hook(task)
        else:
            prompt = task.prompt

        # Prepare command with role-specific system prompt
        cmd = self.claude_cmd.copy()

        # Add system prompt based on task type for better specialization
        system_prompts = {
            "analysis": "You are a specialized analysis agent. Focus on thorough, data-driven analysis. Provide clear, structured summaries with key metrics.",
            "monitoring": "You are a system monitoring agent. Focus on performance metrics, resource usage, and system health indicators. Be concise and actionable.",
            "research": "You are a research specialist. Focus on comprehensive information gathering, accurate citations, and structured findings.",
            "strategic_research_lead": "You are a strategic research commander. Plan and coordinate research operations. Focus on leadership, strategy, and optimal orchestration patterns.",
        }

        if task.task_type in system_prompts:
            cmd.extend(["--append-system-prompt", system_prompts[task.task_type]])

        # Add session and workspace parameters
        cmd.extend(
            [
                "--session-id",
                session_id,
                "--add-dir",
                str(self.output_dir),
                "--",  # Important: separator before prompt
                prompt,
            ]
        )

        # Get token
        token, token_idx = await self.token_pool.acquire()
        env = os.environ.copy()
        env["CLAUDE_CODE_TOKEN"] = token

        # Execute
        task.start_time = datetime.now().timestamp()
        task.status = "running"
        await self.dep_manager.mark_running(task.task_id)

        try:
            logger.info(f"Executing {task.task_id} ({task.task_type})")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            task.end_time = datetime.now().timestamp()
            duration = task.end_time - task.start_time

            if process.returncode == 0:
                task.status = "completed"
                task.result = json.loads(stdout.decode())
                await self.dep_manager.mark_completed(task.task_id)
                self.metrics["completed"] += 1

                logger.info(f"✓ {task.task_id} completed in {duration:.2f}s")
            else:
                task.status = "failed"
                task.error = stderr.decode()
                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1

                logger.error(f"✗ {task.task_id} failed: {task.error}")

            self.metrics["total_duration"] += duration

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            await self.dep_manager.mark_failed(task.task_id)
            self.metrics["failed"] += 1

            logger.error(f"✗ {task.task_id} exception: {e}")

        # Post-execution hook
        if self.post_execute_hook:
            await self.post_execute_hook(task)

        # Save task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        return task.to_dict()

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute a batch of tasks respecting dependencies and parallelism limits"""

        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()

        results = []

        while len(results) < len(tasks):
            # Find tasks ready to run
            ready_tasks = []
            for task in tasks:
                if task.status == "pending" and await self.dep_manager.can_run(task):
                    ready_tasks.append(task)

                    if len(ready_tasks) >= self.max_parallel:
                        break

            if not ready_tasks:
                # Check if we're stuck
                pending = [t for t in tasks if t.status == "pending"]
                if pending:
                    logger.warning(f"Possible deadlock: {len(pending)} tasks pending")
                    # Mark them as failed
                    for task in pending:
                        task.status = "failed"
                        task.error = "Dependencies not met"
                        results.append(task.to_dict())
                break

            # Execute ready tasks in parallel
            logger.info(f"Executing batch of {len(ready_tasks)} tasks")
            batch_results = await asyncio.gather(
                *[self.execute_agent(task) for task in ready_tasks],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch execution error: {result}")
                else:
                    results.append(result)

            # Brief pause between batches
            await asyncio.sleep(0.5)

        self.metrics["end_time"] = datetime.now().isoformat()

        return results

    async def run(
        self,
        task_generator: Callable[[], List[AgentTask]],
        result_processor: Optional[Callable[[List[Dict]], None]] = None,
    ) -> Dict:
        """
        Main entry point - run orchestration with custom task generator.

        Args:
            task_generator: Function that returns list of AgentTask objects
            result_processor: Optional function to process results

        Returns:
            Execution metrics and results
        """

        logger.info("=" * 60)
        logger.info("Generic Agent Orchestrator")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Max parallel: {self.max_parallel}")
        logger.info(f"Token pool size: {self.token_pool.size()}")
        logger.info("=" * 60)

        # Generate tasks
        tasks = task_generator()
        logger.info(f"Generated {len(tasks)} tasks")

        # Execute tasks
        results = await self.execute_batch(tasks)

        # Process results if processor provided
        if result_processor:
            await result_processor(results)

        # Print summary
        logger.info("=" * 60)
        logger.info("EXECUTION COMPLETE")
        logger.info(f"Total: {self.metrics['total']}")
        logger.info(f"Completed: {self.metrics['completed']}")
        logger.info(f"Failed: {self.metrics['failed']}")

        if self.metrics["completed"] > 0:
            avg_time = self.metrics["total_duration"] / self.metrics["completed"]
            logger.info(f"Avg time: {avg_time:.2f}s")

        logger.info("=" * 60)

        return {"metrics": self.metrics, "results": results}


# Example usage for testing
async def example_usage():
    """Example showing how to use the generic orchestrator"""

    def generate_test_tasks() -> List[AgentTask]:
        """Generate some test tasks"""
        tasks = []

        # Create some tasks with dependencies
        tasks.append(
            AgentTask(
                task_id="research_1",
                task_type="research",
                prompt="Research Python async patterns",
                dependencies=[],
            )
        )

        tasks.append(
            AgentTask(
                task_id="design_1",
                task_type="design",
                prompt="Design a simple async system",
                dependencies=["research_1"],  # Depends on research
            )
        )

        tasks.append(
            AgentTask(
                task_id="implement_1",
                task_type="implement",
                prompt="Implement a hello world async function",
                dependencies=["design_1"],  # Depends on design
            )
        )

        return tasks

    async def process_results(results: List[Dict]):
        """Process the results"""
        print("\nResults Summary:")
        for r in results:
            print(f"  {r['task_id']}: {r['status']}")

    # Create and run orchestrator
    import tempfile

    orchestrator = GenericOrchestrator(
        output_dir=Path(tempfile.mkdtemp(prefix="orchestrator_test_")), max_parallel=3
    )

    await orchestrator.run(
        task_generator=generate_test_tasks, result_processor=process_results
    )


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
