"""Supervisor agent for orchestrating other agents."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

from ..core import AgentCapability, AgentConfig, AgentResult, BaseAgent
from ..parallel import ParallelAgentExecutor, ParallelTask
from ..registry import registry as agent_registry

logger = structlog.get_logger(__name__)


@dataclass
class SubTask:
    """Sub-task for delegation."""

    task_id: str
    description: str
    assigned_agent: str
    dependencies: List[str] = None
    result: Optional[AgentResult] = None


class SupervisorAgent(BaseAgent):
    """Supervisor agent that orchestrates other agents."""

    def __init__(self, config: AgentConfig):
        """Initialize supervisor agent."""
        super().__init__(config)
        config.capabilities.append(AgentCapability.PLANNING)
        config.capabilities.append(AgentCapability.PARALLEL)
        self._logger = logger.bind(agent="SupervisorAgent")
        self._executor = ParallelAgentExecutor()
        self._subtasks: List[SubTask] = []
        self._worker_agents: Dict[str, BaseAgent] = {}

    def _execute(self, prompt: str, **kwargs) -> Any:
        """Execute by delegating to other agents."""
        # Decompose task into subtasks
        subtasks = self._decompose_task(prompt)
        self._subtasks = subtasks

        # Assign agents to subtasks
        self._assign_agents(subtasks)

        # Execute subtasks (respecting dependencies)
        results = self._execute_subtasks(subtasks)

        # Combine results
        final_result = self._combine_results(results)

        return final_result

    def _decompose_task(self, prompt: str) -> List[SubTask]:
        """Decompose main task into subtasks."""
        # In real implementation, use LLM to decompose
        # For now, create example subtasks

        subtasks = [
            SubTask(
                task_id="analyze",
                description=f"Analyze the requirements: {prompt}",
                assigned_agent="analyzer",
                dependencies=[],
            ),
            SubTask(
                task_id="implement",
                description=f"Implement the solution for: {prompt}",
                assigned_agent="developer",
                dependencies=["analyze"],
            ),
            SubTask(
                task_id="test",
                description=f"Test the implementation",
                assigned_agent="tester",
                dependencies=["implement"],
            ),
            SubTask(
                task_id="document",
                description=f"Document the solution",
                assigned_agent="documenter",
                dependencies=["implement"],
            ),
        ]

        return subtasks

    def _assign_agents(self, subtasks: List[SubTask]) -> None:
        """Assign agents to subtasks."""
        for subtask in subtasks:
            agent_name = subtask.assigned_agent

            # Get or create agent
            if agent_name not in self._worker_agents:
                if agent_name in agent_registry:
                    self._worker_agents[agent_name] = agent_registry.create(agent_name)
                else:
                    # Create generic agent with appropriate config
                    config = AgentConfig(name=agent_name, model=self.config.model)
                    # In real implementation, would create appropriate agent type
                    self._worker_agents[agent_name] = BaseAgent(config)

            self._logger.info(f"Assigned {agent_name} to task {subtask.task_id}")

    def _execute_subtasks(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Execute subtasks respecting dependencies."""
        completed = set()
        results = []

        while len(completed) < len(subtasks):
            # Find tasks ready to execute (dependencies met)
            ready_tasks = [
                task
                for task in subtasks
                if task.task_id not in completed
                and all(dep in completed for dep in (task.dependencies or []))
            ]

            if not ready_tasks:
                self._logger.error("Circular dependency detected or no tasks ready")
                break

            # Execute ready tasks in parallel
            parallel_tasks = []
            for task in ready_tasks:
                agent = self._worker_agents.get(task.assigned_agent)
                if agent:
                    parallel_tasks.append(
                        ParallelTask(
                            agent=agent,
                            prompt=task.description,
                            kwargs={},
                            task_id=task.task_id,
                        )
                    )

            # Execute in parallel
            if parallel_tasks:
                parallel_results = self._executor.execute_parallel(parallel_tasks)

                # Update subtask results
                for i, task in enumerate(ready_tasks):
                    task.result = parallel_results.results[i]
                    completed.add(task.task_id)
                    results.append(task)

                self._logger.info(
                    f"Completed {len(ready_tasks)} tasks in parallel",
                    tasks=[t.task_id for t in ready_tasks],
                )

        return results

    def _combine_results(self, subtasks: List[SubTask]) -> Dict[str, Any]:
        """Combine results from all subtasks."""
        combined = {
            "total_subtasks": len(subtasks),
            "completed": len([t for t in subtasks if t.result and t.result.success]),
            "failed": len([t for t in subtasks if t.result and not t.result.success]),
            "subtask_results": {},
        }

        for task in subtasks:
            if task.result:
                combined["subtask_results"][task.task_id] = {
                    "description": task.description,
                    "agent": task.assigned_agent,
                    "success": task.result.success,
                    "output": task.result.output,
                    "duration": task.result.duration,
                }

        # In real implementation, use LLM to synthesize final answer
        combined["final_output"] = self._synthesize_results(subtasks)

        return combined

    def _synthesize_results(self, subtasks: List[SubTask]) -> str:
        """Synthesize final result from subtask results."""
        # In real implementation, use LLM to combine results
        successful = [t for t in subtasks if t.result and t.result.success]

        if len(successful) == len(subtasks):
            return "All subtasks completed successfully"
        else:
            return f"Completed {len(successful)}/{len(subtasks)} subtasks"

    def add_worker_agent(self, name: str, agent: BaseAgent) -> None:
        """Add a worker agent to the supervisor's pool."""
        self._worker_agents[name] = agent
        self._logger.info(f"Added worker agent: {name}")
