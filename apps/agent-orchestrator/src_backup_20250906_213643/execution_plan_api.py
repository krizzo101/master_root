#!/usr/bin/env python3
"""
ExecutionPlan API Engine

Based on the Web API System Architecture design, this module provides:
- ExecutionPlan API engine built on GenericOrchestrator foundation
- Schema validation for ExecutionPlan (missing component from research)
- Storage layer for plans, results, and state
- Integration with proven orchestrator patterns
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

# Import orchestrator components
from .generic_orchestrator import AgentTask, GenericOrchestrator

# Try to import ExecutionPlan components
try:
    from .execution_plan import ExecutionMode, ExecutionPlan

    EXECUTION_PLAN_AVAILABLE = True
except ImportError:
    ExecutionPlan = None
    ExecutionMode = None
    EXECUTION_PLAN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ExecutionPlanResponse:
    """Response structure for ExecutionPlan operations"""

    success: bool
    plan_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    results: Optional[List[Dict]] = None
    data: Optional[Dict] = None


@dataclass
class ValidationResult:
    """Schema validation result"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ExecutionPlanSchemaValidator:
    """
    Schema validation for ExecutionPlan (missing component from research)
    Implements the minimum ExecutionPlan spec requirements
    """

    MINIMUM_PLAN_SCHEMA = {
        "type": "object",
        "required": ["plan_id", "name", "tasks"],
        "properties": {
            "plan_id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "version": {"type": "string", "default": "1.0"},
            "tasks": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["task_id", "task_type", "prompt"],
                    "properties": {
                        "task_id": {"type": "string", "minLength": 1},
                        "task_type": {"type": "string", "minLength": 1},
                        "prompt": {"type": "string", "minLength": 1},
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                        "context": {"type": "object", "default": {}},
                        "timeout_seconds": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 3600,
                            "default": 300,
                        },
                    },
                },
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "created_by": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium",
                    },
                },
            },
        },
    }

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SchemaValidator")

    async def validate_plan(self, plan_data: Dict) -> ValidationResult:
        """Validate ExecutionPlan against minimum schema"""

        try:
            # Basic JSON schema validation
            jsonschema.validate(plan_data, self.MINIMUM_PLAN_SCHEMA)

            # Additional business logic validation
            errors = []
            warnings = []

            # Check for circular dependencies
            if self._has_circular_dependencies(plan_data.get("tasks", [])):
                errors.append("Circular dependencies detected in task graph")

            # Check for orphaned tasks
            orphaned = self._find_orphaned_tasks(plan_data.get("tasks", []))
            if orphaned:
                warnings.append(f"Tasks with unresolved dependencies: {orphaned}")

            # Validate task types
            invalid_types = self._validate_task_types(plan_data.get("tasks", []))
            if invalid_types:
                warnings.append(f"Unknown task types: {invalid_types}")

            return ValidationResult(
                is_valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        except jsonschema.ValidationError as e:
            self.logger.error(f"Schema validation failed: {e}")
            return ValidationResult(
                is_valid=False, errors=[f"Schema validation error: {e.message}"]
            )

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False, errors=[f"Validation failed: {str(e)}"]
            )

    def _has_circular_dependencies(self, tasks: List[Dict]) -> bool:
        """Check for circular dependencies in task graph"""

        # Build dependency graph
        graph = {}
        for task in tasks:
            task_id = task.get("task_id")
            dependencies = task.get("dependencies", [])
            graph[task_id] = dependencies

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            if node not in graph:
                return False

            if node in rec_stack:
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for task_id in graph:
            if has_cycle(task_id):
                return True

        return False

    def _find_orphaned_tasks(self, tasks: List[Dict]) -> List[str]:
        """Find tasks with dependencies that don't exist"""

        task_ids = {task.get("task_id") for task in tasks}
        orphaned = []

        for task in tasks:
            dependencies = task.get("dependencies", [])
            for dep in dependencies:
                if dep not in task_ids:
                    orphaned.append(task.get("task_id"))
                    break

        return orphaned

    def _validate_task_types(self, tasks: List[Dict]) -> List[str]:
        """Validate task types against known types"""

        known_types = {
            "general-purpose",
            "code-analyzer",
            "web-scraper",
            "data-processor",
            "file-processor",
            "api-caller",
            "validation",
            "monitoring",
        }

        invalid_types = []
        for task in tasks:
            task_type = task.get("task_type")
            if task_type and task_type not in known_types:
                invalid_types.append(task_type)

        return list(set(invalid_types))  # Remove duplicates


