#!/usr/bin/env python3
"""
Resumable Documentation Orchestrator

Extends GenericOrchestrator with checkpointing and resumption capabilities
specifically designed for long-running documentation workflows.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..generic_orchestrator import AgentTask, GenericOrchestrator
from .documentation_workflow import DocumentationConfig, DocumentationWorkflow
from .execution_plans import CheckpointManager, ExecutionPlan, ExecutionPlanManager

logger = logging.getLogger(__name__)


class ResumableDocumentationOrchestrator:
    """
    Documentation orchestrator with checkpointing and resumption capabilities
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        checkpoint_interval: int = 5,  # Create checkpoint every N completed tasks
        auto_cleanup_checkpoints: bool = True,
        **orchestrator_kwargs,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.checkpoints_dir = output_dir / "checkpoints"
        self.plans_dir = output_dir / "plans"
        self.logs_dir = output_dir / "logs"

        for dir_path in [self.checkpoints_dir, self.plans_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.checkpoint_manager = CheckpointManager(self.checkpoints_dir)
        self.plan_manager = ExecutionPlanManager(self.plans_dir)

        # Initialize base orchestrator
        self.orchestrator = GenericOrchestrator(
            output_dir=output_dir,
            max_parallel=max_parallel,
            tokens=tokens,
            use_optimizations=False,  # Force disable to avoid MCP config issues
            **orchestrator_kwargs,
        )

        # Initialize documentation workflow
        self.doc_workflow = DocumentationWorkflow(self.orchestrator)

        # Configuration
        self.checkpoint_interval = checkpoint_interval
        self.auto_cleanup_checkpoints = auto_cleanup_checkpoints

        # State tracking
        self.current_plan: Optional[ExecutionPlan] = None
        self.current_checkpoint_id: Optional[str] = None
        self.tasks_completed_since_checkpoint = 0

        # Set up orchestrator hooks
        self.orchestrator.post_execute_hook = self._post_execute_hook

    async def execute_system_documentation(
        self,
        app_name: str,
        app_root: str,
        output_dir: str = None,
        template: str = "comprehensive",
        resume_from: str = None,
        **config_kwargs,
    ) -> Dict[str, Any]:
        """
        Execute system documentation workflow with checkpointing

        Args:
            app_name: Name of the application
            app_root: Root directory of the application
            output_dir: Output directory for documentation
            template: Template to use (comprehensive, standard, minimal, api-focused)
            resume_from: Checkpoint ID to resume from
            **config_kwargs: Additional configuration options

        Returns:
            Execution summary with results and metrics
        """

        logger.info(f"Starting system documentation for {app_name}")

        # Handle resumption
        if resume_from:
            return await self._resume_from_checkpoint(resume_from)

        # Create or load execution plan
        plan = self.plan_manager.create_plan_from_template(
            template_name=template,
            app_name=app_name,
            app_root=app_root,
            output_dir=output_dir or f"{app_root}/docs",
            **config_kwargs,
        )

        self.current_plan = plan
        logger.info(f"Created execution plan: {plan.plan_id}")

        # Create documentation configuration
        doc_config = DocumentationConfig(
            app_name=app_name,
            app_root=Path(app_root),
            output_dir=Path(plan.config["output_dir"]),
            **{
                k: v
                for k, v in plan.config.items()
                if k not in ["app_name", "app_root", "output_dir"]
            },
        )

        # Execute workflow with checkpointing
        return await self._execute_with_checkpointing(plan, doc_config)

    async def _execute_with_checkpointing(
        self, plan: ExecutionPlan, doc_config: DocumentationConfig
    ) -> Dict[str, Any]:
        """Execute workflow with automatic checkpointing"""

        completed_tasks = []
        failed_tasks = []
        all_results = []

        # Create initial checkpoint
        initial_checkpoint = self.checkpoint_manager.create_checkpoint(
            workflow_type=plan.workflow_type,
            app_name=plan.app_name,
            completed_tasks=[],
            failed_tasks=[],
            pending_tasks=[task for phase in plan.phases for task in phase["tasks"]],
            config=plan.config,
            context={"plan_id": plan.plan_id},
        )

        self.current_checkpoint_id = initial_checkpoint.checkpoint_id
        logger.info(f"Created initial checkpoint: {self.current_checkpoint_id}")

        try:
            while True:
                # Get next batch of ready tasks
                ready_tasks = self.plan_manager.get_next_phase_tasks(
                    plan, completed_tasks
                )

                if not ready_tasks:
                    logger.info("No more tasks ready for execution")
                    break

                logger.info(f"Executing {len(ready_tasks)} tasks: {ready_tasks}")

                # Create AgentTask objects for ready tasks
                agent_tasks = []
                for task_id in ready_tasks:
                    agent_task = await self._create_agent_task(
                        task_id, plan, doc_config
                    )
                    if agent_task:
                        agent_tasks.append(agent_task)

                if not agent_tasks:
                    logger.warning("No valid agent tasks created")
                    break

                # Execute batch
                batch_results = await self.orchestrator.execute_batch(agent_tasks)
                all_results.extend(batch_results)

                # Update tracking
                for result in batch_results:
                    if result["status"] == "completed":
                        completed_tasks.append(result["task_id"])
                    elif result["status"] == "failed":
                        failed_tasks.append(result["task_id"])

                self.tasks_completed_since_checkpoint += len(
                    [r for r in batch_results if r["status"] == "completed"]
                )

                # Create checkpoint if needed
                if (
                    self.tasks_completed_since_checkpoint >= self.checkpoint_interval
                    or self.plan_manager.is_checkpoint_phase(plan, completed_tasks)
                ):
                    pending_tasks = [
                        task
                        for phase in plan.phases
                        for task in phase["tasks"]
                        if task not in completed_tasks and task not in failed_tasks
                    ]

                    checkpoint = self.checkpoint_manager.create_checkpoint(
                        workflow_type=plan.workflow_type,
                        app_name=plan.app_name,
                        completed_tasks=completed_tasks,
                        failed_tasks=failed_tasks,
                        pending_tasks=pending_tasks,
                        config=plan.config,
                        context={
                            "plan_id": plan.plan_id,
                            "results": all_results,
                            "current_phase": self._get_current_phase(
                                plan, completed_tasks
                            ),
                        },
                    )

                    self.current_checkpoint_id = checkpoint.checkpoint_id
                    self.tasks_completed_since_checkpoint = 0
                    logger.info(f"Created checkpoint: {self.current_checkpoint_id}")

                # Brief pause between batches
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

            # Create failure checkpoint
            pending_tasks = [
                task
                for phase in plan.phases
                for task in phase["tasks"]
                if task not in completed_tasks and task not in failed_tasks
            ]

            failure_checkpoint = self.checkpoint_manager.create_checkpoint(
                workflow_type=plan.workflow_type,
                app_name=plan.app_name,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                pending_tasks=pending_tasks,
                config=plan.config,
                context={
                    "plan_id": plan.plan_id,
                    "error": str(e),
                    "results": all_results,
                    "failure_point": self._get_current_phase(plan, completed_tasks),
                },
            )

            logger.info(
                f"Created failure checkpoint: {failure_checkpoint.checkpoint_id}"
            )
            raise

        # Final summary
        summary = {
            "workflow_type": plan.workflow_type,
            "app_name": plan.app_name,
            "plan_id": plan.plan_id,
            "execution_completed": True,
            "total_tasks": len(
                [task for phase in plan.phases for task in phase["tasks"]]
            ),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(completed_tasks)
            / len([task for phase in plan.phases for task in phase["tasks"]])
            * 100,
            "output_dir": str(doc_config.output_dir),
            "final_checkpoint": self.current_checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
        }

        # Save final summary
        summary_file = self.output_dir / f"execution_summary_{plan.plan_id}.json"
        summary_file.write_text(json.dumps(summary, indent=2, default=str))

        # Cleanup old checkpoints if enabled
        if self.auto_cleanup_checkpoints:
            self.checkpoint_manager.cleanup_old_checkpoints(keep_count=5)

        logger.info(
            f"Workflow completed: {summary['completed_tasks']}/{summary['total_tasks']} tasks successful"
        )

        return summary

    async def _resume_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Resume execution from a checkpoint"""

        logger.info(f"Resuming from checkpoint: {checkpoint_id}")

        # Load checkpoint
        checkpoint = self.checkpoint_manager.load_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # Load execution plan
        plan_id = checkpoint.context.get("plan_id")
        if not plan_id:
            raise ValueError(f"No plan ID in checkpoint: {checkpoint_id}")

        plan = self.plan_manager.load_plan(plan_id)
        if not plan:
            raise ValueError(f"Execution plan not found: {plan_id}")

        self.current_plan = plan
        self.current_checkpoint_id = checkpoint_id

        # Recreate documentation config
        doc_config = DocumentationConfig(
            app_name=checkpoint.app_name,
            app_root=Path(checkpoint.config["app_root"]),
            output_dir=Path(checkpoint.config["output_dir"]),
            **{
                k: v
                for k, v in checkpoint.config.items()
                if k not in ["app_name", "app_root", "output_dir"]
            },
        )

        logger.info(
            f"Resuming execution: {len(checkpoint.completed_tasks)} tasks completed, "
            f"{len(checkpoint.pending_tasks)} tasks pending"
        )

        # Continue execution from current state
        return await self._continue_execution_from_checkpoint(
            checkpoint, plan, doc_config
        )

    async def _continue_execution_from_checkpoint(
        self, checkpoint, plan: ExecutionPlan, doc_config: DocumentationConfig
    ) -> Dict[str, Any]:
        """Continue execution from checkpoint state"""

        completed_tasks = checkpoint.completed_tasks.copy()
        failed_tasks = checkpoint.failed_tasks.copy()
        all_results = checkpoint.context.get("results", [])

        # Continue workflow execution
        try:
            while True:
                ready_tasks = self.plan_manager.get_next_phase_tasks(
                    plan, completed_tasks
                )

                if not ready_tasks:
                    break

                logger.info(f"Continuing with {len(ready_tasks)} tasks: {ready_tasks}")

                # Create and execute agent tasks
                agent_tasks = []
                for task_id in ready_tasks:
                    agent_task = await self._create_agent_task(
                        task_id, plan, doc_config
                    )
                    if agent_task:
                        agent_tasks.append(agent_task)

                batch_results = await self.orchestrator.execute_batch(agent_tasks)
                all_results.extend(batch_results)

                # Update tracking
                for result in batch_results:
                    if result["status"] == "completed":
                        completed_tasks.append(result["task_id"])
                    elif result["status"] == "failed":
                        failed_tasks.append(result["task_id"])

                self.tasks_completed_since_checkpoint += len(
                    [r for r in batch_results if r["status"] == "completed"]
                )

                # Create checkpoint if needed
                if (
                    self.tasks_completed_since_checkpoint >= self.checkpoint_interval
                    or self.plan_manager.is_checkpoint_phase(plan, completed_tasks)
                ):
                    pending_tasks = [
                        task
                        for phase in plan.phases
                        for task in phase["tasks"]
                        if task not in completed_tasks and task not in failed_tasks
                    ]

                    new_checkpoint = self.checkpoint_manager.create_checkpoint(
                        workflow_type=plan.workflow_type,
                        app_name=plan.app_name,
                        completed_tasks=completed_tasks,
                        failed_tasks=failed_tasks,
                        pending_tasks=pending_tasks,
                        config=plan.config,
                        context={
                            "plan_id": plan.plan_id,
                            "results": all_results,
                            "current_phase": self._get_current_phase(
                                plan, completed_tasks
                            ),
                            "resumed_from": checkpoint.checkpoint_id,
                        },
                    )

                    self.current_checkpoint_id = new_checkpoint.checkpoint_id
                    self.tasks_completed_since_checkpoint = 0
                    logger.info(
                        f"Created resume checkpoint: {self.current_checkpoint_id}"
                    )

                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Resume execution failed: {e}")
            raise

        # Create final summary
        summary = {
            "workflow_type": plan.workflow_type,
            "app_name": plan.app_name,
            "plan_id": plan.plan_id,
            "execution_completed": True,
            "resumed_from": checkpoint.checkpoint_id,
            "total_tasks": len(
                [task for phase in plan.phases for task in phase["tasks"]]
            ),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(completed_tasks)
            / len([task for phase in plan.phases for task in phase["tasks"]])
            * 100,
            "output_dir": str(doc_config.output_dir),
            "final_checkpoint": self.current_checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
        }

        summary_file = self.output_dir / f"resume_summary_{plan.plan_id}.json"
        summary_file.write_text(json.dumps(summary, indent=2, default=str))

        if self.auto_cleanup_checkpoints:
            self.checkpoint_manager.cleanup_old_checkpoints(keep_count=5)

        logger.info(
            f"Resume completed: {summary['completed_tasks']}/{summary['total_tasks']} tasks successful"
        )

        return summary

    async def _create_agent_task(
        self, task_id: str, plan: ExecutionPlan, doc_config: DocumentationConfig
    ) -> Optional[AgentTask]:
        """Create AgentTask from plan task ID"""

        # Use the documentation workflow to create specialized tasks
        all_tasks = self.doc_workflow.create_documentation_tasks(doc_config)

        # Find matching task
        for task in all_tasks:
            if task.task_id == task_id:
                return task

        logger.warning(f"Task not found: {task_id}")
        return None

    def _get_current_phase(
        self, plan: ExecutionPlan, completed_tasks: List[str]
    ) -> str:
        """Get current phase name based on completed tasks"""

        for phase in plan.phases:
            phase_tasks = phase["tasks"]

            # If any task in this phase is not completed, this is current phase
            if any(task not in completed_tasks for task in phase_tasks):
                return phase["phase_id"]

        return "completed"

    async def _post_execute_hook(self, task: AgentTask):
        """Post-execution hook for tracking progress"""

        if task.status == "completed":
            logger.info(f"✓ Task completed: {task.task_id}")
        elif task.status == "failed":
            logger.warning(f"✗ Task failed: {task.task_id} - {task.error}")

    def list_checkpoints(self, app_name: str = None) -> List[Dict[str, Any]]:
        """List available checkpoints for resumption"""

        checkpoints = self.checkpoint_manager.list_checkpoints(
            workflow_type="system-documentation", app_name=app_name
        )

        return [
            {
                "checkpoint_id": cp.checkpoint_id,
                "timestamp": cp.timestamp,
                "app_name": cp.app_name,
                "completed_tasks": len(cp.completed_tasks),
                "failed_tasks": len(cp.failed_tasks),
                "pending_tasks": len(cp.pending_tasks),
                "can_resume": len(cp.pending_tasks) > 0,
            }
            for cp in checkpoints
        ]

    def get_checkpoint_details(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a checkpoint"""

        checkpoint = self.checkpoint_manager.load_checkpoint(checkpoint_id)
        if not checkpoint:
            return None

        return {
            "checkpoint": checkpoint.to_dict(),
            "can_resume": len(checkpoint.pending_tasks) > 0,
            "progress": {
                "completed": len(checkpoint.completed_tasks),
                "failed": len(checkpoint.failed_tasks),
                "pending": len(checkpoint.pending_tasks),
                "total": len(checkpoint.completed_tasks)
                + len(checkpoint.failed_tasks)
                + len(checkpoint.pending_tasks),
            },
        }
