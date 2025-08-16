"""
Workflow Template Parser for Universal Workflow Engine

Parses YAML workflow templates and produces an in-memory representation for execution.
Supports Schema v2.0 workflow format with enhanced features including phases, 
dependencies, quality gates, and error handling.
"""
import yaml
import os
from typing import Any, Dict, List, Optional
from string import Template


class WorkflowParserError(Exception):
    """Exception raised for workflow parsing errors."""

    pass


class WorkflowParser:
    def __init__(self, template_path: str, variables: Optional[Dict[str, str]] = None):
        self.template_path = template_path
        self.variables = variables or {}
        self.workflow_def: Dict[str, Any] = {}
        self._validated = False

    def load(self) -> Dict[str, Any]:
        """Load and parse workflow template with variable substitution."""
        if not os.path.exists(self.template_path):
            raise WorkflowParserError(
                f"Workflow template not found: {self.template_path}"
            )

        try:
            with open(self.template_path, "r") as f:
                content = f.read()

            # Perform variable substitution
            if self.variables:
                template = Template(content)
                content = template.safe_substitute(self.variables)

            self.workflow_def = yaml.safe_load(content)

        except yaml.YAMLError as e:
            raise WorkflowParserError(f"YAML parsing error: {e}")
        except Exception as e:
            raise WorkflowParserError(f"Error loading workflow: {e}")

        return self.workflow_def

    def get_steps(self) -> List[Dict[str, Any]]:
        """Get workflow steps with dependency resolution."""
        if not self.workflow_def:
            self.load()
        steps = self.workflow_def.get("workflow", [])
        return self._resolve_step_dependencies(steps)

    def get_phases(self) -> List[str]:
        """Get list of workflow phases."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("phases", [])

    def get_quality_gates(self) -> Dict[str, str]:
        """Get quality gate definitions."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("quality_gates", {})

    def get_error_handling(self) -> Dict[str, Any]:
        """Get error handling configuration."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("error_handling", {})

    def get_inputs(self) -> List[str]:
        """Get required inputs."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("inputs_required", [])

    def get_outputs(self) -> List[str]:
        """Get expected outputs."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("expected_outputs", [])

    def get_metadata(self) -> Dict[str, Any]:
        """Get workflow metadata including name, description, etc."""
        if not self.workflow_def:
            self.load()
        return {
            "name": self.workflow_def.get("name", ""),
            "description": self.workflow_def.get("description", ""),
            "version": self.workflow_def.get("version", ""),
            "agent_profile": self.workflow_def.get("agent_profile", ""),
        }

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring and logging configuration."""
        if not self.workflow_def:
            self.load()
        return self.workflow_def.get("monitoring", {})

    def _resolve_step_dependencies(
        self, steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve and validate step dependencies."""
        step_ids = {step.get("id") for step in steps}

        for step in steps:
            depends_on = step.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]

            # Validate dependencies exist
            for dep in depends_on:
                if dep not in step_ids:
                    raise WorkflowParserError(
                        f"Step '{step.get('id')}' depends on non-existent step '{dep}'"
                    )

        return steps

    def validate_workflow(self) -> List[str]:
        """Validate workflow structure and return list of issues."""
        if not self.workflow_def:
            self.load()

        issues = []

        # Check required fields
        required_fields = ["workflow", "inputs_required", "expected_outputs"]
        for field in required_fields:
            if field not in self.workflow_def:
                issues.append(f"Missing required field: {field}")

        # Validate steps
        steps = self.workflow_def.get("workflow", [])
        if not steps:
            issues.append("No workflow steps defined")
        else:
            step_ids = set()
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    issues.append(f"Step {i} is not a dictionary")
                    continue

                step_id = step.get("id")
                if not step_id:
                    issues.append(f"Step {i} missing required 'id' field")
                elif step_id in step_ids:
                    issues.append(f"Duplicate step ID: {step_id}")
                else:
                    step_ids.add(step_id)

        # Check for circular dependencies
        if not issues:  # Only check if basic structure is valid
            try:
                self._check_circular_dependencies(steps)
            except WorkflowParserError as e:
                issues.append(str(e))

        self._validated = len(issues) == 0
        return issues

    def _check_circular_dependencies(self, steps: List[Dict[str, Any]]) -> None:
        """Check for circular dependencies in step definitions."""
        # Build dependency graph
        graph = {}
        for step in steps:
            step_id = step.get("id")
            depends_on = step.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            graph[step_id] = depends_on

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    raise WorkflowParserError(
                        f"Circular dependency detected involving step: {node}"
                    )

    def is_valid(self) -> bool:
        """Check if workflow has been validated successfully."""
        if not self._validated:
            issues = self.validate_workflow()
            return len(issues) == 0
        return True

    def set_variables(self, variables: Dict[str, str]) -> None:
        """Update template variables and reload workflow."""
        self.variables.update(variables)
        self.workflow_def = {}
        self._validated = False
