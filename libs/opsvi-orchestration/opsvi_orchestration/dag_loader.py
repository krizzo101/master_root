"""DAG loader for converting YAML pipeline definitions to executable graphs."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, Field

from .task_models import TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class TaskDefinition(BaseModel):
    """Definition of a task in a pipeline."""

    name: str
    agent: str
    type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)

    # Flow control
    gate_policies: List[str] = Field(default_factory=list)
    max_loops: int = 1
    fallback_task: Optional[str] = None

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Parallel execution
    parallel: bool = False
    parallel_group: Optional[str] = None


class PipelineDefinition(BaseModel):
    """Definition of a complete pipeline."""

    name: str
    version: str = "1.0"
    description: str = ""

    # Tasks
    tasks: List[TaskDefinition]

    # Global configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Validation
    required_agents: List[str] = Field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate the pipeline definition."""
        errors = []

        # Check for circular dependencies
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in pipeline")

        # Check for missing dependencies
        task_names = {task.name for task in self.tasks}
        for task in self.tasks:
            for dep in task.depends_on:
                if dep not in task_names:
                    errors.append(f"Task '{task.name}' depends on unknown task '{dep}'")

        # Check for missing fallback tasks
        for task in self.tasks:
            if task.fallback_task and task.fallback_task not in task_names:
                errors.append(
                    f"Task '{task.name}' has unknown fallback task '{task.fallback_task}'"
                )

        return errors

    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies using DFS."""

        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            # Find the task
            task = next((t for t in self.tasks if t.name == node), None)
            if not task:
                return False

            for dep in task.depends_on:
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for task in self.tasks:
            if task.name not in visited:
                if has_cycle(task.name, visited, set()):
                    return True
        return False

    def get_task_dependencies(self, task_name: str) -> List[str]:
        """Get all dependencies for a task (including transitive)."""

        def get_deps(node: str, visited: Set[str]) -> Set[str]:
            if node in visited:
                return set()

            visited.add(node)
            deps = set()

            task = next((t for t in self.tasks if t.name == node), None)
            if task:
                for dep in task.depends_on:
                    deps.add(dep)
                    deps.update(get_deps(dep, visited))

            return deps

        return list(get_deps(task_name, set()))

    def get_execution_order(self) -> List[str]:
        """Get the topological sort order for task execution."""
        # Kahn's algorithm for topological sorting
        in_degree = {task.name: 0 for task in self.tasks}

        # Calculate in-degrees
        for task in self.tasks:
            for dep in task.depends_on:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find tasks with no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Update in-degrees for dependent tasks
            task = next((t for t in self.tasks if t.name == current), None)
            if task:
                for dep in task.depends_on:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        # Check for cycles
        if len(result) != len(self.tasks):
            raise ValueError("Pipeline has circular dependencies")

        return result

    def get_parallel_groups(self) -> Dict[str, List[str]]:
        """Get tasks grouped by parallel execution groups."""
        groups = {}
        for task in self.tasks:
            if task.parallel and task.parallel_group:
                if task.parallel_group not in groups:
                    groups[task.parallel_group] = []
                groups[task.parallel_group].append(task.name)
        return groups


class DAGLoader:
    """Loader for DAG pipeline definitions."""

    def __init__(self, pipeline_dir: Optional[Path] = None) -> None:
        """Initialize the DAG loader."""
        self.pipeline_dir = pipeline_dir or Path("pipelines")
        self._loaded_pipelines: Dict[str, PipelineDefinition] = {}

    def load_pipeline(self, name: str) -> PipelineDefinition:
        """Load a pipeline definition by name."""
        if name in self._loaded_pipelines:
            return self._loaded_pipelines[name]

        # Try to load from file
        pipeline_file = self.pipeline_dir / f"{name}.yaml"
        if not pipeline_file.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_file}")

        try:
            with open(pipeline_file, "r") as f:
                data = yaml.safe_load(f)

            pipeline = PipelineDefinition(**data)

            # Validate the pipeline
            errors = pipeline.validate()
            if errors:
                raise ValueError(f"Pipeline validation failed: {'; '.join(errors)}")

            self._loaded_pipelines[name] = pipeline
            logger.info(f"Loaded pipeline: {name}")
            return pipeline

        except Exception as e:
            logger.error(f"Failed to load pipeline {name}: {e}")
            raise

    def list_pipelines(self) -> List[str]:
        """List available pipeline names."""
        if not self.pipeline_dir.exists():
            return []

        pipelines = []
        for file in self.pipeline_dir.glob("*.yaml"):
            pipelines.append(file.stem)
        return pipelines

    def create_task_record(
        self,
        task_def: TaskDefinition,
        project_id: str,
        run_id: str,
        parent_task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a task record from a task definition."""
        from .task_models import TaskRecord

        return TaskRecord(
            name=task_def.name,
            task_type=task_def.type,
            priority=task_def.priority,
            project_id=project_id,
            run_id=run_id,
            parent_task_id=parent_task_id,
            depends_on=task_def.depends_on,
            gate_policies=task_def.gate_policies,
            max_loops=task_def.max_loops,
            fallback_task=task_def.fallback_task,
            agent_path=task_def.agent,
            agent_config=task_def.config,
        ).dict()

    def create_execution_plan(
        self,
        pipeline_name: str,
        project_id: str,
        run_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create an execution plan for a pipeline."""
        pipeline = self.load_pipeline(pipeline_name)

        # Get execution order
        execution_order = pipeline.get_execution_order()

        # Create task records
        task_records = {}
        for task_def in pipeline.tasks:
            task_record = self.create_task_record(task_def, project_id, run_id)
            task_records[task_def.name] = task_record

        # Get parallel groups
        parallel_groups = pipeline.get_parallel_groups()

        return {
            "pipeline": pipeline.dict(),
            "execution_order": execution_order,
            "task_records": task_records,
            "parallel_groups": parallel_groups,
            "input_data": input_data,
            "config": pipeline.config,
        }


# Global loader instance
dag_loader = DAGLoader()
