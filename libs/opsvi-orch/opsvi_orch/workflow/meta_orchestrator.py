"""Meta-orchestrator for coordinating the software factory pipeline."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery.result import AsyncResult

from .dag_loader import dag_loader
from .task_models import Project, Run
from ..memory.graph.neo4j_client import get_neo4j_client
from ..workers.tasks import (
    execute_plan_task,
    execute_spec_task,
    execute_research_task,
    execute_code_task,
    execute_test_task,
    execute_validate_task,
    execute_document_task,
    execute_critic_task,
)

logger = logging.getLogger(__name__)


class MetaOrchestrator:
    """Meta-orchestrator for coordinating pipeline execution."""

    def __init__(self) -> None:
        """Initialize the meta-orchestrator."""
        self.neo4j = get_neo4j_client()
        self.task_mapping = {
            "plan": execute_plan_task,
            "spec": execute_spec_task,
            "research": execute_research_task,
            "code": execute_code_task,
            "test": execute_test_task,
            "validate": execute_validate_task,
            "document": execute_document_task,
            "critic": execute_critic_task,
        }

    async def execute_pipeline(
        self,
        pipeline_name: str,
        project_request: str,
        project_name: str,
        project_description: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a complete pipeline."""
        try:
            # Create project and run
            project = Project(
                name=project_name,
                description=project_description,
                request=project_request,
                config=config or {},
            )

            run = Run(
                project_id=project.id, pipeline_name=pipeline_name, config=config or {}
            )

            # Log to Neo4j
            self.neo4j.create_project(project.dict())
            self.neo4j.create_run(run.dict())
            self.neo4j.link_project_to_run(project.id, run.id)

            # Load pipeline definition
            pipeline = dag_loader.load_pipeline(pipeline_name)
            execution_order = pipeline.get_execution_order()

            # Initialize execution state
            execution_state = {
                "project": project,
                "run": run,
                "pipeline": pipeline,
                "execution_order": execution_order,
                "task_results": {},
                "completed_tasks": set(),
                "failed_tasks": set(),
                "current_loop": 0,
                "max_loops": config.get("max_loops", 3) if config else 3,
            }

            # Execute pipeline
            result = await self._execute_pipeline_loop(execution_state)

            return result

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_id": str(project.id) if "project" in locals() else None,
                "run_id": str(run.id) if "run" in locals() else None,
            }

    async def _execute_pipeline_loop(
        self, execution_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the pipeline with retry loops."""
        project = execution_state["project"]
        run = execution_state["run"]
        pipeline = execution_state["pipeline"]
        execution_order = execution_state["execution_order"]

        for loop in range(execution_state["max_loops"]):
            execution_state["current_loop"] = loop

            logger.info(
                f"Starting pipeline loop {loop + 1}/{execution_state['max_loops']}"
            )

            try:
                # Execute tasks in order
                for task_name in execution_order:
                    if task_name in execution_state["failed_tasks"]:
                        continue  # Skip failed tasks

                    task_result = await self._execute_task(task_name, execution_state)

                    if task_result["success"]:
                        execution_state["completed_tasks"].add(task_name)
                        execution_state["task_results"][task_name] = task_result
                    else:
                        execution_state["failed_tasks"].add(task_name)
                        logger.error(
                            f"Task {task_name} failed: {task_result.get('error')}"
                        )

                # Check if all tasks completed successfully
                if len(execution_state["completed_tasks"]) == len(execution_order):
                    logger.info("All tasks completed successfully")
                    break

                # Check if we should continue to next loop
                if loop < execution_state["max_loops"] - 1:
                    logger.info(f"Some tasks failed, continuing to loop {loop + 2}")
                    # Here you could implement repair logic
                    await self._repair_failed_tasks(execution_state)
                else:
                    logger.warning("Max loops reached, some tasks failed")

            except Exception as e:
                logger.error(f"Pipeline loop {loop + 1} failed: {e}")
                if loop == execution_state["max_loops"] - 1:
                    raise

        # Finalize run
        await self._finalize_run(execution_state)

        return {
            "success": len(execution_state["completed_tasks"]) == len(execution_order),
            "project_id": str(project.id),
            "run_id": str(run.id),
            "completed_tasks": list(execution_state["completed_tasks"]),
            "failed_tasks": list(execution_state["failed_tasks"]),
            "total_loops": execution_state["current_loop"] + 1,
            "task_results": execution_state["task_results"],
        }

    async def _execute_task(
        self, task_name: str, execution_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single task."""
        project = execution_state["project"]
        run = execution_state["run"]
        pipeline = execution_state["pipeline"]

        # Find task definition
        task_def = next((t for t in pipeline.tasks if t.name == task_name), None)
        if not task_def:
            return {
                "success": False,
                "error": f"Task {task_name} not found in pipeline",
            }

        # Check dependencies
        for dep in task_def.depends_on:
            if dep not in execution_state["completed_tasks"]:
                return {"success": False, "error": f"Dependency {dep} not completed"}

        # Prepare task data
        input_data = self._prepare_task_input(task_name, execution_state)

        task_data = {
            "name": task_name,
            "project_id": str(project.id),
            "run_id": str(run.id),
            "input_data": input_data,
            "agent_path": task_def.agent,
            "agent_config": task_def.config,
        }

        # Submit task to Celery
        try:
            task_func = self.task_mapping.get(task_def.type.value)
            if not task_func:
                return {
                    "success": False,
                    "error": f"No task function for type {task_def.type.value}",
                }

            # Submit task
            celery_result = task_func.delay(task_data)

            # Wait for completion
            result = await self._wait_for_task_completion(celery_result, task_name)

            # Apply gate policies if task succeeded
            if result["success"] and task_def.gate_policies:
                gate_result = await self._apply_gate_policies(
                    task_name, result, task_def.gate_policies, execution_state
                )
                if not gate_result["pass"]:
                    result["success"] = False
                    result["error"] = f"Gate policies failed: {gate_result['reasons']}"

            return result

        except Exception as e:
            logger.error(f"Task {task_name} execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_task_completion(
        self, celery_result: AsyncResult, task_name: str
    ) -> Dict[str, Any]:
        """Wait for a Celery task to complete."""
        try:
            # Wait for result with timeout
            result = celery_result.get(timeout=3600)  # 1 hour timeout

            if celery_result.successful():
                return {
                    "success": True,
                    "result": result.get("result"),
                    "task_id": result.get("task_id"),
                    "metrics": result.get("metrics", {}),
                }
            else:
                return {
                    "success": False,
                    "error": f"Task {task_name} failed",
                    "task_id": result.get("task_id") if result else None,
                }

        except Exception as e:
            logger.error(f"Error waiting for task {task_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_gate_policies(
        self,
        task_name: str,
        task_result: Dict[str, Any],
        gate_policies: List[str],
        execution_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply gate policies to a task result."""
        try:
            # Prepare input for critic
            critic_input = {
                "task_type": task_name,
                "task_result": task_result,
                "artifacts": task_result.get("result", {}).get("artifacts", []),
                "code_path": task_result.get("result", {}).get("code_path"),
                "test_path": task_result.get("result", {}).get("test_path"),
                "spec": execution_state.get("task_results", {})
                .get("generate_requirements", {})
                .get("result", {}),
                "architecture": execution_state.get("task_results", {})
                .get("generate_architecture", {})
                .get("result", {}),
            }

            # Execute critic
            critic_result = await self._execute_critic_task(
                critic_input, execution_state
            )

            return critic_result

        except Exception as e:
            logger.error(f"Gate policy evaluation failed: {e}")
            return {
                "pass": False,
                "reasons": [f"Gate policy evaluation failed: {e}"],
                "score": 0.0,
            }

    async def _execute_critic_task(
        self, input_data: Dict[str, Any], execution_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute critic task for evaluation."""
        project = execution_state["project"]
        run = execution_state["run"]

        task_data = {
            "name": "critic_evaluation",
            "project_id": str(project.id),
            "run_id": str(run.id),
            "input_data": input_data,
            "agent_path": "critic_agent",
            "agent_config": {},
        }

        try:
            celery_result = execute_critic_task.delay(task_data)
            result = await self._wait_for_task_completion(
                celery_result, "critic_evaluation"
            )

            if result["success"]:
                return result["result"]
            else:
                return {
                    "pass": False,
                    "reasons": [result.get("error", "Critic evaluation failed")],
                    "score": 0.0,
                }

        except Exception as e:
            logger.error(f"Critic task execution failed: {e}")
            return {
                "pass": False,
                "reasons": [f"Critic execution failed: {e}"],
                "score": 0.0,
            }

    def _prepare_task_input(
        self, task_name: str, execution_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare input data for a task."""
        task_results = execution_state["task_results"]

        # Base input
        input_data = {
            "request": execution_state["project"].request,
            "project_name": execution_state["project"].name,
            "loop": execution_state["current_loop"],
        }

        # Add results from previous tasks
        for completed_task, result in task_results.items():
            if result["success"]:
                input_data[completed_task] = result["result"]

        # Task-specific input preparation
        if task_name == "generate_code":
            # Add architecture and requirements
            if "generate_architecture" in task_results:
                input_data["architecture"] = task_results["generate_architecture"][
                    "result"
                ]
            if "generate_requirements" in task_results:
                input_data["requirements"] = task_results["generate_requirements"][
                    "result"
                ]

        elif task_name == "generate_tests":
            # Add generated code
            if "generate_code" in task_results:
                input_data["code"] = task_results["generate_code"]["result"]

        elif task_name == "validate_system":
            # Add all previous results
            input_data["all_results"] = task_results

        return input_data

    async def _repair_failed_tasks(self, execution_state: Dict[str, Any]) -> None:
        """Attempt to repair failed tasks."""
        # This is a placeholder for repair logic
        # In practice, you might:
        # - Retry with different parameters
        # - Use fallback agents
        # - Apply automatic fixes
        logger.info("Repair logic would be implemented here")

    async def _finalize_run(self, execution_state: Dict[str, Any]) -> None:
        """Finalize the run and update status."""
        project = execution_state["project"]
        run = execution_state["run"]

        # Update run status
        run.status = (
            "completed" if len(execution_state["failed_tasks"]) == 0 else "failed"
        )
        run.completed_at = datetime.utcnow()
        run.completed_tasks = len(execution_state["completed_tasks"])
        run.failed_tasks = len(execution_state["failed_tasks"])

        # Calculate totals
        total_tokens = 0
        total_cost = 0.0
        for result in execution_state["task_results"].values():
            metrics = result.get("metrics", {})
            total_tokens += metrics.get("tokens_used", 0)
            total_cost += metrics.get("cost_usd", 0.0)

        run.total_tokens = total_tokens
        run.total_cost_usd = total_cost

        # Update in Neo4j
        try:
            self.neo4j._execute_query(
                "MATCH (r:Run {id: $run_id}) SET r.status = $status, r.completed_at = datetime($completed_at), r.completed_tasks = $completed_tasks, r.failed_tasks = $failed_tasks, r.total_tokens = $total_tokens, r.total_cost_usd = $total_cost",
                {
                    "run_id": str(run.id),
                    "status": run.status,
                    "completed_at": run.completed_at.isoformat(),
                    "completed_tasks": run.completed_tasks,
                    "failed_tasks": run.failed_tasks,
                    "total_tokens": run.total_tokens,
                    "total_cost_usd": run.total_cost_usd,
                },
            )
        except Exception as e:
            logger.error(f"Failed to update run status: {e}")


# Global orchestrator instance
meta_orchestrator = MetaOrchestrator()


async def execute_software_factory_pipeline(
    request: str,
    project_name: str,
    project_description: str = "",
    pipeline_name: str = "software_factory_v1",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute the software factory pipeline."""
    return await meta_orchestrator.execute_pipeline(
        pipeline_name=pipeline_name,
        project_request=request,
        project_name=project_name,
        project_description=project_description,
        config=config,
    )
