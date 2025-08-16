"""
ASEA State Schema for LangGraph Integration

Defines the state structure that flows through LangGraph workflows,
preserving compatibility with existing ASEA plugin interfaces.
"""

from typing import TypedDict, Dict, Any, List, Optional
from datetime import datetime


class ASEAState(TypedDict):
    """
    LangGraph state schema for ASEA workflows.

    This state structure preserves all existing ASEA functionality while
    adding LangGraph-specific capabilities like checkpointing and streaming.
    """

    # Core workflow identification
    workflow_name: str
    run_id: str
    current_step: str

    # Original ASEA workflow state (preserves existing functionality)
    workflow_state: Dict[str, Any]  # This contains the original ASEA state

    # Plugin execution tracking
    plugin_outputs: Dict[str, Any]
    execution_context: Dict[str, Any]

    # ASEA-specific cognitive enhancement state
    cognitive_metadata: Dict[str, Any]
    reminders: List[str]
    enhanced_understanding: Optional[str]

    # Input/Output mapping for template compatibility
    input_mappings: Dict[str, str]
    output_mappings: Dict[str, str]

    # Error handling and fallbacks
    errors: List[str]
    fallback_data: Dict[str, Any]

    # Performance and monitoring
    step_timings: Dict[str, float]
    plugin_metadata: Dict[str, Dict[str, Any]]

    # LangGraph-specific enhancements
    checkpointed_at: Optional[str]
    human_feedback: Optional[Dict[str, Any]]
    streaming_enabled: bool


def create_initial_state(
    workflow_name: str,
    run_id: str,
    user_input: Dict[str, Any],
    workflow_config: Dict[str, Any],
) -> ASEAState:
    """
    Create initial ASEA state for a LangGraph workflow.

    Args:
        workflow_name: Name of the workflow being executed
        run_id: Unique identifier for this workflow run
        user_input: Input data from the user
        workflow_config: Configuration from the original ASEA workflow JSON

    Returns:
        Initialized ASEAState ready for LangGraph execution
    """
    return ASEAState(
        workflow_name=workflow_name,
        run_id=run_id,
        current_step="initialization",
        workflow_state=user_input.copy(),
        plugin_outputs={},
        execution_context={
            "start_time": datetime.now().isoformat(),
            "config": workflow_config,
        },
        cognitive_metadata={},
        reminders=[],
        enhanced_understanding=None,
        input_mappings={},
        output_mappings={},
        errors=[],
        fallback_data={},
        step_timings={},
        plugin_metadata={},
        checkpointed_at=None,
        human_feedback=None,
        streaming_enabled=False,
    )


def update_state_for_plugin(
    state: ASEAState,
    plugin_name: str,
    plugin_output: Any,
    execution_time: float,
    metadata: Optional[Dict[str, Any]] = None,
) -> ASEAState:
    """
    Update state after plugin execution, preserving ASEA patterns.

    Args:
        state: Current workflow state
        plugin_name: Name of the plugin that was executed
        plugin_output: Output from the plugin
        execution_time: Time taken to execute the plugin
        metadata: Additional metadata about the plugin execution

    Returns:
        Updated state with plugin results integrated
    """
    # Create a copy to avoid mutation
    new_state = state.copy()

    # Update plugin outputs
    new_state["plugin_outputs"][plugin_name] = plugin_output

    # Update timing information
    new_state["step_timings"][plugin_name] = execution_time

    # Update metadata
    if metadata:
        new_state["plugin_metadata"][plugin_name] = metadata

    # Update current step
    new_state["current_step"] = plugin_name

    # Update checkpointing timestamp
    new_state["checkpointed_at"] = datetime.now().isoformat()

    return new_state
