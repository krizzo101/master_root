#!/usr/bin/env python3
"""
Execution Plan Templates for Documentation Workflow

Provides pre-configured execution plans for different documentation scenarios
with built-in dependency management, checkpointing, and resumption capabilities.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionCheckpoint:
    """Checkpoint for workflow resumption"""

    checkpoint_id: str
    timestamp: str
    workflow_type: str
    app_name: str
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionCheckpoint":
        return cls(**data)


@dataclass
class ExecutionPlan:
    """Complete execution plan with dependencies and checkpointing"""

    plan_id: str
    workflow_type: str
    app_name: str
    phases: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    checkpoints: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        return cls(**data)


class ExecutionPlanTemplates:
    """Pre-configured execution plan templates"""

    @staticmethod
    def system_documentation_comprehensive(
        app_name: str, app_root: str, output_dir: str = None
    ) -> ExecutionPlan:
        """Comprehensive documentation plan with all components"""

        plan_id = f"sysdoc_comprehensive_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        phases = [
            {
                "phase_id": "analysis",
                "name": "Codebase Analysis",
                "description": "Deep analysis of codebase structure and components",
                "tasks": ["code_analyzer"],
                "parallel": False,
                "checkpoint": True,
            },
            {
                "phase_id": "core_docs",
                "name": "Core Documentation",
                "description": "Generate essential documentation files",
                "tasks": ["readme_writer", "architecture_analyst"],
                "parallel": True,
                "checkpoint": True,
            },
            {
                "phase_id": "specialized_docs",
                "name": "Specialized Documentation",
                "description": "Generate API and user-focused documentation",
                "tasks": ["api_documenter", "user_guide_writer"],
                "parallel": True,
                "checkpoint": True,
            },
            {
                "phase_id": "deployment_docs",
                "name": "Deployment Documentation",
                "description": "Generate deployment and operations documentation",
                "tasks": ["deployment_specialist"],
                "parallel": False,
                "checkpoint": True,
            },
            {
                "phase_id": "integration",
                "name": "Integration & Validation",
                "description": "Integrate and validate complete documentation suite",
                "tasks": ["integration_validator"],
                "parallel": False,
                "checkpoint": True,
            },
        ]

        dependencies = {
            "readme_writer": ["code_analyzer"],
            "architecture_analyst": ["code_analyzer"],
            "api_documenter": ["code_analyzer"],
            "user_guide_writer": ["code_analyzer"],
            "deployment_specialist": ["architecture_analyst"],
            "integration_validator": [
                "readme_writer",
                "api_documenter",
                "architecture_analyst",
                "user_guide_writer",
                "deployment_specialist",
            ],
        }

        checkpoints = [
            "analysis",
            "core_docs",
            "specialized_docs",
            "deployment_docs",
            "integration",
        ]

        config = {
            "app_name": app_name,
            "app_root": app_root,
            "output_dir": output_dir or f"{app_root}/docs",
            "include_api_docs": True,
            "include_architecture": True,
            "include_deployment": True,
            "include_user_guide": True,
            "include_developer_guide": True,
            "detail_level": "comprehensive",
        }

        return ExecutionPlan(
            plan_id=plan_id,
            workflow_type="system-documentation",
            app_name=app_name,
            phases=phases,
            dependencies=dependencies,
            checkpoints=checkpoints,
            config=config,
        )

    @staticmethod
    def system_documentation_standard(
        app_name: str, app_root: str, output_dir: str = None
    ) -> ExecutionPlan:
        """Standard documentation plan with essential components"""

        plan_id = (
            f"sysdoc_standard_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        phases = [
            {
                "phase_id": "analysis",
                "name": "Codebase Analysis",
                "description": "Analyze codebase structure and key components",
                "tasks": ["code_analyzer"],
                "parallel": False,
                "checkpoint": True,
            },
            {
                "phase_id": "essential_docs",
                "name": "Essential Documentation",
                "description": "Generate core documentation files",
                "tasks": ["readme_writer", "api_documenter"],
                "parallel": True,
                "checkpoint": True,
            },
            {
                "phase_id": "integration",
                "name": "Integration & Validation",
                "description": "Integrate and validate documentation",
                "tasks": ["integration_validator"],
                "parallel": False,
                "checkpoint": True,
            },
        ]

        dependencies = {
            "readme_writer": ["code_analyzer"],
            "api_documenter": ["code_analyzer"],
            "integration_validator": ["readme_writer", "api_documenter"],
        }

        checkpoints = ["analysis", "essential_docs", "integration"]

        config = {
            "app_name": app_name,
            "app_root": app_root,
            "output_dir": output_dir or f"{app_root}/docs",
            "include_api_docs": True,
            "include_architecture": False,
            "include_deployment": False,
            "include_user_guide": False,
            "include_developer_guide": True,
            "detail_level": "standard",
        }

        return ExecutionPlan(
            plan_id=plan_id,
            workflow_type="system-documentation",
            app_name=app_name,
            phases=phases,
            dependencies=dependencies,
            checkpoints=checkpoints,
            config=config,
        )

    @staticmethod
    def system_documentation_minimal(
        app_name: str, app_root: str, output_dir: str = None
    ) -> ExecutionPlan:
        """Minimal documentation plan with basic README only"""

        plan_id = (
            f"sysdoc_minimal_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        phases = [
            {
                "phase_id": "analysis",
                "name": "Basic Analysis",
                "description": "Basic codebase analysis",
                "tasks": ["code_analyzer"],
                "parallel": False,
                "checkpoint": True,
            },
            {
                "phase_id": "readme_only",
                "name": "README Generation",
                "description": "Generate basic README documentation",
                "tasks": ["readme_writer"],
                "parallel": False,
                "checkpoint": True,
            },
        ]

        dependencies = {"readme_writer": ["code_analyzer"]}

        checkpoints = ["analysis", "readme_only"]

        config = {
            "app_name": app_name,
            "app_root": app_root,
            "output_dir": output_dir or f"{app_root}/docs",
            "include_api_docs": False,
            "include_architecture": False,
            "include_deployment": False,
            "include_user_guide": False,
            "include_developer_guide": False,
            "detail_level": "minimal",
        }

        return ExecutionPlan(
            plan_id=plan_id,
            workflow_type="system-documentation",
            app_name=app_name,
            phases=phases,
            dependencies=dependencies,
            checkpoints=checkpoints,
            config=config,
        )

    @staticmethod
    def api_documentation_focused(
        app_name: str, app_root: str, output_dir: str = None
    ) -> ExecutionPlan:
        """API-focused documentation plan"""

        plan_id = f"api_focused_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        phases = [
            {
                "phase_id": "analysis",
                "name": "API Analysis",
                "description": "Deep analysis focusing on API surfaces",
                "tasks": ["code_analyzer"],
                "parallel": False,
                "checkpoint": True,
            },
            {
                "phase_id": "api_docs",
                "name": "API Documentation",
                "description": "Generate comprehensive API documentation",
                "tasks": ["api_documenter", "readme_writer"],
                "parallel": True,
                "checkpoint": True,
            },
            {
                "phase_id": "integration",
                "name": "API Doc Integration",
                "description": "Integrate API documentation with examples",
                "tasks": ["integration_validator"],
                "parallel": False,
                "checkpoint": True,
            },
        ]

        dependencies = {
            "readme_writer": ["code_analyzer"],
            "api_documenter": ["code_analyzer"],
            "integration_validator": ["readme_writer", "api_documenter"],
        }

        checkpoints = ["analysis", "api_docs", "integration"]

        config = {
            "app_name": app_name,
            "app_root": app_root,
            "output_dir": output_dir or f"{app_root}/docs",
            "include_api_docs": True,
            "include_architecture": False,
            "include_deployment": False,
            "include_user_guide": False,
            "include_developer_guide": True,
            "detail_level": "comprehensive",
            "focus_area": "api",
        }

        return ExecutionPlan(
            plan_id=plan_id,
            workflow_type="system-documentation",
            app_name=app_name,
            phases=phases,
            dependencies=dependencies,
            checkpoints=checkpoints,
            config=config,
        )


class CheckpointManager:
    """Manages workflow checkpoints and resumption"""

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: ExecutionCheckpoint) -> Path:
        """Save checkpoint to disk"""
        checkpoint_file = (
            self.checkpoint_dir / f"checkpoint_{checkpoint.checkpoint_id}.json"
        )
        checkpoint_file.write_text(json.dumps(checkpoint.to_dict(), indent=2))
        logger.info(f"Saved checkpoint: {checkpoint_file}")
        return checkpoint_file

    def load_checkpoint(self, checkpoint_id: str) -> Optional[ExecutionCheckpoint]:
        """Load checkpoint from disk"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.json"
        if checkpoint_file.exists():
            data = json.loads(checkpoint_file.read_text())
            return ExecutionCheckpoint.from_dict(data)
        return None

    def list_checkpoints(
        self, workflow_type: str = None, app_name: str = None
    ) -> List[ExecutionCheckpoint]:
        """List available checkpoints with optional filtering"""
        checkpoints = []

        for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                data = json.loads(checkpoint_file.read_text())
                checkpoint = ExecutionCheckpoint.from_dict(data)

                # Apply filters
                if workflow_type and checkpoint.workflow_type != workflow_type:
                    continue
                if app_name and checkpoint.app_name != app_name:
                    continue

                checkpoints.append(checkpoint)

            except Exception as e:
                logger.warning(f"Failed to load checkpoint {checkpoint_file}: {e}")

        return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)

    def create_checkpoint(
        self,
        workflow_type: str,
        app_name: str,
        completed_tasks: List[str],
        failed_tasks: List[str],
        pending_tasks: List[str],
        config: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> ExecutionCheckpoint:
        """Create new checkpoint"""

        checkpoint_id = (
            f"{workflow_type}_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        checkpoint = ExecutionCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            workflow_type=workflow_type,
            app_name=app_name,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            pending_tasks=pending_tasks,
            config=config,
            context=context or {},
        )

        self.save_checkpoint(checkpoint)
        return checkpoint

    def cleanup_old_checkpoints(self, keep_count: int = 10):
        """Clean up old checkpoints, keeping only the most recent ones"""
        checkpoints = self.list_checkpoints()

        if len(checkpoints) > keep_count:
            to_delete = checkpoints[keep_count:]

            for checkpoint in to_delete:
                checkpoint_file = (
                    self.checkpoint_dir / f"checkpoint_{checkpoint.checkpoint_id}.json"
                )
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
                    logger.info(
                        f"Cleaned up old checkpoint: {checkpoint.checkpoint_id}"
                    )


class ExecutionPlanManager:
    """Manages execution plans and workflow orchestration"""

    def __init__(self, plans_dir: Path):
        self.plans_dir = plans_dir
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.templates = ExecutionPlanTemplates()

    def save_plan(self, plan: ExecutionPlan) -> Path:
        """Save execution plan to disk"""
        plan_file = self.plans_dir / f"plan_{plan.plan_id}.json"
        plan_file.write_text(json.dumps(plan.to_dict(), indent=2))
        logger.info(f"Saved execution plan: {plan_file}")
        return plan_file

    def load_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Load execution plan from disk"""
        plan_file = self.plans_dir / f"plan_{plan_id}.json"
        if plan_file.exists():
            data = json.loads(plan_file.read_text())
            return ExecutionPlan.from_dict(data)
        return None

    def create_plan_from_template(
        self,
        template_name: str,
        app_name: str,
        app_root: str,
        output_dir: str = None,
        **kwargs,
    ) -> ExecutionPlan:
        """Create execution plan from template"""

        template_methods = {
            "comprehensive": self.templates.system_documentation_comprehensive,
            "standard": self.templates.system_documentation_standard,
            "minimal": self.templates.system_documentation_minimal,
            "api-focused": self.templates.api_documentation_focused,
        }

        if template_name not in template_methods:
            raise ValueError(
                f"Unknown template: {template_name}. Available: {list(template_methods.keys())}"
            )

        # Apply any additional kwargs to config
        plan = template_methods[template_name](app_name, app_root, output_dir)

        if kwargs:
            plan.config.update(kwargs)

        self.save_plan(plan)
        return plan

    def list_plans(self, workflow_type: str = None) -> List[ExecutionPlan]:
        """List available execution plans"""
        plans = []

        for plan_file in self.plans_dir.glob("plan_*.json"):
            try:
                data = json.loads(plan_file.read_text())
                plan = ExecutionPlan.from_dict(data)

                if workflow_type and plan.workflow_type != workflow_type:
                    continue

                plans.append(plan)

            except Exception as e:
                logger.warning(f"Failed to load plan {plan_file}: {e}")

        return plans

    def get_next_phase_tasks(
        self, plan: ExecutionPlan, completed_tasks: List[str]
    ) -> List[str]:
        """Get tasks for the next executable phase"""

        for phase in plan.phases:
            phase_tasks = phase["tasks"]

            # Check if any task in this phase is not completed
            if any(task not in completed_tasks for task in phase_tasks):
                # Check dependencies
                ready_tasks = []
                for task in phase_tasks:
                    if task in completed_tasks:
                        continue

                    # Check if all dependencies are satisfied
                    deps = plan.dependencies.get(task, [])
                    if all(dep in completed_tasks for dep in deps):
                        ready_tasks.append(task)

                return ready_tasks

        return []  # All phases completed or no ready tasks

    def is_checkpoint_phase(
        self, plan: ExecutionPlan, completed_tasks: List[str]
    ) -> bool:
        """Check if current state represents a checkpoint phase completion"""

        for phase in plan.phases:
            if not phase.get("checkpoint", False):
                continue

            phase_tasks = phase["tasks"]

            # If all tasks in this checkpoint phase are completed, it's a checkpoint
            if all(task in completed_tasks for task in phase_tasks):
                # But make sure we haven't already passed this checkpoint
                next_phase_idx = plan.phases.index(phase) + 1
                if next_phase_idx < len(plan.phases):
                    next_phase = plan.phases[next_phase_idx]
                    next_phase_tasks = next_phase["tasks"]

                    # If no tasks from next phase are completed, we're at checkpoint
                    if not any(task in completed_tasks for task in next_phase_tasks):
                        return True

        return False
