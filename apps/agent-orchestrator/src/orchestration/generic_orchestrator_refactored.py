#!/usr/bin/env python3
"""
Refactored Generic Agent Orchestrator
Coordinates between TaskScheduler, WorkflowEngine, MetricsCollector, and StateManager
Maintains public API compatibility with original GenericOrchestrator
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .metrics_collector import MetricsCollector
from .state_manager import StateManager
from .task_scheduler import AgentTask, TaskScheduler
from .workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class GenericOrchestrator:
    """
    Refactored orchestrator using separated components.
    Maintains backward compatibility with original API.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # Dynamic architecture parameters
        master_mcp_registry_path: Optional[Path] = None,
        agent_execution_profile: str = "standard",
        agent_debug_mode: bool = False,
        agent_base_work_dir: Optional[Path] = None,
        enable_dynamic_configs: bool = False,
        log_to_work_dir: bool = False,
        # Workflow and dashboard parameters
        workflow_name: Optional[str] = None,
        task_file_path: Optional[str] = None,
        enable_dashboard_reporting: bool = False,
        dashboard_state_callback: Optional[Callable] = None,
        workflow_source: Optional[str] = None,
    ):
        """Initialize orchestrator with separated components"""

        # Ensure output directory exists
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize workflow engine first to determine workflow ID
        self.workflow_engine = WorkflowEngine(
            output_dir=self.output_dir,
            workflow_name=workflow_name,
            task_file_path=task_file_path,
            workflow_source=workflow_source,
            use_optimizations=use_optimizations,
            agent_execution_profile=agent_execution_profile,
            agent_debug_mode=agent_debug_mode,
            agent_base_work_dir=agent_base_work_dir,
            enable_dynamic_configs=enable_dynamic_configs,
            master_mcp_registry_path=master_mcp_registry_path,
        )

        # Get workflow info from engine
        workflow_info = self.workflow_engine.get_workflow_info()
        self.workflow_id = workflow_info["workflow_id"]
        self.workflow_name = workflow_info["workflow_name"]
        self.workflow_source = workflow_info["workflow_source"]

        # Initialize task scheduler
        self.task_scheduler = TaskScheduler(
            max_parallel=max_parallel, tokens=tokens, output_dir=self.output_dir
        )

        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(
            output_dir=self.output_dir, workflow_id=self.workflow_id
        )

        # Initialize state manager
        self.state_manager = StateManager(
            output_dir=self.output_dir,
            workflow_id=self.workflow_id,
            workflow_name=self.workflow_name,
            workflow_source=self.workflow_source,
            enable_dashboard_reporting=enable_dashboard_reporting,
            dashboard_state_callback=dashboard_state_callback,
        )

        # Store configuration
        self.max_parallel = max_parallel
        self.use_optimizations = use_optimizations
        self.enable_dashboard_reporting = enable_dashboard_reporting

        # Backward compatibility properties
        self.token_pool = self.task_scheduler.token_pool
        self.dep_manager = self.task_scheduler.dep_manager
        self.message_bus = self.workflow_engine.message_bus

        logger.info(f"GenericOrchestrator initialized for workflow: {self.workflow_id}")

    async def execute_agent(self, task: AgentTask) -> Dict:
        """
        Execute a single agent task.
        Maintains compatibility with original API.
        """
        try:
            # Mark task as running
            await self.task_scheduler.mark_task_running(task.task_id)
            self.metrics_collector.start_task(task.task_id)
            self.state_manager.report_task_activity(
                task.task_id, "started", {"task_type": task.task_type}
            )

            # Acquire token
            token, token_idx = await self.task_scheduler.acquire_token()

            try:
                # Execute via workflow engine
                result = await self.workflow_engine.execute_agent(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    prompt=task.prompt,
                    context=task.context,
                    token=token,
                    work_dir_name=task.work_dir_name,
                    system_prompt=task.system_prompt,
                    enhancement_level=task.enhancement_level,
                )

                # Update task with result
                task.result = result
                task.status = "completed" if result.get("success") else "failed"

                if task.status == "completed":
                    await self.task_scheduler.mark_task_completed(task.task_id, result)
                    self.metrics_collector.end_task(task.task_id, "completed")
                else:
                    error = result.get("error", "Unknown error")
                    await self.task_scheduler.mark_task_failed(
                        task.task_id, error, result
                    )
                    self.metrics_collector.end_task(task.task_id, "failed", error)

                # Save task state
                self.state_manager.save_task_state(task.task_id, task.to_dict())

                return result

            finally:
                # Release token
                self.task_scheduler.release_token(token_idx)

        except Exception as e:
            logger.error(f"Failed to execute agent for task {task.task_id}: {e}")

            # Mark as failed
            await self.task_scheduler.mark_task_failed(
                task.task_id, str(e), {"exception": str(e)}
            )
            self.metrics_collector.end_task(task.task_id, "failed", str(e))

            task.status = "failed"
            task.error = str(e)

            return {"task_id": task.task_id, "success": False, "error": str(e)}

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """
        Execute a batch of tasks with dependency management.
        Maintains compatibility with original API.
        """
        results = []

        # Schedule tasks
        await self.task_scheduler.schedule_tasks(tasks)

        # Update state
        self.state_manager.update_task_counts(total=len(tasks))

        # Process tasks respecting dependencies
        while True:
            # Get next runnable tasks
            runnable = await self.task_scheduler.get_next_runnable_tasks()

            if not runnable:
                # Check if all tasks are done
                stats = self.task_scheduler.get_task_stats()
                if stats["pending"] == 0 and stats["running"] == 0:
                    break

                # Wait a bit for running tasks to complete
                await asyncio.sleep(1)
                continue

            # Execute runnable tasks in parallel
            batch_tasks = []
            for task in runnable:
                # Wait for available slot
                await self.task_scheduler.wait_for_available_slot()

                # Create execution task
                exec_task = asyncio.create_task(self._execute_with_slot(task))
                batch_tasks.append(exec_task)

            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Task execution failed: {result}")
                    results.append({"success": False, "error": str(result)})
                else:
                    results.append(result)

            # Update progress
            stats = self.task_scheduler.get_task_stats()
            eta = self.metrics_collector.calculate_eta(
                stats["completed"], stats["total"]
            )

            self.state_manager.report_workflow_progress(
                completed_tasks=stats["completed"],
                total_tasks=stats["total"],
                eta_seconds=eta,
            )

        return results

    async def _execute_with_slot(self, task: AgentTask) -> Dict:
        """Execute task and release slot when done"""
        try:
            result = await self.execute_agent(task)
            return result
        finally:
            self.task_scheduler.release_execution_slot()

    async def run(
        self,
        task_generator: Optional[Callable] = None,
        result_processor: Optional[Callable] = None,
        tasks: Optional[List[AgentTask]] = None,
    ) -> List[Dict]:
        """
        Main entry point for orchestrator execution.
        Maintains compatibility with original API.
        """
        try:
            # Start workflow
            self.state_manager.report_workflow_started()
            self.metrics_collector.log_audit_action("workflow_started")

            # Generate or use provided tasks
            if tasks is None:
                if task_generator is None:
                    raise ValueError("Either tasks or task_generator must be provided")
                tasks = task_generator()

            # Validate tasks
            if not tasks:
                logger.warning("No tasks to execute")
                return []

            logger.info(f"Starting workflow with {len(tasks)} tasks")

            # Execute tasks
            results = await self.execute_batch(tasks)

            # Process results if processor provided
            if result_processor:
                await result_processor(results)

            # Generate completion report
            completion_report = self.metrics_collector.generate_completion_report()

            # Save metrics
            await self.metrics_collector.save_metrics()

            # Report completion
            self.state_manager.report_workflow_completed(completion_report)

            # Cleanup
            await self.workflow_engine.cleanup()

            logger.info(f"Workflow {self.workflow_id} completed successfully")

            return results

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

            # Save error state
            self.state_manager.set_workflow_status("failed")
            self.metrics_collector.log_audit_action(
                "workflow_failed", {"error": str(e)}
            )

            raise

    # Backward compatibility methods

    def _log_audit_action(self, action: str, details: Dict[str, Any] = None):
        """Backward compatibility wrapper"""
        self.metrics_collector.log_audit_action(action, details)

    def _track_deliverable(self, file_path: str, operation: str = "created"):
        """Backward compatibility wrapper"""
        self.metrics_collector.track_deliverable(file_path, operation)

    def _scan_for_deliverables(self):
        """Backward compatibility wrapper"""
        return self.metrics_collector.scan_for_deliverables()

    def _report_workflow_started(self):
        """Backward compatibility wrapper"""
        self.state_manager.report_workflow_started()

    def _report_workflow_progress(
        self,
        completed_tasks: int,
        total_tasks: int,
        current_task: Optional[str] = None,
        eta_seconds: Optional[int] = None,
    ):
        """Backward compatibility wrapper"""
        self.state_manager.report_workflow_progress(
            completed_tasks, total_tasks, current_task, eta_seconds
        )

    def _report_task_activity(
        self, task_id: str, activity_type: str, details: Optional[Dict[str, Any]] = None
    ):
        """Backward compatibility wrapper"""
        self.state_manager.report_task_activity(task_id, activity_type, details)

    def _report_workflow_completed(self, metrics: Dict):
        """Backward compatibility wrapper"""
        self.state_manager.report_workflow_completed(metrics)

    def _calculate_eta(self, completed_tasks: int, total_tasks: int) -> Optional[int]:
        """Backward compatibility wrapper"""
        return self.metrics_collector.calculate_eta(completed_tasks, total_tasks)

    async def _create_checkpoint(self, task: AgentTask):
        """Backward compatibility wrapper"""
        checkpoint_data = task.to_dict()
        return await self.workflow_engine.create_checkpoint(
            task.task_id, checkpoint_data
        )

    def _update_workflow_metadata(self, updates: Dict):
        """Backward compatibility wrapper"""
        self.state_manager.update_metadata(updates)

    async def _generate_workflow_completion_report(self) -> Dict[str, Any]:
        """Backward compatibility wrapper"""
        return self.metrics_collector.generate_completion_report()

    async def _save_completion_report(self, report: Dict[str, Any]):
        """Backward compatibility wrapper"""
        await self.metrics_collector.save_metrics()


