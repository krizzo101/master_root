#!/usr/bin/env python3
"""
Subdivision Executor - LangGraph-based Parallel Subdivision Workflow Execution

Executes subdivided workflows using modern LangGraph patterns:
- Send API for parallel subdivision agent coordination
- Tool-based handoffs between specialized agents
- State management across subdivision hierarchy
- Result integration and synthesis

Complements the main execution engine for subdivision scenarios.
"""

from datetime import datetime
from typing import Any, Dict, List

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionExecutor:
    """
    Specialized executor for subdivision workflows using LangGraph Send API

    Handles:
    - Parallel execution of subdivision agents
    - Tool-based handoffs between agents
    - State coordination across subdivision hierarchy
    - Result aggregation and integration
    """

    def __init__(self, logger_factory: LoggerFactory = None):
        """Initialize the Subdivision Executor"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        self.logger.info("✅ Subdivision Executor initialized with LangGraph Send API")

    async def execute_subdivision_workflow(
        self,
        state: SmartDecompositionState,
        subdivision_agents: Dict[str, Any],
        debug: bool = False,
    ) -> SmartDecompositionState:
        """
        Execute subdivision workflow using LangGraph Send API for parallel coordination

        Args:
            state: Current execution state
            subdivision_agents: Dictionary of specialized subdivision agents
            debug: Enable detailed logging

        Returns:
            Updated state with subdivision results
        """
        if debug:
            self.logger.info(
                "🏭 SUBDIVISION EXECUTOR: Starting parallel subdivision workflow..."
            )

        execution_start_time = datetime.now()

        try:
            # Build LangGraph StateGraph for subdivision execution
            subdivision_graph = self._build_subdivision_graph(subdivision_agents, debug)

            # Convert state to dict for StateGraph execution
            state_dict = {
                "user_request": state.get("user_request", ""),
                "project_path": state.get("project_path", ""),
                "context": state.get("context", {}),
                "specialized_agents": state.get("specialized_agents", {}),
                "agent_outputs": state.get("agent_outputs", {}),
                "subdivision_mode": True,
                "subdivision_metadata": state.get("context", {}).get(
                    "subdivision_metadata", {}
                ),
            }

            if debug:
                self.logger.info(
                    f"🔄 Executing subdivision graph with {len(subdivision_agents)} agents"
                )

            # Execute the subdivision StateGraph
            result_state = await subdivision_graph.ainvoke(state_dict)

            # Calculate execution time
            execution_time = (
                datetime.now() - execution_start_time
            ).total_seconds() * 1000

            # Update original state with results
            state["agent_outputs"] = result_state.get("agent_outputs", {})
            state["context"].update(result_state.get("context", {}))

            if debug:
                self.logger.info(
                    f"✅ Subdivision workflow completed in {execution_time:.0f}ms"
                )
                self.logger.info(
                    f"📊 Subdivision agents executed: {len(result_state.get('agent_outputs', {}))}"
                )

            return state

        except Exception as e:
            execution_time = (
                datetime.now() - execution_start_time
            ).total_seconds() * 1000
            self.logger.error(
                f"❌ Subdivision workflow execution failed after {execution_time:.0f}ms: {e}"
            )
            raise RuntimeError(f"Subdivision execution failed: {e}")

    def _build_subdivision_graph(
        self, subdivision_agents: Dict[str, Any], debug: bool = False
    ) -> StateGraph:
        """Build LangGraph StateGraph for subdivision execution"""

        if debug:
            self.logger.info("🔧 Building subdivision StateGraph...")

        # Create StateGraph with subdivision state schema
        workflow = StateGraph(dict)

        # Add entry point node
        workflow.add_node("subdivision_coordinator", self._subdivision_coordinator_node)

        # Add specialized agent nodes
        for agent_id, agent_data in subdivision_agents.items():
            workflow.add_node(
                f"execute_{agent_id}",
                self._create_agent_execution_node(agent_id, agent_data),
            )

        # Add result aggregation node
        workflow.add_node("aggregate_subdivision_results", self._aggregate_results_node)

        # Set up graph structure
        workflow.add_edge(START, "subdivision_coordinator")

        # Coordinator distributes work to agents using Send API
        workflow.add_conditional_edges(
            "subdivision_coordinator",
            self._create_subdivision_routing,
            # Dynamic agent list based on subdivision_agents
            {agent_id: f"execute_{agent_id}" for agent_id in subdivision_agents},
        )

        # All agents flow to result aggregation
        for agent_id in subdivision_agents:
            workflow.add_edge(f"execute_{agent_id}", "aggregate_subdivision_results")

        workflow.add_edge("aggregate_subdivision_results", END)

        if debug:
            self.logger.info(
                f"🔧 Subdivision graph built with {len(subdivision_agents)} agent nodes"
            )

        return workflow.compile()

    def _subdivision_coordinator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate subdivision workflow execution using Send API"""

        self.logger.info(
            "🎯 SUBDIVISION COORDINATOR: Distributing work to specialized agents..."
        )

        subdivision_agents = state.get("specialized_agents", {})
        user_request = state.get("user_request", "")

        # Prepare work distribution for Send API
        agent_tasks = []

        for agent_id, agent_data in subdivision_agents.items():
            # Create specialized task context for each agent
            agent_context = {
                "agent_id": agent_id,
                "role": agent_data.get("role", ""),
                "specialization": agent_data.get("specialization", ""),
                "task_request": user_request,
                "subdivision_context": state.get("subdivision_metadata", {}),
                "execution_timestamp": datetime.now().isoformat(),
            }

            agent_tasks.append((agent_id, agent_context))

        # Store coordination data in state
        state["subdivision_coordination"] = {
            "total_agents": len(agent_tasks),
            "coordination_timestamp": datetime.now().isoformat(),
            "agent_tasks": {agent_id: context for agent_id, context in agent_tasks},
        }

        self.logger.info(f"🎯 Coordinated {len(agent_tasks)} subdivision agent tasks")

        return state

    def _create_subdivision_routing(self, state: Dict[str, Any]) -> List[Send]:
        """Create Send objects for parallel subdivision agent execution"""

        subdivision_agents = state.get("specialized_agents", {})
        coordination_data = state.get("subdivision_coordination", {})

        # Create Send objects for each subdivision agent
        send_objects = []

        for agent_id in subdivision_agents.keys():
            agent_context = coordination_data.get("agent_tasks", {}).get(agent_id, {})

            # Create Send object with agent-specific state
            agent_state = state.copy()
            agent_state["current_agent_id"] = agent_id
            agent_state["agent_context"] = agent_context

            send_objects.append(Send(f"execute_{agent_id}", agent_state))

        self.logger.info(
            f"🚀 Created {len(send_objects)} Send objects for parallel subdivision execution"
        )

        return send_objects

    def _create_agent_execution_node(self, agent_id: str, agent_data: Dict[str, Any]):
        """Create execution node for a specific subdivision agent"""

        async def execute_subdivision_agent(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a single subdivision agent"""

            self.logger.info(f"🤖 Executing subdivision agent: {agent_id}")

            try:
                agent = agent_data["agent"]
                agent_context = state.get("agent_context", {})
                user_request = state.get("user_request", "")

                # Create specialized prompt for this subdivision agent
                subdivision_prompt = f"""
Task: {user_request}

Subdivision Context:
- Your Role: {agent_context.get('role', 'Unknown')}
- Your Specialization: {agent_context.get('specialization', 'Unknown')}
- Task Focus: Focus on your specialized domain within the larger request

Instructions:
1. Analyze the request from your specialized perspective
2. Complete your designated portion of the work
3. Provide structured output that can be integrated with other agents
4. Include any handoff recommendations if needed

Provide your specialized contribution to this subdivided workflow.
"""

                # Execute the agent
                agent_result = await agent.ainvoke({"input": subdivision_prompt})

                # Extract result content
                if hasattr(agent_result, "content"):
                    result_content = agent_result.content
                elif isinstance(agent_result, dict) and "output" in agent_result:
                    result_content = agent_result["output"]
                else:
                    result_content = str(agent_result)

                # Update state with agent output
                if "agent_outputs" not in state:
                    state["agent_outputs"] = {}

                state["agent_outputs"][agent_id] = {
                    "content": result_content,
                    "role": agent_context.get("role", ""),
                    "specialization": agent_context.get("specialization", ""),
                    "execution_timestamp": datetime.now().isoformat(),
                    "subdivision_agent": True,
                }

                self.logger.info(
                    f"✅ Subdivision agent {agent_id} completed successfully"
                )

                return state

            except Exception as e:
                self.logger.error(
                    f"❌ Subdivision agent {agent_id} execution failed: {e}"
                )

                # Store error information
                if "agent_outputs" not in state:
                    state["agent_outputs"] = {}

                state["agent_outputs"][agent_id] = {
                    "content": f"Agent execution failed: {e}",
                    "error": True,
                    "execution_timestamp": datetime.now().isoformat(),
                    "subdivision_agent": True,
                }

                return state

        return execute_subdivision_agent

    def _aggregate_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all subdivision agents"""

        self.logger.info("🔄 RESULT AGGREGATION: Combining subdivision agent outputs...")

        agent_outputs = state.get("agent_outputs", {})
        successful_agents = 0
        failed_agents = 0

        for agent_id, output in agent_outputs.items():
            if output.get("error", False):
                failed_agents += 1
            else:
                successful_agents += 1

        # Add aggregation metadata to context
        state["context"]["subdivision_execution"] = {
            "total_agents": len(agent_outputs),
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "aggregation_timestamp": datetime.now().isoformat(),
            "execution_mode": "subdivision_workflow",
        }

        self.logger.info(
            f"📊 Subdivision aggregation complete: {successful_agents} successful, {failed_agents} failed"
        )

        return state

    def get_subdivision_execution_metrics(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get metrics about subdivision execution"""

        agent_outputs = state.get("agent_outputs", {})
        subdivision_context = state.get("context", {}).get("subdivision_execution", {})

        return {
            "execution_mode": "subdivision_workflow",
            "total_agents": len(agent_outputs),
            "successful_agents": subdivision_context.get("successful_agents", 0),
            "failed_agents": subdivision_context.get("failed_agents", 0),
            "success_rate": (
                subdivision_context.get("successful_agents", 0) / len(agent_outputs)
                if agent_outputs
                else 0
            ),
            "subdivision_specializations": [
                output.get("specialization", "Unknown")
                for output in agent_outputs.values()
                if not output.get("error", False)
            ],
        }
