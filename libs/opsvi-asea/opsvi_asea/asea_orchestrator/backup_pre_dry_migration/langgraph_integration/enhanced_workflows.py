"""
Enhanced Workflow Capabilities for ASEA-LangGraph Integration

Implements Phase 2 enhancements including conditional routing, streaming,
human-in-the-loop, and advanced state management.
"""

import time
from typing import Dict, Any, Optional, Callable, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END

from .state import ASEAState
from .plugin_adapter import ASEAPluginNode, create_plugin_node


class ConditionalRouter:
    """
    Implements conditional routing based on plugin outputs and state conditions.

    Allows workflows to dynamically choose next steps based on:
    - Plugin execution results
    - State values and conditions
    - Error conditions and recovery paths
    - User feedback and approvals
    """

    def __init__(self):
        self.conditions = {}
        self.routes = {}

    def add_condition(
        self,
        name: str,
        condition_func: Callable[[ASEAState], bool],
        description: str = "",
    ):
        """
        Add a routing condition.

        Args:
            name: Condition identifier
            condition_func: Function that evaluates state and returns boolean
            description: Human-readable description of the condition
        """
        self.conditions[name] = {"func": condition_func, "description": description}

    def add_route(
        self, from_node: str, condition_name: str, true_path: str, false_path: str = END
    ):
        """
        Add a conditional route.

        Args:
            from_node: Source node name
            condition_name: Condition to evaluate
            true_path: Node to route to if condition is true
            false_path: Node to route to if condition is false
        """
        self.routes[from_node] = {
            "condition": condition_name,
            "true_path": true_path,
            "false_path": false_path,
        }

    def create_routing_function(self, from_node: str) -> Callable:
        """
        Create a routing function for a specific node.

        Args:
            from_node: Node to create routing for

        Returns:
            Routing function for LangGraph
        """
        if from_node not in self.routes:
            return lambda state: END

        route_config = self.routes[from_node]
        condition_name = route_config["condition"]

        if condition_name not in self.conditions:
            return lambda state: route_config["false_path"]

        def router(state: ASEAState) -> str:
            try:
                condition_func = self.conditions[condition_name]["func"]
                result = condition_func(state)

                if result:
                    return route_config["true_path"]
                else:
                    return route_config["false_path"]

            except Exception as e:
                # Log error and take safe path
                print(f"Routing error for {from_node}: {e}")
                return route_config["false_path"]

        return router


