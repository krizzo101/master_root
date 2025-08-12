"""
Orchestration Engine for Multi-Agent Workflow Execution
Uses Langgraph to build and execute the agent workflow graph.
"""
import asyncio
from loguru import logger
from typing import Any, Dict, List
from rich.progress import Progress
from multiagent_cli.input_parser import InputModel
from multiagent_cli.agent_manager import AgentManager
from multiagent_cli.config import AppConfig


class OrchestrationEngine:
    """
    Interprets validated input, builds the agent workflow, manages execution flows.
    """

    def __init__(self, input_data: InputModel, config: AppConfig, logger_inst):
        self.input = input_data
        self.config = config
        self.logger = logger_inst
        self.agent_manager = AgentManager(config, logger_inst)
        self.task_outputs = {}  # task_id: output
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self, progress: Progress, progress_task: int) -> Dict[str, Any]:
        """
        Synchronously runs the orchestration workflow with progress reporting.
        Returns a dictionary of all agent task outputs.
        """
        try:
            result = self.loop.run_until_complete(
                self._run_all(progress, progress_task)
            )
            return result
        finally:
            for t in asyncio.all_tasks(self.loop):
                t.cancel()
            self.loop.close()

    async def _run_all(self, progress: Progress, progress_task: int) -> Dict[str, Any]:
        workloads = self.input.workloads
        total_tasks = sum(len(w.tasks) for w in workloads)
        completed_tasks = 0
        # Schedule all workloads serially (could parallelize if needed)
        for workload in workloads:
            self.logger.info(
                f"Scheduling workload '{workload.name}' with {len(workload.tasks)} task(s)"
            )
            # Build dependency graph (task_id -> depends_on ids)
            tasks = {f"{workload.name}:{i}": t for i, t in enumerate(workload.tasks)}
            dependency_graph = {tid: t.depends_on for tid, t in tasks.items()}
            # Keep track of completed task ids for this workload
            task_outputs = {}
            pending = set(tasks)
            while pending:
                for tid in list(pending):
                    deps = [f"{workload.name}:{dep}" for dep in tasks[tid].depends_on]
                    if all(d in task_outputs or d not in tasks for d in deps):
                        task = tasks[tid]
                        self.logger.info(
                            f"Dispatching agent '{task.agent}' for task '{tid}' ({task.type})"
                        )
                        output = await self.agent_manager.run_agent_task(
                            agent_name=task.agent,
                            task_type=task.type,
                            task_input=task.input,
                            context={
                                "depends_on_outputs": [
                                    task_outputs.get(d)
                                    for d in deps
                                    if d in task_outputs
                                ]
                            },
                        )
                        task_outputs[tid] = output
                        pending.remove(tid)
                        completed_tasks += 1
                        progress.update(
                            progress_task,
                            completed=completed_tasks * 100 // total_tasks
                            if total_tasks > 0
                            else 1,
                        )
                    else:
                        # Not all dependencies are satisfied yet
                        continue
            self.task_outputs.update(task_outputs)
        return self.task_outputs