class ExecutionPlanStorage:
    """
    Storage layer for ExecutionPlan data
    Uses file-based storage with JSON for simplicity
    Can be extended to use database later
    """

    def __init__(self, storage_dir: str = "execution_plans"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.Storage")

    async def store_plan(self, plan: Dict) -> str:
        """Store execution plan"""

        plan_id = plan.get("plan_id", str(uuid.uuid4()))
        plan_file = self.storage_dir / f"{plan_id}.json"

        # Add metadata
        storage_data = {
            "plan": plan,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "version": "1.0",
            },
            "results": None,
        }

        try:
            with open(plan_file, "w") as f:
                json.dump(storage_data, f, indent=2)

            self.logger.info(f"Stored plan: {plan_id}")
            return plan_id

        except Exception as e:
            self.logger.error(f"Failed to store plan {plan_id}: {e}")
            raise

    async def get_plan(self, plan_id: str) -> Optional[Dict]:
        """Retrieve execution plan"""

        plan_file = self.storage_dir / f"{plan_id}.json"

        try:
            if plan_file.exists():
                with open(plan_file, "r") as f:
                    data = json.load(f)
                return data.get("plan")
            else:
                self.logger.warning(f"Plan not found: {plan_id}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to retrieve plan {plan_id}: {e}")
            return None

    async def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status"""

        plan_file = self.storage_dir / f"{plan_id}.json"

        try:
            if plan_file.exists():
                with open(plan_file, "r") as f:
                    data = json.load(f)

                data["metadata"]["status"] = status
                data["metadata"]["updated_at"] = datetime.now().isoformat()

                with open(plan_file, "w") as f:
                    json.dump(data, f, indent=2)

                self.logger.info(f"Updated plan status: {plan_id} -> {status}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to update plan status {plan_id}: {e}")
            return False

    async def store_results(self, plan_id: str, results: List[Dict]) -> bool:
        """Store execution results"""

        plan_file = self.storage_dir / f"{plan_id}.json"

        try:
            if plan_file.exists():
                with open(plan_file, "r") as f:
                    data = json.load(f)

                data["results"] = results
                data["metadata"]["status"] = "completed"
                data["metadata"]["completed_at"] = datetime.now().isoformat()

                with open(plan_file, "w") as f:
                    json.dump(data, f, indent=2)

                self.logger.info(f"Stored results for plan: {plan_id}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to store results for plan {plan_id}: {e}")
            return False

    async def list_plans(self, status: Optional[str] = None) -> List[Dict]:
        """List all plans with optional status filter"""

        plans = []

        try:
            for plan_file in self.storage_dir.glob("*.json"):
                with open(plan_file, "r") as f:
                    data = json.load(f)

                plan_info = {
                    "plan_id": data["plan"]["plan_id"],
                    "name": data["plan"]["name"],
                    "status": data["metadata"]["status"],
                    "created_at": data["metadata"]["created_at"],
                }

                if status is None or plan_info["status"] == status:
                    plans.append(plan_info)

            return plans

        except Exception as e:
            self.logger.error(f"Failed to list plans: {e}")
            return []


class ExecutionPlanAPIEngine:
    """
    ExecutionPlan API engine built on GenericOrchestrator foundation
    Addresses the missing ExecutionPlan components identified in research
    """

    def __init__(self, storage_dir: str = "execution_plans"):
        self.orchestrator = GenericOrchestrator()  # Use proven working foundation
        self.schema_validator = ExecutionPlanSchemaValidator()
        self.plan_storage = ExecutionPlanStorage(storage_dir)
        self.logger = logging.getLogger(f"{__name__}.APIEngine")

    async def create_execution_plan(self, plan_data: Dict) -> ExecutionPlanResponse:
        """Create new execution plan with validation"""

        try:
            self.logger.info(
                f"Creating execution plan: {plan_data.get('name', 'unnamed')}"
            )

            # Schema validation (missing component from research)
            validation = await self.schema_validator.validate_plan(plan_data)
            if not validation.is_valid:
                return ExecutionPlanResponse(
                    success=False,
                    error=f"Schema validation failed: {validation.errors}",
                )

            # Store plan
            plan_id = await self.plan_storage.store_plan(plan_data)

            result = ExecutionPlanResponse(
                success=True, plan_id=plan_id, status="created"
            )

            if validation.warnings:
                result.data = {"warnings": validation.warnings}

            return result

        except Exception as e:
            self.logger.error(f"Failed to create execution plan: {e}")
            return ExecutionPlanResponse(success=False, error=str(e))

    async def get_execution_plan(self, plan_id: str) -> ExecutionPlanResponse:
        """Get execution plan by ID"""

        try:
            plan = await self.plan_storage.get_plan(plan_id)
            if not plan:
                return ExecutionPlanResponse(success=False, error="Plan not found")

            return ExecutionPlanResponse(
                success=True, plan_id=plan_id, data=plan, status="retrieved"
            )

        except Exception as e:
            self.logger.error(f"Failed to get execution plan {plan_id}: {e}")
            return ExecutionPlanResponse(success=False, error=str(e))

    async def execute_plan(self, plan_id: str) -> ExecutionPlanResponse:
        """Execute plan using GenericOrchestrator foundation"""

        try:
            self.logger.info(f"Executing plan: {plan_id}")

            # Load plan
            plan = await self.plan_storage.get_plan(plan_id)
            if not plan:
                return ExecutionPlanResponse(success=False, error="Plan not found")

            # Update status to executing
            await self.plan_storage.update_plan_status(plan_id, "executing")

            # Convert ExecutionPlan to AgentTask objects (proven working)
            agent_tasks = await self.convert_plan_to_tasks(plan)

            # Execute using proven GenericOrchestrator
            self.logger.info(f"Executing {len(agent_tasks)} tasks")
            results = await self.orchestrator.execute_batch(agent_tasks)

            # Store results
            await self.plan_storage.store_results(plan_id, results)

            return ExecutionPlanResponse(
                success=True, plan_id=plan_id, status="completed", results=results
            )

        except Exception as e:
            self.logger.error(f"Failed to execute plan {plan_id}: {e}")
            await self.plan_storage.update_plan_status(plan_id, "failed")
            return ExecutionPlanResponse(success=False, error=str(e))

    async def delete_plan(self, plan_id: str) -> ExecutionPlanResponse:
        """Delete execution plan"""

        try:
            plan_file = Path("execution_plans") / f"{plan_id}.json"
            if plan_file.exists():
                plan_file.unlink()
                self.logger.info(f"Deleted plan: {plan_id}")
                return ExecutionPlanResponse(
                    success=True, plan_id=plan_id, status="deleted"
                )
            else:
                return ExecutionPlanResponse(success=False, error="Plan not found")

        except Exception as e:
            self.logger.error(f"Failed to delete plan {plan_id}: {e}")
            return ExecutionPlanResponse(success=False, error=str(e))

    async def list_plans(self, status: Optional[str] = None) -> ExecutionPlanResponse:
        """List execution plans"""

        try:
            plans = await self.plan_storage.list_plans(status)
            return ExecutionPlanResponse(
                success=True, status="listed", data={"plans": plans}
            )

        except Exception as e:
            self.logger.error(f"Failed to list plans: {e}")
            return ExecutionPlanResponse(success=False, error=str(e))

    async def convert_plan_to_tasks(self, plan: Dict) -> List[AgentTask]:
        """
        Convert ExecutionPlan tasks to AgentTask objects
        Based on minimum working spec from research findings
        """

        tasks = []

        for task_data in plan.get("tasks", []):
            task = AgentTask(
                task_id=task_data.get("task_id"),
                task_type=task_data.get("task_type"),
                prompt=task_data.get("prompt"),
                dependencies=task_data.get("dependencies", []),
                context=task_data.get("context", {}),
            )
            tasks.append(task)

        self.logger.info(f"Converted {len(tasks)} plan tasks to AgentTask objects")
        return tasks