class StreamingManager:
    """
    Manages streaming capabilities for real-time workflow feedback.

    Provides:
    - Real-time step progress updates
    - Streaming plugin outputs
    - Performance monitoring
    - User notifications
    """

    def __init__(self, enable_streaming: bool = True):
        self.enable_streaming = enable_streaming
        self.subscribers = []
        self.step_history = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to streaming updates."""
        self.subscribers.append(callback)

    def emit_update(self, update_type: str, data: Dict[str, Any]):
        """Emit a streaming update to all subscribers."""
        if not self.enable_streaming:
            return

        update = {
            "timestamp": datetime.now().isoformat(),
            "type": update_type,
            "data": data,
        }

        self.step_history.append(update)

        for callback in self.subscribers:
            try:
                callback(update)
            except Exception as e:
                print(f"Streaming callback error: {e}")

    def emit_step_start(self, step_name: str, state: ASEAState):
        """Emit step start notification."""
        self.emit_update(
            "step_start",
            {
                "step_name": step_name,
                "workflow_name": state.get("workflow_name"),
                "run_id": state.get("run_id"),
                "current_state_keys": list(state.get("workflow_state", {}).keys()),
            },
        )

    def emit_step_complete(self, step_name: str, output: Any, execution_time: float):
        """Emit step completion notification."""
        self.emit_update(
            "step_complete",
            {
                "step_name": step_name,
                "execution_time": execution_time,
                "output_summary": self._summarize_output(output),
                "success": True,
            },
        )

    def emit_step_error(self, step_name: str, error: str, execution_time: float):
        """Emit step error notification."""
        self.emit_update(
            "step_error",
            {
                "step_name": step_name,
                "error": error,
                "execution_time": execution_time,
                "success": False,
            },
        )

    def emit_workflow_complete(self, final_state: ASEAState, total_time: float):
        """Emit workflow completion notification."""
        self.emit_update(
            "workflow_complete",
            {
                "workflow_name": final_state.get("workflow_name"),
                "run_id": final_state.get("run_id"),
                "total_execution_time": total_time,
                "steps_completed": len(final_state.get("plugin_outputs", {})),
                "final_output_keys": list(final_state.get("workflow_state", {}).keys()),
                "errors": final_state.get("errors", []),
            },
        )

    def _summarize_output(self, output: Any) -> Dict[str, Any]:
        """Create a summary of plugin output for streaming."""
        if isinstance(output, dict):
            return {"type": "dict", "keys": list(output.keys()), "size": len(output)}
        elif isinstance(output, str):
            return {
                "type": "string",
                "length": len(output),
                "preview": output[:100] + "..." if len(output) > 100 else output,
            }
        elif isinstance(output, list):
            return {
                "type": "list",
                "length": len(output),
                "item_types": [type(item).__name__ for item in output[:5]],
            }
        else:
            return {"type": type(output).__name__, "value": str(output)[:100]}


class HumanInTheLoopManager:
    """
    Manages human-in-the-loop capabilities for workflow intervention.

    Provides:
    - Approval checkpoints
    - Manual intervention points
    - Quality review steps
    - Decision override capabilities
    """

    def __init__(self):
        self.approval_queue = {}
        self.intervention_points = {}
        self.approval_callbacks = {}

    def add_approval_point(
        self,
        step_name: str,
        approval_type: Literal["required", "optional", "quality_check"],
        prompt: str,
        timeout_seconds: Optional[int] = None,
    ):
        """
        Add a human approval point to the workflow.

        Args:
            step_name: Step that requires approval
            approval_type: Type of approval needed
            prompt: Message to show to human reviewer
            timeout_seconds: Optional timeout for approval
        """
        self.intervention_points[step_name] = {
            "type": approval_type,
            "prompt": prompt,
            "timeout": timeout_seconds,
            "created_at": datetime.now().isoformat(),
        }

    def request_approval(
        self, step_name: str, state: ASEAState, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Request human approval for a workflow step.

        Args:
            step_name: Step requesting approval
            state: Current workflow state
            context: Additional context for approval decision

        Returns:
            Approval result with decision and feedback
        """
        if step_name not in self.intervention_points:
            return {"approved": True, "feedback": "No approval required"}

        approval_config = self.intervention_points[step_name]
        approval_id = f"{state.get('run_id')}_{step_name}_{int(time.time())}"

        approval_request = {
            "id": approval_id,
            "step_name": step_name,
            "workflow_name": state.get("workflow_name"),
            "run_id": state.get("run_id"),
            "type": approval_config["type"],
            "prompt": approval_config["prompt"],
            "context": context,
            "state_summary": self._create_state_summary(state),
            "requested_at": datetime.now().isoformat(),
            "timeout": approval_config.get("timeout"),
            "status": "pending",
        }

        self.approval_queue[approval_id] = approval_request

        # For demo purposes, simulate approval decision
        # In production, this would integrate with UI/notification system
        return self._simulate_approval_decision(approval_request)

    def _simulate_approval_decision(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate human approval decision for demo purposes.

        In production, this would be replaced with actual human interface.
        """
        approval_type = request["type"]

        if approval_type == "required":
            # Simulate required approval - approve if no errors
            has_errors = len(request["context"].get("errors", [])) > 0
            return {
                "approved": not has_errors,
                "feedback": "Automated approval: No errors detected"
                if not has_errors
                else "Rejected: Errors detected",
                "reviewer": "system_simulation",
                "approved_at": datetime.now().isoformat(),
            }

        elif approval_type == "quality_check":
            # Simulate quality check - approve if output looks reasonable
            output_quality = self._assess_output_quality(request["context"])
            return {
                "approved": output_quality["score"] >= 0.7,
                "feedback": f"Quality score: {output_quality['score']:.2f} - {output_quality['assessment']}",
                "quality_metrics": output_quality,
                "reviewer": "quality_system",
                "approved_at": datetime.now().isoformat(),
            }

        else:  # optional
            return {
                "approved": True,
                "feedback": "Optional approval - automatically approved",
                "reviewer": "system_auto",
                "approved_at": datetime.now().isoformat(),
            }

    def _create_state_summary(self, state: ASEAState) -> Dict[str, Any]:
        """Create a human-readable summary of workflow state."""
        return {
            "workflow_progress": f"{len(state.get('plugin_outputs', {}))} steps completed",
            "current_step": state.get("current_step", "unknown"),
            "execution_time": sum(state.get("step_timings", {}).values()),
            "error_count": len(state.get("errors", [])),
            "state_size": len(state.get("workflow_state", {})),
        }

    def _assess_output_quality(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of plugin output for approval decisions.

        This is a simplified quality assessment. In production,
        this could use more sophisticated analysis.
        """
        output = context.get("output", {})
        errors = context.get("errors", [])

        # Simple quality scoring
        score = 1.0
        assessment_notes = []

        # Penalize errors
        if errors:
            score -= 0.3 * len(errors)
            assessment_notes.append(f"{len(errors)} errors detected")

        # Check output completeness
        if isinstance(output, dict):
            if not output or all(v is None for v in output.values()):
                score -= 0.4
                assessment_notes.append("Output appears empty or incomplete")
            else:
                assessment_notes.append("Output structure looks good")

        # Check for error indicators in output
        if isinstance(output, dict) and "error" in output:
            score -= 0.5
            assessment_notes.append("Error found in output")

        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]

        return {
            "score": score,
            "assessment": "; ".join(assessment_notes)
            if assessment_notes
            else "No issues detected",
            "criteria_checked": [
                "error_count",
                "output_completeness",
                "error_indicators",
            ],
        }


