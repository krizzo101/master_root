"""
OAMAT Workflow Orchestrator - Utilities

Helper functions and utilities for workflow orchestration.
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Tuple

from src.applications.oamat.workflows.orchestrator.state import AgenticWorkflowState

logger = logging.getLogger("OrchestratorUtilities")


class WorkflowVisualizer:
    """Utilities for visualizing workflow execution"""

    @staticmethod
    def generate_execution_summary(state: AgenticWorkflowState) -> Dict[str, Any]:
        """Generate a comprehensive execution summary"""
        planned_nodes = state.get("planned_nodes", [])
        completed_nodes = state.get("completed_nodes", [])
        failed_nodes = state.get("failed_nodes", [])
        node_outputs = state.get("node_outputs", {})

        total_nodes = len(planned_nodes)
        completed_count = len(completed_nodes)
        failed_count = len(failed_nodes)

        success_rate = (completed_count / total_nodes * 100) if total_nodes > 0 else 0

        return {
            "workflow_id": state.get("workflow_id", "unknown"),
            "current_phase": state.get("current_phase", "unknown"),
            "execution_stats": {
                "total_nodes": total_nodes,
                "completed": completed_count,
                "failed": failed_count,
                "remaining": total_nodes - completed_count - failed_count,
                "success_rate": round(success_rate, 2),
            },
            "node_details": {
                "completed": completed_nodes,
                "failed": failed_nodes,
                "outputs_available": list(node_outputs.keys()),
            },
            "current_task": state.get("current_task"),
            "next_agent": state.get("next_agent"),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def create_workflow_diagram(state: AgenticWorkflowState) -> str:
        """Create a Mermaid diagram representation of the workflow"""
        planned_nodes = state.get("planned_nodes", [])
        completed_nodes = state.get("completed_nodes", [])
        failed_nodes = state.get("failed_nodes", [])
        current_task = state.get("current_task", {})

        # Start building Mermaid flowchart
        diagram_lines = ["graph TD"]

        # Add nodes with status styling
        for i, node in enumerate(planned_nodes):
            node_id = f"N{i}"
            node_name = node.get("agent_role", f"Node_{i}")

            if node_name in completed_nodes:
                # Completed nodes - green
                diagram_lines.append(f'    {node_id}["{node_name}"]:::completed')
            elif node_name in failed_nodes:
                # Failed nodes - red
                diagram_lines.append(f'    {node_id}["{node_name}"]:::failed')
            elif current_task and current_task.get("agent_role") == node_name:
                # Current node - yellow
                diagram_lines.append(f'    {node_id}["{node_name}"]:::current')
            else:
                # Pending nodes - default
                diagram_lines.append(f'    {node_id}["{node_name}"]')

        # Add connections based on dependencies
        for i, node in enumerate(planned_nodes):
            node_id = f"N{i}"
            dependencies = node.get("dependencies", [])

            for dep in dependencies:
                # Find the dependency node index
                for j, dep_node in enumerate(planned_nodes):
                    if dep_node.get("agent_role") == dep:
                        dep_id = f"N{j}"
                        diagram_lines.append(f"    {dep_id} --> {node_id}")
                        break

        # Add styling
        diagram_lines.extend(
            [
                "",
                "    classDef completed fill:#2d5a2d,stroke:#4caf50,stroke-width:2px,color:#ffffff",
                "    classDef failed fill:#5a2d2d,stroke:#f44336,stroke-width:2px,color:#ffffff",
                "    classDef current fill:#5a5a2d,stroke:#ffeb3b,stroke-width:3px,color:#000000",
            ]
        )

        return "\n".join(diagram_lines)


class WorkflowMetrics:
    """Utilities for tracking and analyzing workflow metrics"""

    @staticmethod
    def calculate_execution_metrics(state: AgenticWorkflowState) -> Dict[str, Any]:
        """Calculate detailed execution metrics"""
        planned_nodes = state.get("planned_nodes", [])
        completed_nodes = state.get("completed_nodes", [])
        failed_nodes = state.get("failed_nodes", [])
        node_outputs = state.get("node_outputs", {})

        total_nodes = len(planned_nodes)

        metrics = {
            "completion_rate": (
                len(completed_nodes) / total_nodes if total_nodes > 0 else 0
            ),
            "failure_rate": len(failed_nodes) / total_nodes if total_nodes > 0 else 0,
            "progress_percentage": (
                len(completed_nodes) / total_nodes * 100 if total_nodes > 0 else 0
            ),
            "nodes_with_outputs": len(node_outputs),
            "output_coverage": (
                len(node_outputs) / len(completed_nodes) if completed_nodes else 0
            ),
        }

        # Agent type distribution
        agent_types = {}
        for node in planned_nodes:
            agent_role = node.get("agent_role", "unknown")
            agent_types[agent_role] = agent_types.get(agent_role, 0) + 1

        metrics["agent_distribution"] = agent_types

        # Dependency analysis
        total_dependencies = sum(
            len(node.get("dependencies", [])) for node in planned_nodes
        )
        metrics["avg_dependencies_per_node"] = (
            total_dependencies / total_nodes if total_nodes > 0 else 0
        )

        return metrics

    @staticmethod
    def track_performance_metrics(
        state: AgenticWorkflowState, execution_time: float
    ) -> Dict[str, Any]:
        """Track performance metrics for the workflow execution"""
        completed_nodes = state.get("completed_nodes", [])
        total_nodes = len(state.get("planned_nodes", []))

        performance_metrics = {
            "total_execution_time": execution_time,
            "avg_time_per_node": (
                execution_time / len(completed_nodes) if completed_nodes else 0
            ),
            "nodes_per_minute": (
                len(completed_nodes) / (execution_time / 60)
                if execution_time > 0
                else 0
            ),
            "estimated_completion_time": (
                execution_time * (total_nodes / len(completed_nodes))
                if completed_nodes
                else 0
            ),
        }

        return performance_metrics


class WorkflowValidator:
    """Utilities for validating workflow state and configuration"""

    @staticmethod
    def validate_workflow_state(state: AgenticWorkflowState) -> Tuple[bool, List[str]]:
        """Validate the current workflow state for consistency"""
        errors = []

        # Required fields validation
        required_fields = [
            "workflow_id",
            "user_request",
            "current_phase",
            "planned_nodes",
        ]
        for field in required_fields:
            if field not in state or not state[field]:
                errors.append(f"Missing required field: {field}")

        # Consistency checks
        completed_nodes = state.get("completed_nodes", [])
        failed_nodes = state.get("failed_nodes", [])
        planned_nodes = state.get("planned_nodes", [])

        # Check for overlap between completed and failed nodes
        overlap = set(completed_nodes) & set(failed_nodes)
        if overlap:
            errors.append(f"Nodes cannot be both completed and failed: {overlap}")

        # Check if completed/failed nodes exist in planned nodes
        planned_node_names = {node.get("agent_role") for node in planned_nodes}

        invalid_completed = set(completed_nodes) - planned_node_names
        if invalid_completed:
            errors.append(f"Completed nodes not in planned nodes: {invalid_completed}")

        invalid_failed = set(failed_nodes) - planned_node_names
        if invalid_failed:
            errors.append(f"Failed nodes not in planned nodes: {invalid_failed}")

        # Validate current task
        current_task = state.get("current_task")
        if current_task:
            task_agent = current_task.get("agent_role")
            if task_agent and task_agent not in planned_node_names:
                errors.append(f"Current task agent not in planned nodes: {task_agent}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_node_dependencies(
        planned_nodes: List[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """Validate node dependencies for circular references and missing nodes"""
        errors = []
        node_names = {node.get("agent_role") for node in planned_nodes}

        # Check for missing dependencies
        for node in planned_nodes:
            dependencies = node.get("dependencies", [])
            missing_deps = set(dependencies) - node_names
            if missing_deps:
                node_name = node.get("agent_role", "unknown")
                errors.append(
                    f"Node '{node_name}' has missing dependencies: {missing_deps}"
                )

        # Check for circular dependencies (simplified check)
        def has_circular_dependency(node_name: str, visited: set, path: set) -> bool:
            if node_name in path:
                return True
            if node_name in visited:
                return False

            visited.add(node_name)
            path.add(node_name)

            # Find node and check its dependencies
            for node in planned_nodes:
                if node.get("agent_role") == node_name:
                    for dep in node.get("dependencies", []):
                        if has_circular_dependency(dep, visited, path):
                            return True
                    break

            path.remove(node_name)
            return False

        visited = set()
        for node in planned_nodes:
            node_name = node.get("agent_role")
            if node_name and node_name not in visited:
                if has_circular_dependency(node_name, visited, set()):
                    errors.append(
                        f"Circular dependency detected involving node: {node_name}"
                    )

        return len(errors) == 0, errors


class WorkflowStateManager:
    """Utilities for managing workflow state transitions"""

    @staticmethod
    def update_node_completion(
        state: AgenticWorkflowState, node_name: str, output: Any
    ) -> AgenticWorkflowState:
        """Mark a node as completed and store its output"""
        completed_nodes = state.get("completed_nodes", [])
        if node_name not in completed_nodes:
            completed_nodes.append(node_name)
            state["completed_nodes"] = completed_nodes

        # Store node output
        node_outputs = state.get("node_outputs", {})
        node_outputs[node_name] = output
        state["node_outputs"] = node_outputs

        # Clear current task if it matches the completed node
        current_task = state.get("current_task")
        if current_task and current_task.get("agent_role") == node_name:
            state["current_task"] = None

        logger.info(f"Node '{node_name}' marked as completed")
        return state

    @staticmethod
    def update_node_failure(
        state: AgenticWorkflowState, node_name: str, error: str
    ) -> AgenticWorkflowState:
        """Mark a node as failed and store the error"""
        failed_nodes = state.get("failed_nodes", [])
        if node_name not in failed_nodes:
            failed_nodes.append(node_name)
            state["failed_nodes"] = failed_nodes

        # Store failure information
        node_outputs = state.get("node_outputs", {})
        node_outputs[f"{node_name}_error"] = error
        state["node_outputs"] = node_outputs

        # Clear current task if it matches the failed node
        current_task = state.get("current_task")
        if current_task and current_task.get("agent_role") == node_name:
            state["current_task"] = None

        logger.warning(f"Node '{node_name}' marked as failed: {error}")
        return state

    @staticmethod
    def get_next_executable_nodes(state: AgenticWorkflowState) -> List[Dict[str, Any]]:
        """Get list of nodes that can be executed next based on dependencies"""
        planned_nodes = state.get("planned_nodes", [])
        completed_nodes = set(state.get("completed_nodes", []))
        failed_nodes = set(state.get("failed_nodes", []))

        executable_nodes = []

        for node in planned_nodes:
            node_name = node.get("agent_role")

            # Skip if already completed or failed
            if node_name in completed_nodes or node_name in failed_nodes:
                continue

            # Check if all dependencies are satisfied
            dependencies = set(node.get("dependencies", []))
            if dependencies.issubset(completed_nodes):
                executable_nodes.append(node)

        return executable_nodes

    @staticmethod
    def serialize_state_for_persistence(state: AgenticWorkflowState) -> str:
        """Serialize workflow state for persistence"""
        try:
            # Create a copy and convert any non-serializable objects
            serializable_state = {}
            for key, value in state.items():
                try:
                    json.dumps(value)  # Test if serializable
                    serializable_state[key] = value
                except (TypeError, ValueError):
                    # Convert to string representation for non-serializable objects
                    serializable_state[key] = str(value)

            return json.dumps(serializable_state, indent=2)
        except Exception as e:
            logger.error(f"Failed to serialize state: {e}")
            return json.dumps({"error": f"Serialization failed: {e}"})

    @staticmethod
    def deserialize_state_from_persistence(
        serialized_state: str,
    ) -> AgenticWorkflowState:
        """Deserialize workflow state from persistence"""
        try:
            return json.loads(serialized_state)
        except Exception as e:
            logger.error(f"Failed to deserialize state: {e}")
            # Return minimal valid state
            return {
                "workflow_id": "unknown",
                "user_request": "Failed to deserialize",
                "current_phase": "error",
                "planned_nodes": [],
                "completed_nodes": [],
                "failed_nodes": [],
                "node_outputs": {},
            }
