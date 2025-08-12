"""
Phase 3: Multi-Agent Orchestration for ASEA-LangGraph Integration

Implements advanced multi-agent capabilities including:
1. Parallel Agent Execution
2. Agent Coordination and Communication
3. Distributed Task Management
4. Result Aggregation and Synthesis
5. Cross-Agent State Sharing
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ASEAState, update_state_for_plugin
from .enhanced_workflows import EnhancedWorkflowBuilder, StreamingManager
from .error_recovery import ErrorRecoveryManager, create_default_error_patterns


class AgentRole(Enum):
    """Agent role types for multi-agent orchestration."""

    COORDINATOR = "coordinator"  # Orchestrates other agents
    SPECIALIST = "specialist"  # Domain-specific expertise
    CRITIC = "critic"  # Quality assessment and review
    SYNTHESIZER = "synthesizer"  # Combines multiple agent outputs
    RESEARCHER = "researcher"  # Information gathering
    VALIDATOR = "validator"  # Validation and verification


class ExecutionMode(Enum):
    """Agent execution modes."""

    SEQUENTIAL = "sequential"  # Agents execute one after another
    PARALLEL = "parallel"  # Agents execute simultaneously
    PIPELINE = "pipeline"  # Output of one feeds into next
    COMPETITIVE = "competitive"  # Multiple agents compete, best result wins
    COLLABORATIVE = "collaborative"  # Agents share state and coordinate


@dataclass
class AgentDefinition:
    """Definition of an agent in multi-agent workflow."""

    agent_id: str
    role: AgentRole
    plugin_class: type
    input_mapping: Dict[str, str]
    output_mapping: Dict[str, str]
    plugin_config: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    timeout_seconds: Optional[int] = None
    retry_config: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class AgentExecution:
    """Tracks execution of a single agent."""

    agent_id: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    thread_id: Optional[str] = None
    retry_count: int = 0


class AgentCoordinator:
    """
    Coordinates execution of multiple agents with different orchestration patterns.

    Provides:
    - Parallel and sequential execution modes
    - Dependency management between agents
    - Cross-agent communication and state sharing
    - Result aggregation and synthesis
    - Distributed error handling
    """

    def __init__(self, max_workers: int = 4):
        self.agents: Dict[str, AgentDefinition] = {}
        self.execution_history: List[AgentExecution] = []
        self.shared_state: Dict[str, Any] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.streaming_manager = StreamingManager(enable_streaming=True)
        self.recovery_manager = create_default_error_patterns()

        # Communication channels between agents
        self.message_queues: Dict[str, List[Dict[str, Any]]] = {}
        self.state_locks = threading.RLock()

    def register_agent(self, agent_definition: AgentDefinition) -> "AgentCoordinator":
        """
        Register an agent for orchestration.

        Args:
            agent_definition: Complete agent definition

        Returns:
            Self for method chaining
        """
        self.agents[agent_definition.agent_id] = agent_definition
        self.message_queues[agent_definition.agent_id] = []

        # Configure retry for this agent if specified
        if agent_definition.retry_config:
            self.recovery_manager.configure_retry(
                agent_definition.agent_id, **agent_definition.retry_config
            )

        return self

    def add_agent_dependency(
        self, agent_id: str, depends_on: str
    ) -> "AgentCoordinator":
        """Add a dependency between agents."""
        if agent_id in self.agents:
            self.agents[agent_id].dependencies.append(depends_on)
        return self

    def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Send a message between agents."""
        with self.state_locks:
            if to_agent in self.message_queues:
                self.message_queues[to_agent].append(
                    {
                        "from": from_agent,
                        "timestamp": datetime.now().isoformat(),
                        "message": message,
                    }
                )

    def get_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages for an agent."""
        with self.state_locks:
            messages = self.message_queues.get(agent_id, []).copy()
            self.message_queues[agent_id] = []  # Clear after reading
            return messages

    def update_shared_state(self, updates: Dict[str, Any]):
        """Update shared state accessible by all agents."""
        with self.state_locks:
            self.shared_state.update(updates)

    def get_shared_state(self) -> Dict[str, Any]:
        """Get current shared state."""
        with self.state_locks:
            return self.shared_state.copy()

    def execute_parallel(
        self,
        agent_ids: List[str],
        base_state: ASEAState,
        execution_mode: ExecutionMode = ExecutionMode.PARALLEL,
    ) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel.

        Args:
            agent_ids: List of agent IDs to execute
            base_state: Base workflow state
            execution_mode: How to execute the agents

        Returns:
            Dictionary of agent results
        """
        if execution_mode == ExecutionMode.SEQUENTIAL:
            return self._execute_sequential(agent_ids, base_state)
        elif execution_mode == ExecutionMode.PARALLEL:
            return self._execute_parallel_concurrent(agent_ids, base_state)
        elif execution_mode == ExecutionMode.PIPELINE:
            return self._execute_pipeline(agent_ids, base_state)
        elif execution_mode == ExecutionMode.COMPETITIVE:
            return self._execute_competitive(agent_ids, base_state)
        elif execution_mode == ExecutionMode.COLLABORATIVE:
            return self._execute_collaborative(agent_ids, base_state)
        else:
            raise ValueError(f"Unsupported execution mode: {execution_mode}")

    def _execute_sequential(
        self, agent_ids: List[str], base_state: ASEAState
    ) -> Dict[str, Any]:
        """Execute agents sequentially."""
        results = {}
        current_state = base_state

        for agent_id in agent_ids:
            if agent_id not in self.agents:
                continue

            self.streaming_manager.emit_update(
                "agent_start",
                {
                    "agent_id": agent_id,
                    "mode": "sequential",
                    "position": len(results) + 1,
                    "total": len(agent_ids),
                },
            )

            try:
                result = self._execute_single_agent(agent_id, current_state)
                results[agent_id] = result

                # Update state with result for next agent
                current_state = self._merge_agent_result(
                    current_state, agent_id, result
                )

                self.streaming_manager.emit_update(
                    "agent_complete",
                    {
                        "agent_id": agent_id,
                        "success": True,
                        "result_keys": list(result.keys())
                        if isinstance(result, dict)
                        else [],
                    },
                )

            except Exception as e:
                results[agent_id] = {"error": str(e)}
                self.streaming_manager.emit_update(
                    "agent_error", {"agent_id": agent_id, "error": str(e)}
                )

        return results

    def _execute_parallel_concurrent(
        self, agent_ids: List[str], base_state: ASEAState
    ) -> Dict[str, Any]:
        """Execute agents concurrently."""
        results = {}
        futures = {}

        # Submit all agents for execution
        for agent_id in agent_ids:
            if agent_id in self.agents:
                future = self.executor.submit(
                    self._execute_single_agent, agent_id, base_state
                )
                futures[future] = agent_id

                self.streaming_manager.emit_update(
                    "agent_start",
                    {
                        "agent_id": agent_id,
                        "mode": "parallel",
                        "total_agents": len(agent_ids),
                    },
                )

        # Collect results as they complete
        for future in as_completed(futures):
            agent_id = futures[future]
            try:
                result = future.result()
                results[agent_id] = result

                self.streaming_manager.emit_update(
                    "agent_complete",
                    {
                        "agent_id": agent_id,
                        "success": True,
                        "completed": len(results),
                        "remaining": len(futures) - len(results),
                    },
                )

            except Exception as e:
                results[agent_id] = {"error": str(e)}
                self.streaming_manager.emit_update(
                    "agent_error", {"agent_id": agent_id, "error": str(e)}
                )

        return results

    def _execute_pipeline(
        self, agent_ids: List[str], base_state: ASEAState
    ) -> Dict[str, Any]:
        """Execute agents in pipeline mode (output of one feeds into next)."""
        results = {}
        current_state = base_state

        for i, agent_id in enumerate(agent_ids):
            if agent_id not in self.agents:
                continue

            self.streaming_manager.emit_update(
                "pipeline_stage",
                {
                    "agent_id": agent_id,
                    "stage": i + 1,
                    "total_stages": len(agent_ids),
                    "input_from": agent_ids[i - 1] if i > 0 else "base_state",
                },
            )

            try:
                # Execute agent with accumulated state
                result = self._execute_single_agent(agent_id, current_state)
                results[agent_id] = result

                # Merge result into state for next stage
                current_state = self._merge_agent_result(
                    current_state, agent_id, result
                )

                # Update shared state for pipeline coordination
                self.update_shared_state(
                    {f"pipeline_stage_{i}": result, "pipeline_current_agent": agent_id}
                )

            except Exception as e:
                results[agent_id] = {"error": str(e)}
                break  # Stop pipeline on error

        return results

    def _execute_competitive(
        self, agent_ids: List[str], base_state: ASEAState
    ) -> Dict[str, Any]:
        """Execute agents competitively and return best result."""
        # Execute all agents in parallel
        all_results = self._execute_parallel_concurrent(agent_ids, base_state)

        # Score results and select winner
        best_agent = None
        best_score = -1

        for agent_id, result in all_results.items():
            if "error" not in result:
                score = self._score_agent_result(agent_id, result)
                if score > best_score:
                    best_score = score
                    best_agent = agent_id

        self.streaming_manager.emit_update(
            "competitive_winner",
            {
                "winner": best_agent,
                "score": best_score,
                "participants": list(agent_ids),
            },
        )

        return {
            "winner": best_agent,
            "winning_result": all_results.get(best_agent, {}),
            "all_results": all_results,
            "scores": {
                aid: self._score_agent_result(aid, result)
                for aid, result in all_results.items()
            },
        }

    def _execute_collaborative(
        self, agent_ids: List[str], base_state: ASEAState
    ) -> Dict[str, Any]:
        """Execute agents collaboratively with state sharing."""
        results = {}

        # Initialize shared collaboration state
        self.update_shared_state(
            {
                "collaboration_session": str(uuid.uuid4()),
                "participating_agents": agent_ids,
                "collaboration_round": 0,
            }
        )

        # Execute in rounds, allowing agents to see each other's work
        max_rounds = 3
        for round_num in range(max_rounds):
            self.update_shared_state({"collaboration_round": round_num})

            round_results = {}
            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    continue

                # Prepare state with previous round results
                collaborative_state = base_state.copy()
                collaborative_state["shared_state"] = self.get_shared_state()
                collaborative_state["previous_results"] = results
                collaborative_state["agent_messages"] = self.get_messages(agent_id)

                try:
                    result = self._execute_single_agent(agent_id, collaborative_state)
                    round_results[agent_id] = result

                    # Share result with other agents
                    self.update_shared_state(
                        {f"agent_{agent_id}_round_{round_num}": result}
                    )

                except Exception as e:
                    round_results[agent_id] = {"error": str(e)}

            results.update(round_results)

            # Check if collaboration should continue
            if self._should_continue_collaboration(round_results, round_num):
                continue
            else:
                break

        return results

    def _execute_single_agent(self, agent_id: str, state: ASEAState) -> Dict[str, Any]:
        """Execute a single agent with error recovery."""
        agent_def = self.agents[agent_id]

        # Create plugin node
        from .plugin_adapter import create_plugin_node

        plugin_node = create_plugin_node(
            plugin_class=agent_def.plugin_class,
            input_mapping=agent_def.input_mapping,
            output_mapping=agent_def.output_mapping,
            plugin_config=agent_def.plugin_config,
        )

        # Execute with recovery if configured
        if agent_def.retry_config:
            result_state = self.recovery_manager.execute_with_recovery(
                agent_id, plugin_node, state
            )
        else:
            result_state = plugin_node(state)

        # Extract agent-specific output
        output_key = agent_def.output_mapping.get("response", agent_id.lower())
        return result_state.get("workflow_state", {}).get(output_key, {})

    def _merge_agent_result(
        self, state: ASEAState, agent_id: str, result: Any
    ) -> ASEAState:
        """Merge agent result into workflow state."""
        new_state = state.copy()
        if "workflow_state" not in new_state:
            new_state["workflow_state"] = {}

        new_state["workflow_state"][f"agent_{agent_id}_result"] = result
        new_state["workflow_state"]["last_agent"] = agent_id

        return new_state

    def _score_agent_result(self, agent_id: str, result: Dict[str, Any]) -> float:
        """Score an agent result for competitive mode."""
        if "error" in result:
            return 0.0

        # Simple scoring based on result completeness and length
        score = 0.0

        if isinstance(result, dict):
            score += len(result) * 0.1  # More fields = higher score

            for key, value in result.items():
                if isinstance(value, str) and len(value) > 50:
                    score += 0.5  # Substantial text content
                elif isinstance(value, (list, dict)) and value:
                    score += 0.3  # Non-empty collections

        elif isinstance(result, str) and len(result) > 100:
            score += 1.0  # Good text response

        return min(score, 10.0)  # Cap at 10.0

    def _should_continue_collaboration(
        self, round_results: Dict[str, Any], round_num: int
    ) -> bool:
        """Determine if collaborative execution should continue."""
        # Simple heuristic: continue if any agent produced new substantial content
        if round_num >= 2:  # Max 3 rounds
            return False

        substantial_results = 0
        for result in round_results.values():
            if "error" not in result and self._score_agent_result("temp", result) > 2.0:
                substantial_results += 1

        return (
            substantial_results >= len(round_results) * 0.5
        )  # At least half produced good results