class EnhancedWorkflowBuilder:
    """
    Builder for creating enhanced LangGraph workflows with Phase 2 capabilities.

    Combines conditional routing, streaming, human-in-the-loop, and advanced
    state management into a unified workflow creation interface.
    """

    def __init__(self, enable_streaming: bool = True, enable_approvals: bool = False):
        self.router = ConditionalRouter()
        self.streaming = StreamingManager(enable_streaming)
        self.hitl = HumanInTheLoopManager()
        self.enable_approvals = enable_approvals

        # Workflow components
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []
        self.entry_point = None

    def add_plugin_node(
        self,
        name: str,
        plugin_class: type,
        input_mapping: Dict[str, str],
        output_mapping: Dict[str, str],
        plugin_config: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
        approval_type: Literal["required", "optional", "quality_check"] = "optional",
    ) -> "EnhancedWorkflowBuilder":
        """
        Add a plugin node with enhanced capabilities.

        Args:
            name: Node name
            plugin_class: ASEA plugin class
            input_mapping: Input parameter mapping
            output_mapping: Output state mapping
            plugin_config: Plugin configuration
            requires_approval: Whether this step requires human approval
            approval_type: Type of approval if required

        Returns:
            Self for method chaining
        """
        # Create base plugin node
        base_plugin_node = create_plugin_node(
            plugin_class=plugin_class,
            input_mapping=input_mapping,
            output_mapping=output_mapping,
            plugin_config=plugin_config,
        )

        # Wrap with enhanced capabilities
        enhanced_node = self._create_enhanced_node(
            name=name,
            base_node=base_plugin_node,
            requires_approval=requires_approval,
            approval_type=approval_type,
        )

        self.nodes[name] = enhanced_node

        # Add approval point if needed
        if requires_approval:
            self.hitl.add_approval_point(
                step_name=name,
                approval_type=approval_type,
                prompt=f"Review and approve results from {name} step",
            )

        return self

    def add_conditional_edge(
        self,
        from_node: str,
        condition_func: Callable[[ASEAState], bool],
        true_path: str,
        false_path: str = END,
        condition_name: Optional[str] = None,
    ) -> "EnhancedWorkflowBuilder":
        """
        Add a conditional edge between nodes.

        Args:
            from_node: Source node
            condition_func: Condition evaluation function
            true_path: Path if condition is true
            false_path: Path if condition is false
            condition_name: Optional condition identifier

        Returns:
            Self for method chaining
        """
        if not condition_name:
            condition_name = f"{from_node}_condition_{len(self.router.conditions)}"

        self.router.add_condition(condition_name, condition_func)
        self.router.add_route(from_node, condition_name, true_path, false_path)

        self.conditional_edges.append(
            {
                "from": from_node,
                "condition": condition_name,
                "true_path": true_path,
                "false_path": false_path,
            }
        )

        return self

    def add_edge(self, from_node: str, to_node: str) -> "EnhancedWorkflowBuilder":
        """Add a simple edge between nodes."""
        self.edges.append((from_node, to_node))
        return self

    def set_entry_point(self, node_name: str) -> "EnhancedWorkflowBuilder":
        """Set the workflow entry point."""
        self.entry_point = node_name
        return self

    def build(self) -> StateGraph:
        """
        Build the enhanced LangGraph workflow.

        Returns:
            Compiled LangGraph workflow with all enhancements
        """
        # Create the StateGraph
        workflow = StateGraph(ASEAState)

        # Add all nodes
        for name, node_func in self.nodes.items():
            workflow.add_node(name, node_func)

        # Add simple edges
        for from_node, to_node in self.edges:
            workflow.add_edge(from_node, to_node)

        # Add conditional edges
        for edge_config in self.conditional_edges:
            router_func = self.router.create_routing_function(edge_config["from"])
            workflow.add_conditional_edges(
                edge_config["from"],
                router_func,
                {
                    edge_config["true_path"]: edge_config["true_path"],
                    edge_config["false_path"]: edge_config["false_path"],
                },
            )

        # Set entry point
        if self.entry_point:
            workflow.set_entry_point(self.entry_point)

        return workflow

    def _create_enhanced_node(
        self,
        name: str,
        base_node: ASEAPluginNode,
        requires_approval: bool,
        approval_type: str,
    ) -> Callable:
        """
        Create an enhanced node wrapper with streaming and approval capabilities.

        Args:
            name: Node name
            base_node: Base ASEA plugin node
            requires_approval: Whether approval is required
            approval_type: Type of approval

        Returns:
            Enhanced node function
        """

        def enhanced_node_func(state: ASEAState) -> ASEAState:
            # Emit step start
            self.streaming.emit_step_start(name, state)

            start_time = time.time()

            try:
                # Execute base plugin
                result_state = base_node(state)
                execution_time = time.time() - start_time

                # Check for errors
                if result_state.get("errors"):
                    self.streaming.emit_step_error(
                        name, "; ".join(result_state["errors"]), execution_time
                    )
                else:
                    # Get plugin output for approval context
                    plugin_output = result_state.get("plugin_outputs", {}).get(
                        name.lower().replace("_", "")
                    )

                    # Request approval if required
                    if requires_approval and self.enable_approvals:
                        approval_result = self.hitl.request_approval(
                            step_name=name,
                            state=result_state,
                            context={
                                "output": plugin_output,
                                "errors": result_state.get("errors", []),
                                "execution_time": execution_time,
                            },
                        )

                        # Add approval result to state (ensure state is mutable)
                        new_state = result_state.copy()
                        if "human_feedback" not in new_state:
                            new_state["human_feedback"] = {}
                        new_state["human_feedback"][name] = approval_result
                        result_state = new_state

                        # Handle rejection
                        if not approval_result.get("approved", True):
                            result_state["errors"].append(
                                f"Step {name} rejected by human reviewer: {approval_result.get('feedback', 'No reason provided')}"
                            )

                    self.streaming.emit_step_complete(
                        name, plugin_output, execution_time
                    )

                return result_state

            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Enhanced node {name} failed: {str(e)}"

                self.streaming.emit_step_error(name, error_msg, execution_time)

                # Create error state
                error_state = state.copy()
                error_state["errors"].append(error_msg)
                error_state["step_timings"][name] = execution_time

                return error_state

        return enhanced_node_func
