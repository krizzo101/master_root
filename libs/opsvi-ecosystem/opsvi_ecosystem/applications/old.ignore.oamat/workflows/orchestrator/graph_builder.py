"""
OAMAT Workflow Orchestrator - Graph Builder

Creates dynamic LangGraph workflows from workflow plans.
"""

import logging
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from src.applications.oamat.agents.models import (
    EnhancedWorkflowNode,
    EnhancedWorkflowPlan,
)
from src.applications.oamat.workflows.orchestrator.state import AgenticWorkflowState

logger = logging.getLogger("OAMAT.WorkflowGraphBuilder")


class WorkflowGraphBuilder:
    """Builds dynamic LangGraph workflows from workflow plans"""

    def __init__(self, supervisor_node: Callable, completion_node: Callable):
        self.supervisor_node = supervisor_node
        self.completion_node = completion_node
        self.logger = logger

    def create_dynamic_workflow_graph(
        self, workflow_plan: EnhancedWorkflowPlan, agent_creators: dict[str, Callable]
    ) -> StateGraph:
        """Create a dynamic workflow graph based on the enhanced workflow plan"""
        graph = StateGraph(AgenticWorkflowState)

        # Add fixed supervisor and completion nodes
        graph.add_node("supervisor", self.supervisor_node)
        graph.add_node("completion", self.completion_node)

        # Add parallel execution handler
        graph.add_node("parallel_execution", self._create_parallel_execution_node())

        # Add workflow-specific agent nodes
        for node in workflow_plan.nodes:
            if node.id in agent_creators:
                graph.add_node(node.id, agent_creators[node.id])
            else:
                logger.warning(f"No agent creator found for node: {node.id}")

        # Add edges
        graph.add_edge(START, "supervisor")
        self._add_workflow_edges(graph, workflow_plan)
        graph.add_edge("completion", END)

        # Log creation
        logger.info(
            f"Created dynamic workflow graph with {len(workflow_plan.nodes)} nodes"
        )
        return graph

    def _create_parallel_execution_node(self):
        """Create a node that handles parallel execution of multiple agents"""

        def parallel_execution_handler(state):
            """Handle parallel execution of agents using Send API"""
            parallel_commands = state.get("parallel_commands", [])

            if not parallel_commands:
                # No parallel commands, route back to supervisor
                return {"next_node": "supervisor"}

            # Create Send commands from stored parallel commands
            from langgraph.constants import Send

            send_commands = []

            for cmd_info in parallel_commands:
                node_id = cmd_info["node_id"]
                agent_state = cmd_info["agent_state"]
                send_commands.append(Send(node_id, agent_state))

            print(f"🚀 PARALLEL: Executing {len(send_commands)} agents simultaneously")

            # Return Send commands for parallel execution
            return send_commands

        return parallel_execution_handler

    def _add_workflow_edges(
        self, graph: StateGraph, workflow_plan: EnhancedWorkflowPlan
    ):
        """Add edges between nodes based on the workflow plan"""

        # Define the routing logic from the supervisor
        graph.add_conditional_edges(
            "supervisor",
            lambda state: state.get("next_node"),  # The supervisor's decision
            {node.id: node.id for node in workflow_plan.nodes}
            | {"completion": "completion", "parallel_execution": "parallel_execution"},
        )

        # Add edges from each agent node back to the supervisor for the next routing decision
        for node in workflow_plan.nodes:
            graph.add_edge(node.id, "supervisor")

        # Ensure completion goes to END
        graph.add_edge("completion", END)

    def _has_predecessors(
        self, node: EnhancedWorkflowNode, workflow_plan: EnhancedWorkflowPlan
    ) -> bool:
        """Check if a node has predecessors in the workflow plan"""
        for other_node in workflow_plan.nodes:
            if node.id in other_node.next_nodes:
                return True
        return False
