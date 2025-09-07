#!/usr/bin/env python3
"""
Execution Plan Adapter

Provides compatibility layer between ExecutionPlan schema and the
orchestrator's internal data structures (EnhancedAgentTask, QualityGateManager).
Handles type conversions, validation, and mapping between systems.
"""

import logging
import os

# Import orchestrator components
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from enhanced_orchestrator import EnhancedAgentTask
from quality_gates import QualityGateManager

# Add parent directory for execution_plan_schema
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from execution_plan_schema import (
    ExecutionMode,
    ExecutionPhase,
    ExecutionPlan,
    QualityGate,
    QualityGateType,
    TaskDefinition,
    TaskType,
    ValidationLevel,
)

logger = logging.getLogger(__name__)


class ExecutionPlanAdapter:
    """
    Adapter for converting ExecutionPlan objects to orchestrator-compatible formats.

    Handles type conversions, validation, and bridging between the ExecutionPlan
    schema and the enhanced orchestrator's internal structures.
    """

    def __init__(self, quality_gate_manager: Optional[QualityGateManager] = None):
        self.quality_gate_manager = quality_gate_manager
        self._task_type_mapping = self._build_task_type_mapping()
        self._gate_type_mapping = self._build_gate_type_mapping()

    def _build_task_type_mapping(self) -> Dict[TaskType, str]:
        """Build mapping from ExecutionPlan TaskType enum to orchestrator strings"""
        return {
            # Core agent types
            TaskType.GENERAL_PURPOSE: "general-purpose",
            TaskType.DEVELOPMENT_SPECIALIST: "development-specialist",
            TaskType.API_INTEGRATION_SPECIALIST: "api-integration-specialist",
            TaskType.QA_TESTING_GURU: "qa-testing-guru",
            TaskType.TECHNICAL_WRITER: "technical-writer",
            # Specialized agents
            TaskType.DATABASE_SPECIALIST: "database-specialist",
            TaskType.SECURITY_ARCHITECT: "security-architect",
            TaskType.PERFORMANCE_OPTIMIZER: "performance-optimizer",
            TaskType.SOLUTION_ARCHITECT: "solution-architect",
            TaskType.REQUIREMENTS_ANALYST: "requirements-analyst",
            # SDLC agents
            TaskType.SDLC_DISCOVERY: "sdlc-discovery",
            TaskType.SDLC_DESIGN: "sdlc-design",
            TaskType.SDLC_DEVELOPMENT: "sdlc-development",
            TaskType.SDLC_TESTING: "sdlc-testing",
            TaskType.SDLC_DEPLOYMENT: "sdlc-deployment",
            TaskType.SDLC_PRODUCTION: "sdlc-production",
        }

    def _build_gate_type_mapping(self) -> Dict[QualityGateType, str]:
        """Build mapping from ExecutionPlan QualityGateType to orchestrator strings"""
        return {
            QualityGateType.DATABASE: "database",
            QualityGateType.HTTP: "http",
            QualityGateType.FILE_EXISTS: "file_exists",
            QualityGateType.CODE_QUALITY: "code_quality",
            QualityGateType.TEST_RESULTS: "test_results",
            QualityGateType.CUSTOM: "custom",
        }

    def convert_task_type(self, task_type: Union[TaskType, str]) -> str:
        """Convert TaskType enum or custom string to orchestrator string"""
        if isinstance(task_type, TaskType):
            return self._task_type_mapping.get(task_type, task_type.value)
        return str(task_type)

    def convert_validation_level(self, level: ValidationLevel) -> bool:
        """Convert ValidationLevel to boolean validation_required flag"""
        return level != ValidationLevel.NONE

    def generate_deterministic_uuid(self, task_id: str, plan_id: str) -> str:
        """Generate deterministic UUID for predictable log file tracking"""
        # Use task_id and plan_id to create reproducible UUID
        seed_string = f"{plan_id}-{task_id}"
        # Create UUID from hash of seed string
        import hashlib

        hash_obj = hashlib.md5(seed_string.encode())
        hex_str = hash_obj.hexdigest()

        # Format as proper UUID
        uuid_str = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"
        return uuid_str

    def convert_task_definition(
        self, task_def: TaskDefinition, plan_id: str
    ) -> EnhancedAgentTask:
        """Convert TaskDefinition to EnhancedAgentTask"""

        # Generate deterministic UUID if not provided
        agent_uuid = getattr(task_def, "agent_uuid", None)
        if not agent_uuid:
            agent_uuid = self.generate_deterministic_uuid(task_def.task_id, plan_id)

        # Convert task type
        task_type_str = self.convert_task_type(task_def.task_type)

        # Build enhanced context
        enhanced_context = task_def.context.to_dict() if task_def.context else {}

        working_dir = getattr(task_def, "working_directory", None)
        if working_dir:
            enhanced_context["working_directory"] = working_dir

        output_files = getattr(task_def, "output_files", None)
        if output_files:
            enhanced_context["output_files"] = output_files

        resource_reqs = getattr(task_def, "resource_requirements", None)
        if resource_reqs:
            enhanced_context.update(resource_reqs)

        # Create enhanced agent task
        enhanced_task = EnhancedAgentTask(
            task_id=task_def.task_id,
            task_type=task_type_str,
            prompt=task_def.prompt,
            dependencies=task_def.dependencies,
            context=enhanced_context,
            # Enhanced features
            quality_gates=getattr(task_def, "quality_gates", []),
            validation_required=self.convert_validation_level(
                getattr(task_def, "validation_level", ValidationLevel.STANDARD)
            ),
            phase_id=getattr(task_def, "phase_id", None),
            agent_uuid=agent_uuid,
            team_id=getattr(task_def, "team_id", None),
            monitoring_enabled=getattr(task_def, "monitoring_enabled", True),
            background_execution=getattr(task_def, "background_execution", False),
        )

        return enhanced_task

    def convert_quality_gate(self, gate: QualityGate) -> Dict[str, Any]:
        """Convert QualityGate to QualityGateManager format"""

        gate_type_str = self._gate_type_mapping.get(
            gate.gate_type, gate.gate_type.value
        )

        return {
            "gate_id": gate.gate_id,
            "name": gate.name,
            "description": gate.description,
            "validator_type": gate_type_str,
            "config": gate.config,
            "dependencies": gate.dependencies,
            "timeout_seconds": gate.timeout_seconds,
            "retry_interval": getattr(gate, "retry_interval", 30),
            "max_retries": getattr(gate, "max_retries", 3),
            "enabled": gate.enabled,
            "critical": getattr(gate, "critical", False),
        }

    def convert_execution_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Convert complete ExecutionPlan to orchestrator-compatible format"""

        # Validate plan first
        validation_result = execution_plan.validate_comprehensive()
        if not validation_result.is_valid:
            raise ValueError(
                f"Invalid execution plan: {', '.join(validation_result.errors)}"
            )

        # Convert tasks
        enhanced_tasks = []
        for task_def in execution_plan.tasks:
            enhanced_task = self.convert_task_definition(
                task_def, execution_plan.plan_id
            )
            enhanced_tasks.append(enhanced_task)

        # Convert quality gates
        quality_gates = []
        for gate in execution_plan.quality_gates:
            gate_config = self.convert_quality_gate(gate)
            quality_gates.append(gate_config)

        # Build orchestrator configuration
        orchestrator_config = {
            "plan_id": execution_plan.plan_id,
            "name": execution_plan.name,
            "description": execution_plan.description,
            "execution_mode": execution_plan.execution_mode,
            "max_parallel": execution_plan.max_parallel_tasks,
            "enable_quality_gates": execution_plan.enable_quality_gates,
            "enable_monitoring": execution_plan.enable_monitoring,
            "use_optimizations": execution_plan.use_optimizations,
            "output_directory": execution_plan.output_directory,
            "token_requirements": getattr(
                execution_plan.resource_requirements, "estimated_tokens", 5
            )
            if execution_plan.resource_requirements
            else 5,
            "estimated_duration": execution_plan.estimated_total_duration_minutes,
            "fallback_strategy": execution_plan.fallback_strategy,
        }

        return {
            "tasks": enhanced_tasks,
            "quality_gates": quality_gates,
            "phases": execution_plan.phases,
            "config": orchestrator_config,
        }

    async def initialize_quality_gates(self, execution_plan: ExecutionPlan):
        """Initialize quality gates in the QualityGateManager"""

        if not self.quality_gate_manager:
            logger.warning(
                "No QualityGateManager available - skipping gate initialization"
            )
            return

        # Define gates
        for gate in execution_plan.quality_gates:
            if gate.enabled:
                gate_config = self.convert_quality_gate(gate)

                try:
                    await self.quality_gate_manager.define_gate(
                        gate_id=gate_config["gate_id"],
                        name=gate_config["name"],
                        description=gate_config["description"],
                        validator_type=gate_config["validator_type"],
                        config=gate_config["config"],
                        dependencies=gate_config["dependencies"],
                        timeout_seconds=gate_config["timeout_seconds"],
                        retry_interval=gate_config["retry_interval"],
                        max_retries=gate_config["max_retries"],
                    )

                    logger.info(f"Initialized quality gate: {gate.gate_id}")

                except Exception as e:
                    logger.error(
                        f"Failed to initialize quality gate {gate.gate_id}: {e}"
                    )
                    raise

        # Define phases
        for phase in execution_plan.phases:
            try:
                await self.quality_gate_manager.define_phase(
                    phase_id=phase.phase_id,
                    name=phase.name,
                    description=phase.description,
                    gates=phase.gates,
                )

                logger.info(f"Initialized execution phase: {phase.phase_id}")

            except Exception as e:
                logger.error(f"Failed to initialize phase {phase.phase_id}: {e}")
                raise

        # Start validation loop
        try:
            await self.quality_gate_manager.start_validation_loop()
            logger.info("Quality gate validation loop started")
        except Exception as e:
            logger.error(f"Failed to start quality gate validation loop: {e}")
            raise

    def get_execution_order_batches(
        self, execution_plan: ExecutionPlan
    ) -> List[List[str]]:
        """Get task execution order respecting dependencies"""
        try:
            return execution_plan.get_execution_order()
        except ValueError as e:
            logger.error(f"Failed to determine execution order: {e}")
            raise

    def estimate_resource_requirements(
        self, execution_plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """Estimate resource requirements for the execution plan"""

        total_tasks = len(execution_plan.tasks)
        max_parallel = min(execution_plan.max_parallel_tasks, total_tasks)

        # Calculate token requirements
        token_requirement = max(execution_plan.token_requirements, max_parallel)

        # Estimate duration
        estimated_duration = execution_plan.estimated_total_duration_minutes
        if not estimated_duration:
            # Fallback estimation based on task count
            task_durations = [
                task.estimated_duration_minutes or 30  # Default 30 min per task
                for task in execution_plan.tasks
            ]
            estimated_duration = sum(task_durations) / max_parallel

        # Count background tasks
        background_tasks = len(
            [task for task in execution_plan.tasks if task.background_execution]
        )

        return {
            "total_tasks": total_tasks,
            "max_parallel_tasks": max_parallel,
            "token_requirement": token_requirement,
            "estimated_duration_minutes": estimated_duration,
            "background_task_count": background_tasks,
            "quality_gate_count": len(execution_plan.quality_gates),
            "phase_count": len(execution_plan.phases),
            "monitoring_enabled": execution_plan.enable_monitoring,
            "quality_gates_enabled": execution_plan.enable_quality_gates,
        }

    def validate_orchestrator_compatibility(
        self, execution_plan: ExecutionPlan
    ) -> List[str]:
        """Validate that execution plan is compatible with orchestrator capabilities"""

        warnings = []

        # Check task types
        for task in execution_plan.tasks:
            if isinstance(task.task_type, TaskType):
                if task.task_type not in self._task_type_mapping:
                    warnings.append(f"Unknown task type: {task.task_type}")
            # Custom string task types are allowed

        # Check quality gate types
        for gate in execution_plan.quality_gates:
            if gate.gate_type not in self._gate_type_mapping:
                warnings.append(f"Unknown quality gate type: {gate.gate_type}")

        # Check execution mode support
        if execution_plan.execution_mode == ExecutionMode.MIXED:
            warnings.append(
                "MIXED execution mode requires careful dependency management"
            )

        # Check resource requirements
        if execution_plan.max_parallel_tasks > 50:
            warnings.append(
                f"High parallel task count ({execution_plan.max_parallel_tasks}) may cause resource issues"
            )

        # Check background execution
        background_count = len(
            [t for t in execution_plan.tasks if t.background_execution]
        )
        if background_count > execution_plan.max_parallel_tasks:
            warnings.append(
                f"More background tasks ({background_count}) than max parallel ({execution_plan.max_parallel_tasks})"
            )

        return warnings


def create_execution_plan_from_json(json_path: Union[str, Path]) -> ExecutionPlan:
    """Load ExecutionPlan from JSON file"""

    import json

    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"ExecutionPlan file not found: {json_path}")

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        return ExecutionPlan.from_dict(data)

    except Exception as e:
        raise ValueError(f"Failed to load ExecutionPlan from {json_path}: {e}")


def save_execution_plan_to_json(
    execution_plan: ExecutionPlan, json_path: Union[str, Path]
):
    """Save ExecutionPlan to JSON file"""

    import json

    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(json_path, "w") as f:
            json.dump(execution_plan.to_dict(), f, indent=2)

        logger.info(f"ExecutionPlan saved to {json_path}")

    except Exception as e:
        raise ValueError(f"Failed to save ExecutionPlan to {json_path}: {e}")