class MultiAgentWorkflowBuilder:
    """
    Builder for creating multi-agent workflows with orchestration patterns.

    Provides fluent API for:
    - Agent registration and configuration
    - Execution mode selection
    - Dependency management
    - Result aggregation strategies
    """

    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.execution_groups: List[Dict[str, Any]] = []
        self.aggregation_strategy = "merge"  # merge, competitive, collaborative

    def add_agent(
        self,
        agent_id: str,
        role: AgentRole,
        plugin_class: type,
        input_mapping: Dict[str, str],
        output_mapping: Dict[str, str],
        plugin_config: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> "MultiAgentWorkflowBuilder":
        """Add an agent to the workflow."""
        agent_def = AgentDefinition(
            agent_id=agent_id,
            role=role,
            plugin_class=plugin_class,
            input_mapping=input_mapping,
            output_mapping=output_mapping,
            plugin_config=plugin_config,
            description=description,
        )

        self.coordinator.register_agent(agent_def)
        return self

    def add_execution_group(
        self,
        agent_ids: List[str],
        execution_mode: ExecutionMode,
        name: Optional[str] = None,
    ) -> "MultiAgentWorkflowBuilder":
        """Add a group of agents to execute together."""
        self.execution_groups.append(
            {
                "name": name or f"group_{len(self.execution_groups)}",
                "agent_ids": agent_ids,
                "execution_mode": execution_mode,
            }
        )
        return self

    def set_aggregation_strategy(self, strategy: str) -> "MultiAgentWorkflowBuilder":
        """Set how to aggregate results from multiple agents."""
        self.aggregation_strategy = strategy
        return self

    def build_multi_agent_node(self) -> Callable[[ASEAState], ASEAState]:
        """Build a LangGraph node that executes the multi-agent workflow."""

        def multi_agent_node(state: ASEAState) -> ASEAState:
            all_results = {}

            # Execute each group
            for group in self.execution_groups:
                group_name = group["name"]
                agent_ids = group["agent_ids"]
                execution_mode = group["execution_mode"]

                self.coordinator.streaming_manager.emit_update(
                    "group_start",
                    {
                        "group_name": group_name,
                        "agent_count": len(agent_ids),
                        "execution_mode": execution_mode.value,
                    },
                )

                group_results = self.coordinator.execute_parallel(
                    agent_ids, state, execution_mode
                )

                all_results[group_name] = group_results

            # Aggregate results
            aggregated_results = self._aggregate_results(all_results)

            # Update state
            new_state = state.copy()
            if "workflow_state" not in new_state:
                new_state["workflow_state"] = {}

            new_state["workflow_state"]["multi_agent_results"] = aggregated_results
            new_state["workflow_state"]["agent_execution_summary"] = {
                "total_groups": len(self.execution_groups),
                "total_agents": sum(len(g["agent_ids"]) for g in self.execution_groups),
                "aggregation_strategy": self.aggregation_strategy,
            }

            return new_state

        return multi_agent_node

    def _aggregate_results(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all execution groups."""
        if self.aggregation_strategy == "merge":
            # Simple merge of all results
            aggregated = {}
            for group_name, group_results in all_results.items():
                aggregated[group_name] = group_results
            return aggregated

        elif self.aggregation_strategy == "competitive":
            # Find best result across all groups
            best_result = None
            best_score = -1

            for group_name, group_results in all_results.items():
                for agent_id, result in group_results.items():
                    if "error" not in result:
                        score = self.coordinator._score_agent_result(agent_id, result)
                        if score > best_score:
                            best_score = score
                            best_result = {
                                "group": group_name,
                                "agent": agent_id,
                                "result": result,
                                "score": score,
                            }

            return {
                "strategy": "competitive",
                "winner": best_result,
                "all_results": all_results,
            }

        elif self.aggregation_strategy == "collaborative":
            # Synthesize results from all agents
            synthesis = {
                "strategy": "collaborative",
                "individual_contributions": all_results,
                "synthesized_result": self._synthesize_collaborative_results(
                    all_results
                ),
            }
            return synthesis

        else:
            return all_results

    def _synthesize_collaborative_results(
        self, all_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize collaborative results into unified output."""
        synthesis = {
            "key_insights": [],
            "consensus_points": [],
            "diverse_perspectives": [],
            "combined_recommendations": [],
        }

        # Extract insights from all agent results
        for group_name, group_results in all_results.items():
            for agent_id, result in group_results.items():
                if "error" not in result and isinstance(result, dict):
                    # Look for common result patterns
                    if "insights" in result:
                        synthesis["key_insights"].extend(result["insights"])
                    if "recommendations" in result:
                        synthesis["combined_recommendations"].extend(
                            result["recommendations"]
                        )
                    if "analysis" in result:
                        synthesis["diverse_perspectives"].append(
                            {"agent": agent_id, "analysis": result["analysis"]}
                        )

        return synthesis
