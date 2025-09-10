#!/usr/bin/env python3
"""
Task Scheduler Component
Handles task scheduling, dependency management, and parallel execution control
"""

import asyncio
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Generic agent task definition with enhanced error tracking and project organization"""

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
    quality_gates: List[str] = field(default_factory=list)
    raw_output: Optional[str] = None
    error_details: Optional[Dict] = None
    work_dir_name: Optional[str] = None
    system_prompt: Optional[str] = None
    system_prompt_file: Optional[str] = None
    enhancement_level: Optional[int] = None

    # Project organization fields
    project_location: Optional[str] = None
    deliverable_structure: Optional[Dict[str, str]] = field(default_factory=dict)
    directory_permissions: Optional[List[str]] = field(default_factory=list)
    output_validation: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary with error details"""
        result = asdict(self)
        if self.raw_output and len(self.raw_output) > 1000:
            result["raw_output"] = (
                self.raw_output[:500] + "..." + self.raw_output[-500:]
            )
        return result


class DependencyManager:
    """Manages task dependencies and execution order"""

    def __init__(self):
        self.completed: Set[str] = set()
        self.running: Set[str] = set()
        self.failed: Set[str] = set()
        self.lock = asyncio.Lock()

    async def can_run(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        async with self.lock:
            if task.task_id in self.running or task.task_id in self.completed:
                return False

            for dep in task.dependencies:
                if dep not in self.completed:
                    return False

            return True

    async def mark_running(self, task_id: str):
        """Mark task as running"""
        async with self.lock:
            self.running.add(task_id)

    async def mark_completed(self, task_id: str):
        """Mark task as completed"""
        async with self.lock:
            self.running.discard(task_id)
            self.completed.add(task_id)

    async def mark_failed(self, task_id: str):
        """Mark task as failed"""
        async with self.lock:
            self.running.discard(task_id)
            self.failed.add(task_id)

    async def get_status(self) -> Dict[str, Set[str]]:
        """Get current status of all tasks"""
        async with self.lock:
            return {
                "completed": self.completed.copy(),
                "running": self.running.copy(),
                "failed": self.failed.copy(),
            }

    async def reset(self):
        """Reset all task states"""
        async with self.lock:
            self.completed.clear()
            self.running.clear()
            self.failed.clear()


class TokenPool:
    """Manages API tokens for parallel execution"""

    def __init__(self, tokens: List[str] = None):
        if tokens is not None:
            self.tokens = [t for t in tokens if t and t.strip()]
        else:
            self.tokens = self._get_tokens_from_tool()

        if not self.tokens:
            raise RuntimeError("No tokens available. Cannot proceed without TokenTool.")

        self.current_index = 0
        self.lock = asyncio.Lock()
        self.in_use: Set[int] = set()

        logger.info(f"TokenPool initialized with {len(self.tokens)} tokens")

    def _get_tokens_from_tool(self) -> List[str]:
        """Get tokens from TokenTool"""
        import json
        import subprocess

        try:
            result = subprocess.run(
                ["python", "-m", "token_tool", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            tokens = json.loads(result.stdout).get("tokens", [])
            return tokens
        except Exception as e:
            logger.error(f"Failed to get tokens from TokenTool: {e}")
            return []

    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin)"""
        async with self.lock:
            token = self.tokens[self.current_index]
            token_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(self.tokens)
            self.in_use.add(token_idx)
            return token, token_idx

    def release(self, token_idx: int):
        """Release a token back to the pool"""
        if token_idx in self.in_use:
            self.in_use.discard(token_idx)
            logger.debug(f"Released token index {token_idx}")

    def size(self) -> int:
        """Get total number of tokens"""
        return len(self.tokens)

    @property
    def available(self) -> int:
        """Get number of available tokens"""
        return len(self.tokens) - len(self.in_use)


class TaskScheduler:
    """
    Manages task scheduling, dependencies, and parallel execution
    Extracted from GenericOrchestrator
    """

    def __init__(
        self,
        max_parallel: int = 10,
        tokens: List[str] = None,
        output_dir: Optional[Path] = None,
    ):
        self.max_parallel = max(1, max_parallel if max_parallel is not None else 10)
        self.token_pool = TokenPool(tokens)
        self.dep_manager = DependencyManager()
        self.output_dir = output_dir or Path(".")

        # Task tracking
        self.tasks: Dict[str, AgentTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.execution_semaphore = asyncio.Semaphore(self.max_parallel)

        logger.info(f"TaskScheduler initialized with max_parallel={self.max_parallel}")

    def add_task(self, task: AgentTask):
        """Add a task to the scheduler"""
        self.tasks[task.task_id] = task
        logger.debug(f"Added task {task.task_id} with dependencies {task.dependencies}")

    async def schedule_tasks(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Schedule tasks respecting dependencies"""
        # Add all tasks
        for task in tasks:
            self.add_task(task)

        # Create execution order based on dependencies
        scheduled = []
        pending = set(task.task_id for task in tasks)

        while pending:
            ready_tasks = []
            for task_id in pending:
                task = self.tasks[task_id]
                if await self.dep_manager.can_run(task):
                    ready_tasks.append(task)

            if not ready_tasks:
                # Check for circular dependencies
                if pending:
                    logger.error(f"Circular dependency detected in tasks: {pending}")
                    break

            for task in ready_tasks:
                scheduled.append(task)
                pending.discard(task.task_id)
                await self.dep_manager.mark_completed(task.task_id)

        # Reset dependency manager for actual execution
        await self.dep_manager.reset()

        return scheduled

    async def get_next_runnable_tasks(
        self, batch_size: Optional[int] = None
    ) -> List[AgentTask]:
        """Get next batch of runnable tasks"""
        runnable = []
        batch_size = batch_size or self.max_parallel

        for task_id, task in self.tasks.items():
            if len(runnable) >= batch_size:
                break

            if task.status == "pending" and await self.dep_manager.can_run(task):
                runnable.append(task)

        return runnable

    async def mark_task_running(self, task_id: str):
        """Mark a task as running"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "running"
            self.tasks[task_id].start_time = datetime.now().timestamp()
            await self.dep_manager.mark_running(task_id)

    async def mark_task_completed(self, task_id: str, result: Optional[Dict] = None):
        """Mark a task as completed"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "completed"
            task.end_time = datetime.now().timestamp()
            task.result = result
            await self.dep_manager.mark_completed(task_id)

    async def mark_task_failed(
        self, task_id: str, error: str, error_details: Optional[Dict] = None
    ):
        """Mark a task as failed"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "failed"
            task.end_time = datetime.now().timestamp()
            task.error = error
            task.error_details = error_details
            await self.dep_manager.mark_failed(task_id)

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[AgentTask]:
        """Get all tasks"""
        return list(self.tasks.values())

    def get_task_stats(self) -> Dict[str, int]:
        """Get task statistics"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }

        for task in self.tasks.values():
            stats[task.status] += 1

        return stats

    async def wait_for_available_slot(self) -> bool:
        """Wait for an execution slot to become available"""
        await self.execution_semaphore.acquire()
        return True

    def release_execution_slot(self):
        """Release an execution slot"""
        self.execution_semaphore.release()

    async def acquire_token(self) -> Tuple[str, int]:
        """Acquire a token for task execution"""
        return await self.token_pool.acquire()

    def release_token(self, token_idx: int):
        """Release a token back to the pool"""
        self.token_pool.release(token_idx)

    def get_token_stats(self) -> Dict[str, int]:
        """Get token pool statistics"""
        return {
            "total": self.token_pool.size(),
            "available": self.token_pool.available,
            "in_use": self.token_pool.size() - self.token_pool.available,
        }
