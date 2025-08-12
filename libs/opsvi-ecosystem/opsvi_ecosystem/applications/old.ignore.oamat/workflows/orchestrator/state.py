"""
OAMAT Workflow Orchestrator State Management
"""

from typing import Annotated, Any

from typing_extensions import TypedDict


def add_unique_nodes(left: list[str], right: list[str]) -> list[str]:
    """
    Custom reducer for completed_nodes that maintains uniqueness.
    Prevents massive duplication that was occurring with operator.add.

    Args:
        left: Existing list of completed nodes
        right: New nodes to add

    Returns:
        Combined list with no duplicates, maintaining order
    """
    if not left:
        left = []
    if not right:
        right = []

    existing = set(left)
    unique_new = [item for item in right if item not in existing]
    return left + unique_new


class AgenticWorkflowState(TypedDict, total=False):
    """State model for agentic workflows"""

    user_request: str
    context: dict[str, Any]
    current_node: str | None
    # Use custom unique reducer to prevent duplication bug
    completed_nodes: Annotated[list[str], add_unique_nodes]
    results: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any]

    # OAMAT project context
    project_name: str | None
    project_path: str | None

    # Additional fields that might be used by the workflow
    planned_nodes: list[dict[str, Any]]
    workflow_plan: Any | None  # EnhancedWorkflowPlan for supervisor routing
    sdlc_context: dict[str, Any]
    node_outputs: dict[str, Any]
    agent_outputs: dict[str, Any]  # Agent execution outputs
    current_task: dict[str, Any] | None
    failed_nodes: list[str]

    # Workflow completion status
    success: bool | None
    error: str | None
    total_files_created: int | None


def create_initial_state(
    user_request: str, context: dict[str, Any] = None, **kwargs
) -> AgenticWorkflowState:
    """Create the initial state for a workflow execution"""

    # Debug the workflow_plan processing
    workflow_plan_param = kwargs.get("workflow_plan")
    print(
        f"🔧 DEBUG: create_initial_state called with workflow_plan type: {type(workflow_plan_param)}"
    )
    print(
        f"🔧 DEBUG: workflow_plan_param is not None: {workflow_plan_param is not None}"
    )

    workflow_plan_serialized = None
    if workflow_plan_param:
        try:
            workflow_plan_serialized = workflow_plan_param.model_dump()
            print(
                f"🔧 DEBUG: Successfully serialized workflow_plan with {len(workflow_plan_serialized.get('nodes', []))} nodes"
            )
        except Exception as e:
            print(f"🔧 DEBUG: Failed to serialize workflow_plan: {e}")
            workflow_plan_serialized = None
    else:
        print("🔧 DEBUG: No workflow_plan provided to create_initial_state")

    planned_nodes = []
    if context:
        planned_nodes = context.get("planned_nodes", [])

    metadata = {
        "workflow_id": kwargs.get("workflow_id", "default"),
        "planned_nodes": planned_nodes,
    }
    metadata.update(kwargs.get("metadata", {}))

    # CRITICAL FIX: Extract project context from the enhanced context
    project_name = None
    project_path = None

    if context:
        # Try to get project info from context first
        project_name = context.get("project_name")
        project_path = context.get("project_path")
        print(
            f"🔧 DEBUG: Extracted from context - project_name: {project_name}, project_path: {project_path}"
        )

    # Fallback to global context if not in passed context
    if not project_name or not project_path:
        from src.applications.oamat.utils.project_context import ProjectContextManager

        global_project_name = ProjectContextManager.get_project_name()
        global_project_path = ProjectContextManager.get_project_path()

        if global_project_name and not project_name:
            project_name = global_project_name
        if global_project_path and not project_path:
            project_path = global_project_path

        print(
            f"🔧 DEBUG: After global fallback - project_name: {project_name}, project_path: {project_path}"
        )

    state = AgenticWorkflowState(
        user_request=user_request,
        context=context or {},
        current_node="start",
        completed_nodes=[],
        results={},
        errors=[],
        metadata=metadata,
        planned_nodes=planned_nodes,
        workflow_plan=workflow_plan_serialized,  # Use the serialized version
        sdlc_context={},
        node_outputs={},
        agent_outputs={},  # Initialize agent outputs
        current_task=None,
        failed_nodes=[],
        # CRITICAL FIX: Set project context in initial state
        project_name=project_name,
        project_path=project_path,
    )

    print(
        f"🔧 DEBUG: Created state with workflow_plan: {state.get('workflow_plan') is not None}"
    )
    print(f"🔧 DEBUG: Created state with project_name: {state.get('project_name')}")
    print(f"🔧 DEBUG: Created state with project_path: {state.get('project_path')}")

    return state
