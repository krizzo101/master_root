"""
Workflow Converter for ASEA-LangGraph Integration

Converts existing ASEA JSON workflow definitions into LangGraph StateGraph workflows,
preserving all functionality while adding LangGraph capabilities.
"""

import json
from typing import Dict, Any, List, Optional, Callable

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ASEAState, create_initial_state
from ..plugins.plugin_manager import PluginManager


class WorkflowConverter:
    """
    Converts ASEA JSON workflows to LangGraph StateGraph workflows.

    This converter maintains full backwards compatibility with existing
    ASEA workflow definitions while adding LangGraph orchestration capabilities.
    """

    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        """
        Initialize the workflow converter.

        Args:
            plugin_manager: ASEA plugin manager instance for loading plugins
        """
        if plugin_manager:
            self.plugin_manager = plugin_manager
        else:
            # Create plugin manager with default plugin directory
            import os

            plugin_dir = os.path.join(
                os.path.dirname(__file__), "..", "plugins", "available"
            )
            self.plugin_manager = PluginManager(plugin_dir)
        self.plugin_cache = {}

    def convert_workflow_file(self, workflow_file: str) -> StateGraph:
        """
        Convert a JSON workflow file to a LangGraph StateGraph.

        Args:
            workflow_file: Path to the ASEA JSON workflow file

        Returns:
            LangGraph StateGraph ready for execution
        """
        with open(workflow_file, "r") as f:
            workflow_definition = json.load(f)

        return self.convert_workflow_definition(workflow_definition)

    def convert_workflow_definition(self, workflow_def: Dict[str, Any]) -> StateGraph:
        """
        Convert a workflow definition dictionary to a LangGraph StateGraph.

        Args:
            workflow_def: ASEA workflow definition dictionary

        Returns:
            LangGraph StateGraph ready for execution
        """
        # Create the StateGraph with ASEA state schema
        workflow = StateGraph(ASEAState)

        # Extract workflow metadata
        workflow_name = workflow_def.get("name", "unnamed_workflow")
        steps = workflow_def.get("steps", [])

        # Convert each step to a LangGraph node
        for step in steps:
            node_name = step["name"]
            plugin_name = step["plugin"]

            # Create plugin node
            plugin_node = self._create_plugin_node_from_step(step)

            # Add node to workflow
            workflow.add_node(node_name, plugin_node)

        # Add edges based on step dependencies
        self._add_workflow_edges(workflow, steps)

        # Set entry point (first step)
        if steps:
            workflow.set_entry_point(steps[0]["name"])

        # Set finish point (last step leads to END)
        if steps:
            last_step = steps[-1]["name"]
            workflow.add_edge(last_step, END)

        return workflow

    def _create_plugin_node_from_step(self, step: Dict[str, Any]) -> Callable:
        """
        Create a plugin node from a workflow step definition.

        Args:
            step: Step definition from ASEA workflow JSON

        Returns:
            Plugin node function for LangGraph
        """
        plugin_name = step["plugin"]

        # Get or create plugin instance
        if plugin_name not in self.plugin_cache:
            plugin_class = self.plugin_manager.get_plugin(plugin_name)
            if not plugin_class:
                raise ValueError(f"Plugin '{plugin_name}' not found")

            self.plugin_cache[plugin_name] = plugin_class()
            self.plugin_cache[plugin_name].initialize()

        plugin_instance = self.plugin_cache[plugin_name]

        # Extract input and output mappings
        input_mapping = step.get("inputs", {})
        output_mapping = step.get("outputs", {})
        plugin_config = step.get("config", {})

        # Create plugin node adapter
        from .plugin_adapter import ASEAPluginNode

        plugin_node = ASEAPluginNode(
            plugin=plugin_instance,
            input_mapping=input_mapping,
            output_mapping=output_mapping,
            plugin_config=plugin_config,
        )

        return plugin_node

    def _add_workflow_edges(self, workflow: StateGraph, steps: List[Dict[str, Any]]):
        """
        Add edges between workflow steps based on dependencies.

        Args:
            workflow: LangGraph StateGraph to add edges to
            steps: List of step definitions from ASEA workflow
        """
        # For now, implement sequential execution (step N -> step N+1)
        # TODO: Add support for conditional routing and parallel execution

        for i in range(len(steps) - 1):
            current_step = steps[i]["name"]
            next_step = steps[i + 1]["name"]
            workflow.add_edge(current_step, next_step)

    def create_workflow_executor(self, workflow_def: Dict[str, Any]) -> Callable:
        """
        Create a complete workflow executor from ASEA workflow definition.

        Args:
            workflow_def: ASEA workflow definition dictionary

        Returns:
            Executable workflow function
        """
        # Convert to LangGraph
        graph = self.convert_workflow_definition(workflow_def)

        # Add checkpointing (memory-based for now)
        checkpointer = MemorySaver()

        # Compile the workflow
        compiled_workflow = graph.compile(checkpointer=checkpointer)

        def execute_workflow(
            user_input: Dict[str, Any], run_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Execute the workflow with user input.

            Args:
                user_input: Input data for the workflow
                run_id: Optional run ID for checkpointing

            Returns:
                Final workflow state
            """
            import uuid

            # Generate run ID if not provided
            if not run_id:
                run_id = str(uuid.uuid4())

            # Create initial state
            initial_state = create_initial_state(
                workflow_name=workflow_def.get("name", "unnamed"),
                run_id=run_id,
                user_input=user_input,
                workflow_config=workflow_def.get("config", {}),
            )

            # Execute workflow
            config = {"configurable": {"thread_id": run_id}}
            final_state = compiled_workflow.invoke(initial_state, config=config)

            return final_state

        return execute_workflow


def convert_cognitive_enhancement_workflow() -> Callable:
    """
    Convert the existing cognitive enhancement workflow to LangGraph.

    Returns:
        Executable cognitive enhancement workflow function
    """
    converter = WorkflowConverter()

    # Load the existing cognitive enhancement workflow
    workflow_file = "/home/opsvi/asea/asea_orchestrator/workflows/cognitive_enhancement/enhanced_response_workflow.json"

    try:
        with open(workflow_file, "r") as f:
            workflow_def = json.load(f)

        return converter.create_workflow_executor(workflow_def)

    except FileNotFoundError:
        # Fallback: create a basic cognitive enhancement workflow
        basic_workflow = {
            "name": "cognitive_enhancement_basic",
            "description": "Basic cognitive enhancement workflow",
            "steps": [
                {
                    "name": "cognitive_reminder",
                    "plugin": "cognitive_reminder",
                    "inputs": {"context": "{{ workflow.input.user_prompt }}"},
                    "outputs": {"reminders": "reminders"},
                },
                {
                    "name": "cognitive_pre_analysis",
                    "plugin": "cognitive_pre_analysis",
                    "inputs": {
                        "prompt": "{{ workflow.input.user_prompt }}",
                        "context": "{{ workflow.state.reminders }}",
                    },
                    "outputs": {"enhanced_understanding": "enhanced_understanding"},
                },
                {
                    "name": "ai_reasoning",
                    "plugin": "ai_reasoning",
                    "inputs": {"prompt": "{{ workflow.state.enhanced_understanding }}"},
                    "outputs": {"response": "ai_response"},
                },
            ],
        }

        return converter.create_workflow_executor(basic_workflow)