# Example usage maintaining original API
def generate_test_tasks() -> List[AgentTask]:
    """Example task generator (from original)"""
    return [
        AgentTask(
            task_id="test_1",
            task_type="research",
            prompt="Research Python async patterns",
            context={"topic": "asyncio"},
            dependencies=[],
        ),
        AgentTask(
            task_id="test_2",
            task_type="analysis",
            prompt="Analyze the research findings",
            context={"source": "test_1"},
            dependencies=["test_1"],
        ),
        AgentTask(
            task_id="test_3",
            task_type="summary",
            prompt="Create executive summary",
            context={"sources": ["test_1", "test_2"]},
            dependencies=["test_1", "test_2"],
        ),
    ]


async def process_results(results: List[Dict]):
    """Example result processor (from original)"""
    logger.info(f"Processing {len(results)} results")
    for result in results:
        if result.get("success"):
            logger.info(f"Task {result.get('task_id')} completed successfully")
        else:
            logger.error(f"Task {result.get('task_id')} failed: {result.get('error')}")


async def main():
    """Example main function demonstrating API compatibility"""
    output_dir = Path("output/test_refactored")

    orchestrator = GenericOrchestrator(
        output_dir=output_dir,
        max_parallel=3,
        use_optimizations=True,
        workflow_name="test_refactored_orchestrator",
        enable_dashboard_reporting=False,
    )

    results = await orchestrator.run(
        task_generator=generate_test_tasks, result_processor=process_results
    )

    logger.info(f"Completed {len(results)} tasks")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
