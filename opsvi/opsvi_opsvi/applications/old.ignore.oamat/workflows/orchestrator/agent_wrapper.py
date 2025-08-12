"""
OAMAT Workflow Orchestrator - Agent Wrapper

Agent creation and execution wrapper for dynamic workflow orchestration.
"""

import logging
import traceback
from collections.abc import Callable

from src.applications.oamat.agents.agent_factory import AgentFactory
from src.applications.oamat.agents.registry import AGENT_REGISTRY
from src.applications.oamat.utils.rule_loader import (
    get_rules_for_agent,
    get_security_rules,
)
from src.applications.oamat.workflows.orchestrator.state import AgenticWorkflowState

logger = logging.getLogger("AgentWrapper")


class AgentWrapperFactory:
    """Factory for creating agent wrappers"""

    def __init__(self, agent_factory: AgentFactory, agent_details_mode: bool = False):
        self.agent_factory = agent_factory
        self.agent_details_mode = agent_details_mode

    def create_specialized_agent(self, role: str) -> Callable:
        """
        Creates a specialized agent wrapper function for the given role.
        This wrapper handles state management and agent execution.
        """
        logger.debug(f"Creating specialized agent wrapper for role: {role}")

        async def agent_wrapper(state: AgenticWorkflowState) -> dict:
            """
            Wrapper function that executes a specialized agent and manages state.
            This function is called by LangGraph during workflow execution.
            """
            logger.info(f"🤖 Executing {role} agent...")

            # Track current agent execution
            current_task = state.get("current_task")
            if not current_task:
                logger.warning(f"No current task found for {role} agent")
                return {
                    "errors": state.get("errors", [])
                    + [{"agent": role, "error": "No current task assigned"}]
                }

            try:
                # 1. Get agent specification from the registry
                agent_spec = AGENT_REGISTRY.get(role)
                if not agent_spec:
                    raise ValueError(f"No spec found for agent role: {role}")

                # Add the role as both name and role for the factory and rules integration
                agent_spec["name"] = role
                agent_spec["role"] = role

                # 2. Create the agent runnable using the factory
                agent_runnable = self.agent_factory.create_dynamic_agent(agent_spec)
                logger.debug(f"   Dynamically created agent for role: {role}")

                # 3. Construct a rich, context-aware input message with development standards
                # This ensures the agent knows WHY it's performing a task and WHAT standards to follow.

                # Load applicable development rules for this agent
                development_rules = get_rules_for_agent(role)
                security_rules = get_security_rules()

                # For agent details mode, also get full rule information
                if self.agent_details_mode:
                    # Import rule loader to get full rule details
                    from src.applications.oamat.utils.rule_loader import rule_loader

                    full_rules_info = rule_loader.get_rules_for_agent(role)
                    full_security_rules = rule_loader.get_rules_for_agent(
                        "all", ["security"]
                    )

                    enhanced_context = f"""
**AGENT DETAILS MODE ENABLED**

**FULL DEVELOPMENT RULES FOR {role.upper()} AGENT:**
{full_rules_info}

**FULL SECURITY RULES:**
{full_security_rules}

**WORKFLOW CONTEXT:**
- Workflow ID: {state.get('workflow_id', 'unknown')}
- Current Phase: {state.get('current_phase', 'unknown')}
- User Request: {state.get('user_request', 'No request provided')}

**CURRENT TASK:**
{current_task}

**SHARED CONTEXT:**
{state.get('shared_context', {})}

**PREVIOUS AGENT OUTPUTS:**
{state.get('agent_outputs', {})}

**TASK REQUIREMENTS:**
Please complete the assigned task following all applicable development standards and security guidelines.
Ensure your output is structured, professional, and meets the specified requirements.
"""
                else:
                    enhanced_context = f"""
**WORKFLOW CONTEXT:**
- Workflow ID: {state.get('workflow_id', 'unknown')}
- Current Phase: {state.get('current_phase', 'unknown')}
- User Request: {state.get('user_request', 'No request provided')}

**CURRENT TASK:**
{current_task}

**DEVELOPMENT RULES:**
{development_rules}

**SECURITY GUIDELINES:**
{security_rules}

**SHARED CONTEXT:**
{state.get('shared_context', {})}

**PREVIOUS AGENT OUTPUTS:**
{state.get('agent_outputs', {})}

**TASK REQUIREMENTS:**
Please complete the assigned task following all applicable development standards and security guidelines.
"""

                # 4. Execute the agent with the enhanced context
                logger.debug(f"   Invoking {role} agent with enhanced context...")

                # Create input message for the agent
                from langchain_core.messages import HumanMessage

                input_message = HumanMessage(content=enhanced_context)

                # Execute the agent
                result = await agent_runnable.ainvoke(
                    {
                        "messages": [input_message],
                        **state,  # Include all state for context
                    }
                )

                # 5. Process and store the agent's output
                agent_output = {
                    "agent_role": role,
                    "task": current_task,
                    "result": result,
                    "timestamp": (
                        str(
                            logger.handlers[0].formatter.formatTime(
                                logger.makeRecord("temp", 0, "", 0, "", (), None)
                            )
                        )
                        if logger.handlers
                        else "unknown"
                    ),
                    "context_used": (
                        enhanced_context[:500] + "..."
                        if len(enhanced_context) > 500
                        else enhanced_context
                    ),
                }

                # Update state with agent output
                updated_agent_outputs = state.get("agent_outputs", {}).copy()
                updated_agent_outputs[role] = agent_output

                # Mark task as completed
                completed_nodes = state.get("completed_nodes", []).copy()
                current_task_id = (
                    current_task.get("id")
                    if isinstance(current_task, dict)
                    else str(current_task)
                )
                if current_task_id not in completed_nodes:
                    completed_nodes.append(current_task_id)

                logger.info(f"✅ {role} agent completed successfully")

                return {
                    "agent_outputs": updated_agent_outputs,
                    "completed_nodes": completed_nodes,
                    "current_task": None,  # Clear current task
                    "messages": state.get("messages", [])
                    + [input_message]
                    + (result.get("messages", []) if isinstance(result, dict) else []),
                }

            except Exception as e:
                error_msg = f"Error in {role} agent: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Full traceback: {traceback.format_exc()}")

                return {
                    "errors": state.get("errors", [])
                    + [{"agent": role, "error": error_msg, "task": current_task}],
                    "failed_nodes": state.get("failed_nodes", [])
                    + [
                        (
                            current_task.get("id")
                            if isinstance(current_task, dict)
                            else str(current_task)
                        )
                    ],
                }

        return agent_wrapper

    def create_agent_creators_dict(self, roles: list) -> dict[str, Callable]:
        """Create a dictionary of agent creators for all specified roles"""
        return {role: self.create_specialized_agent(role) for role in roles}
