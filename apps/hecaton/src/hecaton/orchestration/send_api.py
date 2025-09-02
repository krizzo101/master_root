"""
Send API Orchestrator - Primary HECATON orchestration using LangGraph
Enables true parallel multi-agent execution with 3-5x performance improvement
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Individual agent task with validation"""

    agent_id: str
    agent_type: str
    task_prompt: str
    token_index: int
    worktree_path: str
    mcp_profile: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    permission_mode: str = "plan"
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class OrchestrationState:
    """Typed state for Send API orchestration"""

    main_task: str
    num_agents: int
    agent_tasks: List[AgentTask] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    phase: str = "initialized"
    errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    max_parallel: int = 5


class SendAPIOrchestrator:
    """
    Primary orchestrator using LangGraph's Send API for true parallel execution.

    This is the DEFAULT orchestrator for HECATON, providing:
    - True parallel agent execution without asyncio limitations
    - 3-5x performance improvement over sequential execution
    - Proper state management across parallel agents
    - Automatic error recovery and result aggregation
    """

    def __init__(
        self,
        executor,
        token_pool,
        worktree_manager,
        performance_monitor=None,
        max_parallel: int = 5,
    ):
        """
        Initialize Send API orchestrator with required components.

        Args:
            executor: RealClaudeSubprocessExecutor instance
            token_pool: SecureTokenPool for CLAUDE_CODE_TOKEN management
            worktree_manager: WorktreeManager for git isolation
            performance_monitor: Optional PerformanceMonitor for metrics
            max_parallel: Max agents to run in parallel (default 5)
        """
        self.executor = executor
        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.performance_monitor = performance_monitor
        self.max_parallel = max_parallel
        self.workflow = self._build_workflow()

        logger.info(f"Send API Orchestrator initialized (max_parallel={max_parallel})")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with Send API pattern.

        Graph structure:
        START -> plan_agents -> fan_out -> [run_agent (parallel)] -> aggregate -> END
        """
        workflow = StateGraph(OrchestrationState)

        # Add nodes
        workflow.add_node("plan_agents", self._plan_agents)
        workflow.add_node("fan_out", self._fan_out)
        workflow.add_node("run_agent", self._run_agent)
        workflow.add_node("aggregate", self._aggregate_results)

        # Define flow
        workflow.add_edge(START, "plan_agents")
        workflow.add_edge("plan_agents", "fan_out")
        # Fan-out uses Send API for parallel execution
        workflow.add_edge("fan_out", "run_agent")
        workflow.add_edge("run_agent", "aggregate")
        workflow.add_edge("aggregate", END)

        return workflow.compile()

    async def _plan_agents(self, state: OrchestrationState) -> OrchestrationState:
        """
        Plan agent tasks based on main task and available resources.
        """
        logger.info(f"Planning {state.num_agents} agents for: {state.main_task}")

        # Agent role definitions with tool requirements
        agent_configs = {
            "code": {
                "mcp_profile": None,  # No MCP for code agents
                "allowed_tools": ["Read", "Write", "Edit"],
                "system_prompt": "You write code directly with no preamble. Keep diffs minimal and idiomatic.",
            },
            "test": {
                "mcp_profile": None,  # No MCP for test agents
                "allowed_tools": [
                    "Read",
                    "Write",
                    "Edit",
                    "Bash(pytest:*)",
                    "Bash(npm test:*)",
                ],
                "system_prompt": "You create/maintain tests. Never edit non-test code.",
            },
            "research": {
                "mcp_profile": "research",  # Uses web search MCP
                "allowed_tools": ["Read", "WebSearch"],
                "system_prompt": "You synthesize findings with citations. Prefer primary docs.",
            },
            "review": {
                "mcp_profile": None,
                "allowed_tools": ["Read"],
                "system_prompt": "You review code for quality, security, and best practices.",
            },
            "docs": {
                "mcp_profile": None,
                "allowed_tools": ["Read", "Write", "Edit"],
                "system_prompt": "You write clear documentation. Focus on why, not what.",
            },
        }

        # Select agent types
        available_types = list(agent_configs.keys())
        selected_types = available_types[: state.num_agents]

        # Create agent tasks
        agent_tasks = []
        for i, agent_type in enumerate(selected_types):
            config = agent_configs[agent_type]

            # Acquire token from pool (round-robin)
            token, token_idx = self.token_pool.acquire()

            # Create isolated worktree
            agent_id = f"agent_{i}_{agent_type}_{uuid4().hex[:8]}"
            worktree = self.worktree_manager.create(agent_id)

            task = AgentTask(
                agent_id=agent_id,
                agent_type=agent_type,
                task_prompt=f"{state.main_task}\n\n[{agent_type.upper()} AGENT]: {config['system_prompt']}",
                token_index=token_idx,
                worktree_path=str(worktree),
                mcp_profile=config["mcp_profile"],
                allowed_tools=config["allowed_tools"],
                permission_mode="plan",  # Always use plan mode for safety
            )
            agent_tasks.append(task)

            # Start performance tracking
            if self.performance_monitor:
                self.performance_monitor.start_tracking(agent_id)

        state.agent_tasks = agent_tasks
        state.phase = "planned"
        return state

    async def _fan_out(self, state: OrchestrationState) -> List[Send]:
        """
        Create Send objects for parallel execution.

        This is the CRITICAL Send API pattern - returns Send objects
        that LangGraph uses to route tasks in parallel.
        """
        sends = []

        # Apply parallelism limit
        active_tasks = state.agent_tasks[: state.max_parallel]

        for task in active_tasks:
            # Each Send carries the task to run_agent node
            sends.append(Send("run_agent", {"task": task, "executor": self.executor}))

        logger.info(
            f"Fanning out {len(sends)} agents (max_parallel={state.max_parallel})"
        )
        return sends

    async def _run_agent(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute individual agent task (runs in parallel).

        This node is invoked once per Send object in parallel.
        """
        task = inputs["task"]
        executor = inputs["executor"]

        logger.info(f"Running {task.agent_id} ({task.agent_type})")

        try:
            # Build headless Claude command
            result = await executor.execute_task(
                {
                    "id": task.agent_id,
                    "prompt": task.task_prompt,
                    "agent_type": task.agent_type,
                    "worktree": task.worktree_path,
                    "token_index": task.token_index,
                    "mcp_profile": task.mcp_profile,
                    "allowed_tools": task.allowed_tools,
                    "permission_mode": task.permission_mode,
                }
            )

            task.status = "completed"
            task.result = result

        except asyncio.TimeoutError:
            logger.error(f"{task.agent_id} timed out")
            task.status = "timeout"
            task.error = "Agent execution timed out"

        except Exception as e:
            logger.error(f"{task.agent_id} failed: {e}")
            task.status = "failed"
            task.error = str(e)

        return {"task": task}

    async def _aggregate_results(self, state: OrchestrationState) -> OrchestrationState:
        """
        Aggregate results from all parallel agents.
        """
        logger.info("Aggregating results from parallel agents")

        # Collect results from completed tasks
        results = {}
        metrics = {"total": len(state.agent_tasks), "completed": 0, "failed": 0}

        for task in state.agent_tasks:
            results[task.agent_id] = {
                "type": task.agent_type,
                "status": task.status,
                "result": task.result,
                "error": task.error,
            }

            if task.status == "completed":
                metrics["completed"] += 1
            else:
                metrics["failed"] += 1
                state.errors.append(f"{task.agent_id}: {task.error}")

            # End performance tracking
            if self.performance_monitor:
                self.performance_monitor.end_tracking(
                    task.agent_id, success=(task.status == "completed")
                )

        # Calculate performance stats
        if self.performance_monitor:
            perf_stats = self.performance_monitor.calculate_statistics()
            metrics.update(perf_stats)

        state.results = results
        state.performance_metrics = metrics
        state.phase = "completed"

        # Cleanup worktrees
        for task in state.agent_tasks:
            try:
                self.worktree_manager.cleanup(task.agent_id, force=True)
            except Exception as e:
                logger.warning(f"Worktree cleanup failed for {task.agent_id}: {e}")

        logger.info(
            f"Completed: {metrics['completed']}/{metrics['total']} agents succeeded"
        )
        return state

    async def execute(self, task: str, num_agents: int = 2) -> Dict[str, Any]:
        """
        Execute task using Send API parallel orchestration.

        Args:
            task: Main task description
            num_agents: Number of parallel agents (2-15)

        Returns:
            Dictionary with results and performance metrics
        """
        # Cap agents at token pool size
        max_agents = min(num_agents, self.token_pool.get_token_count(), 15)

        # Initialize state
        initial_state = OrchestrationState(
            main_task=task, num_agents=max_agents, max_parallel=self.max_parallel
        )

        try:
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "results": final_state.results,
                "metrics": final_state.performance_metrics,
                "errors": final_state.errors,
                "phase": final_state.phase,
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                "results": {},
                "metrics": {"error": str(e)},
                "errors": [str(e)],
                "phase": "failed",
            }
