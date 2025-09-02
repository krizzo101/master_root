"""
LangGraph Agentic Orchestrator for OAMAT: Best of both worlds.

Combines:
- ManagerAgent: Dynamic workflow planning and generation
- LangGraph: Robust state management, parallelism, and execution
- Runtime adaptation: Modify graphs during execution

This orchestrator provides the benefits of both intelligent planning
and battle-tested LangGraph execution infrastructure.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

# LangGraph imports
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# OAMAT imports
from src.applications.oamat.agents.enhanced_manager_agent import (
    AGENT_REGISTRY,
    EnhancedManagerAgent,
    EnhancedWorkflowPlan,
)
from src.applications.oamat.agents.langgraph_base_agent import LangGraphAgentFactory

# WorkflowDefinition moved to archive (unused)
from src.applications.oamat.db.neo4j_client import Neo4jClient
from src.applications.oamat.utils.error_recovery import handle_agent_error
from src.applications.oamat.utils.rule_loader import (
    get_rules_for_agent,
    get_security_rules,
)

logger = logging.getLogger("OAMAT.LangGraphAgenticOrchestrator")


# LangGraph State Definition
class AgenticWorkflowState(TypedDict):
    """State for LangGraph-based agentic workflows with native context management"""

    # Core execution state
    workflow_id: str
    user_request: str
    current_phase: str

    # Manager planning
    workflow_plan: Optional[Dict[str, Any]]
    planned_nodes: List[Dict[str, Any]]

    # Execution tracking
    completed_nodes: List[str]
    failed_nodes: List[str]
    node_outputs: Dict[str, Any]
    current_task: Optional[Dict[str, Any]]
    next_agent: Optional[str]  # For routing

    # NATIVE CONTEXT FLOW: Agent outputs stored here automatically
    agent_outputs: Dict[str, Any]  # e.g., {"researcher": {...}, "coder": {...}}

    # Dynamic agent management
    generated_agents: Dict[str, Any]  # Dynamically created agents
    agent_registry: Dict[str, Any]  # Runtime agent registry

    # Context and coordination
    shared_context: Dict[str, Any]
    thread_id: Optional[str]

    # Messages and interactions
    messages: Annotated[List[Any], add_messages]

    # Error handling
    errors: List[Dict[str, Any]]
    retry_count: int

    # Results
    final_output: Optional[Dict[str, Any]]
    success: bool

    # FIXED: Add remaining_steps field required by create_react_agent
    remaining_steps: int


class ModernWorkflowOrchestrator:
    """
    Modern workflow orchestrator using LangGraph best practices.
    """

    def __init__(
        self, neo4j_client: Neo4jClient = None, llm_config: Dict[str, Any] = None
    ):
        self.neo4j_client = neo4j_client or Neo4jClient(
            uri="bolt://localhost:7687", user="neo4j", password="oamatdbtest"
        )

        self.llm_config = llm_config or {"model": "gpt-4.1", "mode": "responses"}

        self.manager_agent = self._create_manager_agent()
        self.agent_factory = LangGraphAgentFactory(
            llm_config=self.llm_config, neo4j_client=self.neo4j_client
        )
        self.memory_saver = MemorySaver()
        self.agent_roles = list(
            AGENT_REGISTRY.keys()
        )  # Dynamically get all agent roles
        logger.info(
            "ModernWorkflowOrchestrator initialized with LangGraph best practices"
        )

    def _create_manager_agent(self) -> EnhancedManagerAgent:
        """Create and configure the manager agent with o3 reasoning model"""
        model = "o3"
        logger.info(f"🧠 Creating ManagerAgent with o3 reasoning model: {model}")
        return EnhancedManagerAgent(neo4j_client=self.neo4j_client, model=model)

    def create_dynamic_workflow_graph(
        self, workflow_plan: EnhancedWorkflowPlan
    ) -> StateGraph:
        """Creates a dynamic LangGraph workflow from the sophisticated plan."""
        graph = StateGraph(AgenticWorkflowState)

        # Add supervisor node that coordinates the workflow
        graph.add_node("supervisor", self._supervisor_node)

        # Add specialized agent nodes
        for node in workflow_plan.nodes:
            agent_wrapper = self._create_specialized_agent(node.agent_role)
            graph.add_node(node.id, agent_wrapper)

        # Add completion node for final output formatting
        graph.add_node("completion", self._create_completion_node())

        # Set entry point
        graph.set_entry_point("supervisor")

        # 🚀 PARALLEL EXECUTION SUPPORT
        if workflow_plan.strategy == "parallel":
            # For parallel workflows, create concurrent execution paths
            parallel_batches = self._group_parallel_nodes(workflow_plan.nodes)

            for batch_id, batch_nodes in enumerate(parallel_batches):
                if len(batch_nodes) > 1:
                    # Multiple nodes can run in parallel
                    for node in batch_nodes:
                        graph.add_edge("supervisor", node.id)
                        # All parallel nodes go to completion or next batch
                        next_batch = parallel_batches.get(batch_id + 1)
                        if next_batch:
                            graph.add_edge(
                                node.id, "supervisor"
                            )  # Route back for next batch
                        else:
                            graph.add_edge(node.id, "completion")
                else:
                    # Single node - standard routing
                    node = batch_nodes[0]
                    graph.add_edge("supervisor", node.id)
                    graph.add_edge(node.id, "completion")
        else:
            # Standard routing logic for linear workflows
            def router(state: AgenticWorkflowState) -> str:
                completed_nodes = state.get("completed_nodes", [])
                planned_nodes = state.get("planned_nodes", [])

                for node in planned_nodes:
                    node_id = node.get("id")
                    if node_id not in completed_nodes:
                        return node_id
                return "completion"

            graph.add_conditional_edges("supervisor", router)

            # Add edges from each agent back to supervisor
            for node in workflow_plan.nodes:
                graph.add_edge(node.id, "supervisor")

            # Add edge to completion when done
            graph.add_edge("completion", END)

        return graph.compile(checkpointer=self.memory_saver)

    def _group_parallel_nodes(self, nodes: List) -> Dict[int, List]:
        """Groups nodes into parallel execution batches based on dependencies."""
        batches = {}
        batch_id = 0
        remaining_nodes = nodes.copy()
        completed_nodes = set()

        while remaining_nodes:
            current_batch = []
            nodes_to_remove = []

            for node in remaining_nodes:
                # Check if node's dependencies are satisfied
                dependencies_met = True
                if hasattr(node, "dependencies") and node.dependencies:
                    for dep in node.dependencies:
                        if dep not in completed_nodes:
                            dependencies_met = False
                            break

                if dependencies_met:
                    current_batch.append(node)
                    nodes_to_remove.append(node)
                    completed_nodes.add(node.id)

            if current_batch:
                batches[batch_id] = current_batch
                batch_id += 1

                # Remove processed nodes
                for node in nodes_to_remove:
                    remaining_nodes.remove(node)
            else:
                # No progress possible - break to avoid infinite loop
                if remaining_nodes:
                    batches[batch_id] = remaining_nodes
                break

        return batches

    def _supervisor_node(self, state: AgenticWorkflowState) -> dict:
        """Deterministic supervisor node that dispatches tasks based on the plan."""
        logger.debug("--- SUPERVISOR NODE ---")
        planned_nodes = state.get("planned_nodes", [])
        completed_nodes = state.get("completed_nodes", [])

        logger.debug(f"Planned Nodes: {[node.get('id') for node in planned_nodes]}")
        logger.debug(f"Completed Nodes: {completed_nodes}")

        next_node_to_execute = None
        if planned_nodes:
            for node in planned_nodes:
                if node["id"] not in completed_nodes:
                    next_node_to_execute = node
                    break

        if next_node_to_execute:
            agent_role = next_node_to_execute.get("agent_role")
            if agent_role in self.agent_roles:
                logger.debug(
                    f"Dispatching task '{next_node_to_execute['id']}' to agent '{agent_role}'"
                )
                # Set the next agent for the router and the current task for the agent
                return {
                    "next_agent": agent_role,
                    "current_task": next_node_to_execute,
                    "messages": [
                        (
                            "ai",
                            f"Dispatching to {agent_role} for task {next_node_to_execute['id']}",
                        )
                    ],
                }
            else:
                logger.warning(
                    f"⚠️ Agent '{agent_role}' not found for task '{next_node_to_execute['id']}'. Skipping."
                )
                state["failed_nodes"] = state.get("failed_nodes", []) + [
                    next_node_to_execute["id"]
                ]
                # Route back to self to re-evaluate
                return {
                    "next_agent": "supervisor",
                    "messages": [("ai", f"Agent {agent_role} not found.")],
                }

        else:
            logger.debug("All planned nodes are complete. Routing to completion.")
            return {
                "next_agent": "completion",
                "messages": [("ai", "Workflow complete.")],
            }

    def _create_specialized_agent(self, role: str):
        """
        Creates and invokes a real, specialized agent using the agent factory.
        This replaces the previous placeholder implementation.
        """

        async def agent_wrapper(state: AgenticWorkflowState) -> dict:
            """Wrapper that handles agent creation, execution, and state management"""
            logger.info(
                f"🤖 [{datetime.now().strftime('%H:%M:%S')}] {role.upper()} AGENT EXECUTING..."
            )

            task_info = state.get("current_task")
            if not task_info:
                logger.warning(
                    "   ⚠️ No current task found in state. Returning to supervisor."
                )
                return {"messages": [("ai", "No task found for agent.")]}

            node_id = task_info.get("id", "unknown")
            task_description = task_info.get("task_type", "No description provided.")

            logger.debug(f"   Node: {node_id}")
            logger.debug(f"   Task: {task_description}")

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

                prompt = f"""
                **Project Context**
                User's Goal: {state.get('user_request')}
                Overall Plan: {[node.get('id') for node in state.get('planned_nodes', [])]}
                Completed Steps: {state.get('completed_nodes', [])}

                **Your Current Task**
                Your Role: {role}
                Task ID: {node_id}
                Task Description: {task_description}

                {development_rules}

                {security_rules}

                **EXECUTION REQUIREMENTS:**
                - Follow ALL applicable development standards listed above
                - Ensure code quality, security, and best practices compliance
                - Generate production-ready, maintainable code
                - Include proper error handling and input validation
                - Add appropriate documentation and comments

                Please execute your task based on the provided description, keeping the overall project context and development standards in mind.
                """

                # Special handling for the reflexion agent to give it full final context
                if role == "reflexion":
                    prompt = f"""
                    **Postmortem Analysis Request**

                    The workflow has completed. Please provide a detailed analysis.

                    User's Goal: {state.get('user_request')}

                    Workflow Plan:
                    {json.dumps(state.get('workflow_plan', {}), indent=2)}

                    Execution Summary:
                    Completed Nodes: {state.get('completed_nodes', [])}
                    Failed Nodes: {state.get('failed_nodes', [])}

                    Node Outputs:
                    {json.dumps(state.get('node_outputs', {}), indent=2)}

                    Based on all this information, analyze what went well, what went wrong, and what could be improved for future workflows. Be specific and actionable.
                    """

                messages = [HumanMessage(content=prompt)]

                # 4. Invoke the agent with the constructed message
                agent_output = await agent_runnable.ainvoke({"messages": messages})

                # Extract the last message content as the result
                output_message = agent_output.get("messages", [])[-1]
                output_content = (
                    output_message.content
                    if hasattr(output_message, "content")
                    else str(output_message)
                )

                logger.info(f"   ✅ Agent {role} completed task '{node_id}'")
                logger.debug(f"   Output: {output_content[:200]}...")

            except Exception as e:
                logger.error(f"   ❌ Agent {role} failed on task '{node_id}': {e}")

                # Enhanced error handling with recovery
                try:
                    # Build error context with required fields
                    error_context = state.copy()
                    error_context.update(
                        {"agent_role": role, "node_id": node_id, "task_id": node_id}
                    )

                    recovery_result = await handle_agent_error(
                        error=e, context=error_context
                    )

                    if recovery_result.get("recovery_successful", False):
                        # Recovery successful - update state and continue
                        logger.info(
                            f"   🔄 Recovery successful for {role}: {recovery_result.get('recovery_message')}"
                        )

                        # Apply state modifications from recovery
                        if recovery_result.get("modified_state"):
                            state.update(recovery_result["modified_state"])

                        if recovery_result.get("continue_workflow", False):
                            # If recovery suggests continuing, provide a recovery message instead of failing
                            output_content = f"Agent {role} recovered from error using {recovery_result.get('recovery_strategy')}: {recovery_result.get('recovery_message')}"
                        else:
                            # Recovery completed but task should be marked as failed
                            output_content = f"Agent {role} failed but recovery applied: {recovery_result.get('recovery_message')}"
                            state["failed_nodes"] = state.get("failed_nodes", []) + [
                                node_id
                            ]
                    else:
                        # Recovery failed - mark as failed and continue
                        logger.error(
                            f"   💥 Recovery failed for {role}: {recovery_result.get('recovery_message')}"
                        )
                        output_content = f"Agent {role} failed with error: {e}. Recovery attempted but unsuccessful: {recovery_result.get('recovery_message')}"
                        state["failed_nodes"] = state.get("failed_nodes", []) + [
                            node_id
                        ]

                except ImportError:
                    # Fallback to basic error handling if enhanced handler not available
                    logger.warning(
                        "Enhanced error handling not available, using basic error handling"
                    )
                    output_content = f"Agent {role} failed with error: {e}"
                    state["failed_nodes"] = state.get("failed_nodes", []) + [node_id]
                except Exception as recovery_error:
                    # Error in error handling - use basic fallback
                    logger.error(f"Error in error recovery system: {recovery_error}")
                    output_content = f"Agent {role} failed with error: {e}. Error recovery also failed: {recovery_error}"
                    state["failed_nodes"] = state.get("failed_nodes", []) + [node_id]

            # 4. Update state
            completed_nodes = state.get("completed_nodes", []) + [node_id]
            node_outputs = state.get("node_outputs", {})
            node_outputs[node_id] = output_content

            # The message back to the supervisor
            return {
                "completed_nodes": completed_nodes,
                "node_outputs": node_outputs,
                "messages": [("ai", output_content)],
            }

        return agent_wrapper

    def _create_completion_node(self):
        """Creates the node that handles workflow completion."""

        def completion_node(state: AgenticWorkflowState) -> dict:
            """Final node to prepare and log the workflow's output."""
            print(f"\n🏁 [{datetime.now().strftime('%H:%M:%S')}] WORKFLOW COMPLETE")
            final_output = {
                "result": "Workflow executed successfully.",
                "success": True,
                "workflow_id": state["workflow_id"],
                "completed_nodes": state.get("completed_nodes", []),
                "node_outputs": state.get("node_outputs", {}),
                "timestamp": datetime.now().isoformat(),
            }
            print(f"   Workflow ID: {final_output['workflow_id']}")
            print(f"   Completed Nodes: {len(final_output['completed_nodes'])}")

            return {
                "final_output": final_output,
                "success": True,
                "messages": [("ai", "Workflow finished.")],
            }

        return completion_node

    def _create_unified_project_name(self, user_request: str) -> str:
        """Create a unified project name from the user request that all agents will share."""
        import re
        from datetime import datetime

        # Extract key words from user request for a meaningful project name
        words = re.findall(r"\b\w+\b", user_request.lower())
        # Filter out common words and keep meaningful ones
        meaningful_words = [
            w
            for w in words
            if w
            not in {
                "and",
                "or",
                "the",
                "a",
                "an",
                "to",
                "for",
                "of",
                "in",
                "on",
                "at",
                "by",
                "with",
            }
        ]

        # Take first 3-4 meaningful words and join with hyphens
        project_words = (
            meaningful_words[:3] if len(meaningful_words) >= 3 else meaningful_words
        )
        if not project_words:
            project_words = ["oamat", "project"]

        project_base = "-".join(project_words)

        # Add timestamp for uniqueness but keep it readable
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{project_base}-{timestamp}"

    async def execute_agentic_workflow(
        self, user_request: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute an agentic workflow from a user request."""
        workflow_id = str(uuid.uuid4())
        logger.info(f"🚀 Starting modern workflow {workflow_id}: {user_request}")

        try:
            analysis = self.manager_agent.analyze_request(user_request, context)
            logger.info(
                f"📊 Request analysis complete: {analysis.primary_intent} ({analysis.domain_category})"
            )

            workflow_plan = self.manager_agent.generate_sophisticated_workflow(
                analysis, user_request, context
            )
            logger.info("✅ Successfully parsed structured workflow JSON")

            # 🎯 PRETTY-PRINT WORKFLOW PLAN FOR ALL RUNS
            print(f"\n{'='*80}")
            print("📋 GENERATED WORKFLOW PLAN")
            print(f"{'='*80}")
            workflow_dict = workflow_plan.model_dump()
            print(f"📌 Title: {workflow_dict.get('title', 'Unnamed Workflow')}")
            print(f"🎯 Strategy: {workflow_dict.get('strategy', 'Unknown')}")
            print(f"⚡ Complexity: {workflow_dict.get('complexity', 'Unknown')}")
            print(
                f"⏱️  Estimated Duration: {workflow_dict.get('estimated_duration_minutes', 'Unknown')} minutes"
            )
            print(f"\n🔗 WORKFLOW NODES ({len(workflow_dict.get('nodes', []))}):")
            for i, node in enumerate(workflow_dict.get("nodes", []), 1):
                print(
                    f"  {i}. [{node.get('agent_role', 'Unknown')}] {node.get('id', 'Unknown')} - {node.get('task_type', 'Unknown')}"
                )
                if node.get("tools_required"):
                    print(f"     🛠️  Tools: {', '.join(node['tools_required'])}")
                if node.get("next_nodes"):
                    print(f"     ➡️  Next: {', '.join(node['next_nodes'])}")
            print(f"{'='*80}\n")

            # FIXED: Set unified project name for entire workflow
            project_name = self._create_unified_project_name(user_request)
            os.environ["OAMAT_CURRENT_PROJECT"] = project_name
            logger.info(f"📁 Set unified project directory: {project_name}")

            graph = self.create_dynamic_workflow_graph(workflow_plan)
            app = graph

            initial_state = {
                "workflow_id": workflow_id,
                "user_request": user_request,
                "current_phase": "planning",
                "workflow_plan": workflow_plan.model_dump(),
                "planned_nodes": [node.model_dump() for node in workflow_plan.nodes],
                "completed_nodes": [],
                "failed_nodes": [],
                "node_outputs": {},
                "agent_outputs": {},
                "generated_agents": {},
                "agent_registry": {},
                "shared_context": context or {},
                "messages": [],
                "errors": [],
                "retry_count": 0,
                "final_output": None,
                "success": False,
                "remaining_steps": len(workflow_plan.nodes),
                "current_task": None,
                "next_agent": None,  # Initialize next_agent
                "project_name": project_name,  # Add project name to state
            }

            config = {
                "recursion_limit": 250,
                "configurable": {"thread_id": workflow_id},
            }
            final_state = None
            completion_output = None

            # Use astream_events for more detailed logging if needed
            async for event in app.astream(initial_state, config):
                # Process events...
                # The final state is available in the last event
                if "supervisor" in event:
                    final_state = event["supervisor"]
                # Check for completion node output
                if "completion" in event:
                    completion_output = event["completion"]

            # Prefer completion node output, fallback to supervisor final_output
            if completion_output and completion_output.get("final_output"):
                return completion_output["final_output"]
            elif final_state and final_state.get("final_output"):
                return final_state["final_output"]
            elif final_state and final_state.get("success"):
                # If workflow completed successfully but no explicit final_output
                return {
                    "result": "Workflow executed successfully.",
                    "success": True,
                    "workflow_id": workflow_id,
                    "completed_nodes": final_state.get("completed_nodes", []),
                    "node_outputs": final_state.get("node_outputs", {}),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {"error": "Workflow did not complete as expected."}

        except Exception as e:
            logger.error(f"FATAL: Workflow execution failed: {e}", exc_info=True)
            return {"error": str(e)}

    def get_workflow_visualization(self, workflow_plan: EnhancedWorkflowPlan) -> str:
        """Generate Mermaid visualization of the modern workflow"""
        graph = self.create_dynamic_workflow_graph(workflow_plan)
        try:
            # The get_graph().draw_mermaid_png() might not be standard
            # but illustrates the intent. A better way might be to
            # construct the mermaid string manually.
            return graph.get_graph().draw_mermaid_png()
        except Exception:
            return "Could not generate graph visualization."
