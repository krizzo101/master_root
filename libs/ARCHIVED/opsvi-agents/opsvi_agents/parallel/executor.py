"""Parallel agent executor for concurrent execution."""

import asyncio
import concurrent.futures
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import structlog

from ..core import AgentConfig, AgentResult, BaseAgent

logger = structlog.get_logger(__name__)


@dataclass
class ParallelTask:
    """Task for parallel execution."""

    agent: BaseAgent
    prompt: str
    kwargs: Dict[str, Any]
    task_id: str


@dataclass
class ParallelResult:
    """Result from parallel execution."""

    results: List[AgentResult]
    total_duration: float
    success_count: int
    failure_count: int


class ParallelAgentExecutor:
    """Execute multiple agents in parallel."""

    def __init__(self, max_workers: int = 5):
        """Initialize parallel executor."""
        self.max_workers = max_workers
        self._logger = logger.bind(component="ParallelAgentExecutor")

    def execute_parallel(
        self, tasks: List[Union[ParallelTask, tuple]]
    ) -> ParallelResult:
        """Execute agents in parallel (synchronous)."""
        start_time = time.time()
        results = []

        # Convert tuples to ParallelTask if needed
        parallel_tasks = []
        for i, task in enumerate(tasks):
            if isinstance(task, tuple):
                agent, prompt = task[:2]
                kwargs = task[2] if len(task) > 2 else {}
                task = ParallelTask(agent, prompt, kwargs, f"task_{i}")
            parallel_tasks.append(task)

        # Execute in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._execute_task, task): task
                for task in parallel_tasks
            }

            # Collect results
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self._logger.error(
                        "Task failed", task_id=task.task_id, error=str(e)
                    )
                    # Create failed result
                    failed_result = AgentResult(
                        success=False,
                        output=None,
                        context=task.agent.context,
                        error=str(e),
                    )
                    results.append(failed_result)

        # Calculate metrics
        total_duration = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        self._logger.info(
            "Parallel execution completed",
            total_tasks=len(tasks),
            success=success_count,
            failed=failure_count,
            duration=total_duration,
        )

        return ParallelResult(
            results=results,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        )

    def _execute_task(self, task: ParallelTask) -> AgentResult:
        """Execute single task."""
        self._logger.debug("Executing task", task_id=task.task_id)
        return task.agent.execute(task.prompt, **task.kwargs)

    def execute_batch(
        self, agent: BaseAgent, prompts: List[str], shared_kwargs: Dict[str, Any] = None
    ) -> ParallelResult:
        """Execute same agent with multiple prompts."""
        tasks = [
            ParallelTask(agent, prompt, shared_kwargs or {}, f"batch_{i}")
            for i, prompt in enumerate(prompts)
        ]
        return self.execute_parallel(tasks)

    def execute_pipeline(self, stages: List[Dict[str, Any]]) -> List[AgentResult]:
        """Execute agents in pipeline (sequential stages, parallel within stage)."""
        all_results = []

        for i, stage in enumerate(stages):
            self._logger.info(f"Executing pipeline stage {i+1}/{len(stages)}")

            # Get tasks for this stage
            stage_tasks = stage.get("tasks", [])

            # Execute stage in parallel
            stage_results = self.execute_parallel(stage_tasks)

            # Check if stage should halt on failure
            if stage.get("halt_on_failure", False) and stage_results.failure_count > 0:
                self._logger.warning(f"Pipeline halted at stage {i+1} due to failures")
                break

            # Pass results to next stage if configured
            if stage.get("pass_results", False) and i < len(stages) - 1:
                # Add results to next stage's tasks
                for task in stages[i + 1].get("tasks", []):
                    if isinstance(task, ParallelTask):
                        task.kwargs["previous_results"] = stage_results.results

            all_results.extend(stage_results.results)

        return all_results


def create_parallel_executor(max_workers: int = 5) -> ParallelAgentExecutor:
    """Create parallel executor instance."""
    return ParallelAgentExecutor(max_workers=max_workers)
