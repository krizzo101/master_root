"""
OAMAT Workflow Orchestrator - Execution

Main workflow execution logic and coordination.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from src.applications.oamat.agents.models import (
    EnhancedWorkflowPlan,
)
from src.applications.oamat.workflows.orchestrator.state import (
    AgenticWorkflowState,
    create_initial_state,
)

# REMOVED: SDLCPhaseManager - using pure intelligence-based workflows

logger = logging.getLogger("WorkflowExecution")


class WorkflowExecutor:
    """Executes agentic workflows using LangGraph orchestration"""

    def __init__(self):  # REMOVED: sdlc_manager parameter - using pure intelligence
        """Initialize WorkflowExecutor for intelligent workflow execution"""
        self.logger = logging.getLogger("OAMAT.WorkflowExecutor")
        # REMOVED: SDLC manager - WorkflowManager creates intelligent workflows naturally

    async def execute_agentic_workflow(
        self,
        user_request: str,
        workflow_plan: EnhancedWorkflowPlan,
        workflow_graph,
        context: dict[str, Any] = None,
        interactive: bool = True,
        initial_state: AgenticWorkflowState = None,
    ) -> dict[str, Any]:
        """
        Execute a complete agentic workflow using LangGraph orchestration.

        This is the main entry point for workflow execution that coordinates
        between planning, execution, and result compilation.
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()

        logger.info(f"🚀 Starting agentic workflow execution: {workflow_id}")
        logger.info(f"📋 User request: {user_request}")
        logger.info(f"🎯 Workflow plan: {len(workflow_plan.nodes)} nodes")

        try:
            # Initialize workflow state if not provided
            if initial_state is None:
                initial_state = create_initial_state(
                    user_request=user_request,
                    context=context,
                    workflow_id=workflow_id,
                    workflow_plan=workflow_plan,  # FIX: Add missing workflow_plan parameter
                )
            else:
                initial_state["metadata"]["workflow_id"] = workflow_id

            # Convert workflow plan to state format
            planned_nodes = []
            for node in workflow_plan.nodes:
                planned_nodes.append(
                    {
                        "id": node.id,
                        "agent_role": node.agent_role,
                        "task_description": node.description,
                        "dependencies": getattr(node, "dependencies", []),
                        "tools": node.tools_required,
                        "critical": getattr(node, "critical", False),
                        "execution_order": getattr(node, "execution_order", 0),
                    }
                )

            initial_state["planned_nodes"] = planned_nodes

            # INTELLIGENCE-BASED: Always use LangGraph orchestration with WorkflowManager intelligence
            logger.info("⚡ Executing intelligent workflow with LangGraph orchestration")
            return await self._execute_standard_workflow(
                workflow_plan,
                workflow_id,
                user_request,
                context,
                workflow_graph,
                initial_state,
            )

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": error_msg,
                "execution_time": execution_time,
                "timestamp": end_time.isoformat(),
            }

    # REMOVED: _execute_sdlc_phases and _execute_phase_agent methods
    # Using pure intelligence-based workflows through WorkflowManager instead of rigid SDLC phases

    async def _execute_standard_workflow(
        self,
        workflow_plan: EnhancedWorkflowPlan,
        workflow_id: str,
        user_request: str,
        context: dict[str, Any] = None,
        workflow_graph=None,
        initial_state: AgenticWorkflowState = None,
    ) -> dict[str, Any]:
        """Execute workflow using standard LangGraph orchestration"""
        start_time = datetime.now()  # FIXED: Moved to very beginning of method

        try:
            if not workflow_graph:
                raise ValueError("Workflow graph is required for standard execution")

            # Compile the workflow graph with memory
            from langgraph.checkpoint.memory import MemorySaver

            memory_saver = MemorySaver()
            compiled_graph = workflow_graph.compile(checkpointer=memory_saver)

            # Use provided initial state
            if initial_state is None:
                initial_state = create_initial_state(
                    user_request,
                    context,
                    workflow_id=workflow_id,
                    workflow_plan=workflow_plan,
                )
                print(
                    f"🔄 DEBUG: Created initial_state with keys: {list(initial_state.keys())}"
                )
                print(
                    f"🔄 DEBUG: workflow_plan in initial_state: {initial_state.get('workflow_plan') is not None}"
                )
                if initial_state.get("workflow_plan"):
                    print(
                        f"🔄 DEBUG: workflow_plan has {len(initial_state['workflow_plan'].nodes)} nodes"
                    )
            else:
                print(
                    f"🔄 DEBUG: Using provided initial_state with keys: {list(initial_state.keys())}"
                )

            # Execute the workflow
            logger.info("🔄 Executing compiled workflow graph...")
            print(
                f"🔄 DEBUG: About to start LangGraph execution with initial_state: {list(initial_state.keys())}"
            )

            config = {"configurable": {"thread_id": workflow_id}}
            final_state = None

            # Stream through the workflow execution
            print("🔄 DEBUG: Starting astream iteration...")
            iteration_count = 0
            async for state in compiled_graph.astream(initial_state, config=config):
                iteration_count += 1
                print(
                    f"🔄 DEBUG: Iteration {iteration_count} - State keys: {list(state.keys())}"
                )
                logger.debug(f"Workflow state update: {list(state.keys())}")
                final_state = state

            print(
                f"🔄 DEBUG: LangGraph execution completed after {iteration_count} iterations"
            )
            print(
                f"🔄 DEBUG: Final state keys: {list(final_state.keys()) if final_state else 'None'}"
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            if final_state:
                return {
                    "success": final_state.get("success", True),
                    "workflow_id": workflow_id,
                    "agent_outputs": final_state.get("agent_outputs", {}),
                    "final_output": final_state.get("final_output"),
                    "completed_nodes": final_state.get("completed_nodes", []),
                    "failed_nodes": final_state.get("failed_nodes", []),
                    "errors": final_state.get("errors", []),
                    "project_name": final_state.get("project_name"),
                    "project_path": final_state.get("project_path"),
                    "execution_time": execution_time,
                    "timestamp": end_time.isoformat(),
                }
            else:
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": "No final state received from workflow execution",
                    "execution_time": execution_time,
                    "timestamp": end_time.isoformat(),
                }

        except Exception as e:
            import traceback

            # Enhanced error logging for debugging parallel execution issues
            error_type = type(e).__name__
            error_str = str(e) if str(e) else "No error message provided"
            error_repr = repr(e)
            full_traceback = traceback.format_exc()

            error_msg = f"Standard workflow execution failed: {error_type}: {error_str}"

            # Comprehensive error logging
            logger.error("🚨 WORKFLOW EXECUTION FAILURE:")
            logger.error(f"   Error Type: {error_type}")
            logger.error(f"   Error Message: {error_str}")
            logger.error(f"   Error Repr: {error_repr}")
            logger.error(f"   Full Traceback:\n{full_traceback}")

            # Check for specific LangGraph/parallel execution errors
            if "Send" in str(e) or "parallel" in str(e).lower():
                logger.error(
                    "🔧 PARALLEL EXECUTION ERROR detected - likely issue with Send API dispatch"
                )

            if not str(e):  # Empty error message
                logger.error(
                    "🔧 EMPTY ERROR MESSAGE - this suggests an internal LangGraph issue"
                )
                error_msg = f"Standard workflow execution failed: {error_type} (no error message - check LangGraph version and Send API compatibility)"

            end_time = datetime.now()
            execution_time = (
                end_time - start_time
            ).total_seconds()  # FIXED: Now start_time is in scope

            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": error_msg,
                "execution_time": execution_time,
                "timestamp": end_time.isoformat(),
                "debug_info": {
                    "error_type": error_type,
                    "error_repr": error_repr,
                    "traceback": full_traceback,
                },
            }

    def _create_unified_project_name(self, user_request: str) -> str:
        """Create a unified project name from user request"""
        # Simple implementation - clean and truncate the request
        import re

        # Extract key words and clean
        clean_request = re.sub(r"[^\w\s]", "", user_request.lower())
        words = clean_request.split()[:3]  # Take first 3 words

        project_name = "_".join(words) if words else "oamat_project"

        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        return f"{project_name}_{timestamp}"
