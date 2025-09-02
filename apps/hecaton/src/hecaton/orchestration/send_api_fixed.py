"""
Send API Orchestrator - FIXED implementation with proper LangGraph Send pattern
Enables true parallel multi-agent execution without asyncio.gather()
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Sequence
from uuid import uuid4

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# Enhanced logging with context
logging.basicConfig(
    format="%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
    level=logging.DEBUG,
)
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
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class OrchestrationState:
    """Central state for orchestration workflow"""

    main_task: str
    phase: str = "planning"
    agent_tasks: List[AgentTask] = field(default_factory=list)
    completed_tasks: List[AgentTask] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    max_parallel: int = 5
    num_agents: int = 2
    iteration: int = 0
    total_iterations: int = 0


class SendAPIOrchestrator:
    """
    FIXED orchestrator using LangGraph's Send API for true parallel execution.

    This implementation properly uses the Send API pattern to achieve:
    - True parallel agent execution without asyncio.gather()
    - Message-passing based orchestration
    - Proper state management across parallel agents
    - Automatic batching and fan-out/fan-in patterns
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
            executor: RealClaudeExecutor for running Claude agents
            token_pool: Token pool for API key management
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

        logger.info(
            f"🚀 Send API Orchestrator initialized | max_parallel={max_parallel} | tokens_available={token_pool.get_available_count()}"
        )

    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with proper Send API pattern.

        The key difference: We use conditional edges and Send objects
        for true message-based parallel execution, NOT asyncio.gather()
        """
        logger.debug("Building Send API workflow graph")

        workflow = StateGraph(OrchestrationState)

        # Add nodes - each is a processing step
        workflow.add_node("plan_agents", self._plan_agents)
        workflow.add_node(
            "run_agent", self._run_agent
        )  # This runs in parallel via Send
        workflow.add_node("collect_results", self._collect_results)

        # Define edges - the critical part for Send API
        workflow.add_edge(START, "plan_agents")

        # CRITICAL: Use conditional edge that returns Send objects
        # This is where the Send API magic happens!
        workflow.add_conditional_edges(
            "plan_agents",
            self._route_to_agents,  # Returns Send objects for parallel execution
            # No explicit paths needed - Send objects handle routing
        )

        # Agents complete and route to collection
        workflow.add_edge("run_agent", "collect_results")

        # Check if more iterations needed
        workflow.add_conditional_edges(
            "collect_results",
            self._check_completion,
            {"continue": "plan_agents", "end": END},  # More agents to run  # All done
        )

        logger.debug("Workflow graph built successfully")
        return workflow.compile()

    def _plan_agents(self, state: OrchestrationState) -> OrchestrationState:
        """
        Plan and prepare agent tasks for execution.
        """
        iteration_num = state.iteration + 1
        total_to_plan = min(
            state.num_agents - len(state.completed_tasks), state.max_parallel
        )

        logger.info(
            f"📋 Planning agents | iteration={iteration_num} | planning={total_to_plan} | completed={len(state.completed_tasks)}/{state.num_agents}"
        )

        if state.iteration == 0:
            # First iteration - create all tasks
            state.total_iterations = (
                state.num_agents + state.max_parallel - 1
            ) // state.max_parallel
            logger.debug(f"First iteration | total_iterations={state.total_iterations}")

            agent_types = self._determine_agent_types(state.main_task, state.num_agents)

            for i, agent_type in enumerate(agent_types):
                agent_id = f"agent_{agent_type}_{uuid4().hex[:8]}"

                # Acquire token
                token_index = self.token_pool.acquire_token(agent_id)
                if token_index is None:
                    logger.warning(f"⚠️ No token available for {agent_id}")
                    continue

                # Setup worktree
                worktree_path = self.worktree_manager.setup_agent(agent_id)

                task = AgentTask(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    task_prompt=f"{state.main_task} - {agent_type} perspective",
                    token_index=token_index,
                    worktree_path=str(worktree_path),
                )

                state.agent_tasks.append(task)
                logger.debug(
                    f"Created task | agent_id={agent_id} | type={agent_type} | token_idx={token_index}"
                )

        state.phase = "executing"
        state.iteration = iteration_num

        # Log task queue status
        pending = [t for t in state.agent_tasks if t.status == "pending"]
        logger.info(
            f"📊 Task queue | pending={len(pending)} | running=0 | completed={len(state.completed_tasks)}"
        )

        return state

    def _route_to_agents(self, state: OrchestrationState) -> Sequence[Send]:
        """
        CRITICAL METHOD: Returns Send objects for parallel execution.
        This is the core of the Send API pattern - no asyncio.gather() needed!

        Returns:
            List of Send objects that LangGraph executes in parallel
        """
        sends = []
        tasks_to_run = []

        # Get pending tasks up to max_parallel limit
        pending_tasks = [t for t in state.agent_tasks if t.status == "pending"]
        tasks_to_run = pending_tasks[: state.max_parallel]

        logger.info(
            f"🚦 Routing to agents | batch_size={len(tasks_to_run)} | max_parallel={state.max_parallel}"
        )

        for idx, task in enumerate(tasks_to_run, 1):
            task.status = "running"
            task.start_time = datetime.now()

            # Create Send object - this is the key!
            # Each Send creates a parallel execution branch
            send = Send(
                "run_agent",  # Target node
                {
                    "task": task,
                    "executor": self.executor,
                    "task_number": idx,
                    "total_in_batch": len(tasks_to_run),
                },
            )
            sends.append(send)

            logger.debug(
                f"Created Send object | task={idx}/{len(tasks_to_run)} | agent_id={task.agent_id} | type={task.agent_type}"
            )

        logger.info(
            f"📤 Dispatching {len(sends)} Send objects for parallel execution (NOT using asyncio.gather!)"
        )
        return sends

    async def _run_agent(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute individual agent task (runs in parallel via Send API).

        This node is invoked once per Send object in TRUE parallel fashion,
        not Python async concurrency.
        """
        task = inputs["task"]
        executor = inputs["executor"]
        task_num = inputs["task_number"]
        total_batch = inputs["total_in_batch"]

        logger.info(
            f"🤖 Running agent | task={task_num}/{total_batch} | agent_id={task.agent_id} | type={task.agent_type}"
        )

        try:
            # Start performance tracking
            if self.performance_monitor:
                self.performance_monitor.start_tracking(task.agent_id)

            # Log execution details
            logger.debug(
                f"Execution details | agent_id={task.agent_id} | worktree={task.worktree_path} | token_idx={task.token_index}"
            )

            # Build execution request
            execution_request = {
                "id": task.agent_id,
                "prompt": task.task_prompt,
                "agent_type": task.agent_type,
                "worktree": task.worktree_path,
                "token_index": task.token_index,
                "mcp_profile": task.mcp_profile,
                "allowed_tools": task.allowed_tools,
                "permission_mode": task.permission_mode,
            }

            logger.debug(f"Executing Claude subprocess | agent_id={task.agent_id}")

            # Execute via real Claude subprocess
            result = await executor.execute_task(execution_request)

            task.status = "completed"
            task.result = result
            task.end_time = datetime.now()
            execution_time = (task.end_time - task.start_time).total_seconds()

            logger.info(
                f"✅ Agent completed | agent_id={task.agent_id} | execution_time={execution_time:.2f}s | status={result.get('status')}"
            )

            # End performance tracking
            if self.performance_monitor:
                self.performance_monitor.end_tracking(task.agent_id, success=True)

        except asyncio.TimeoutError:
            task.status = "timeout"
            task.error = "Agent execution timed out"
            task.end_time = datetime.now()
            logger.error(f"⏱️ Agent timeout | agent_id={task.agent_id}")

            if self.performance_monitor:
                self.performance_monitor.end_tracking(task.agent_id, success=False)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.now()
            logger.error(
                f"❌ Agent failed | agent_id={task.agent_id} | error={e}", exc_info=True
            )

            if self.performance_monitor:
                self.performance_monitor.end_tracking(task.agent_id, success=False)

        finally:
            # Cleanup resources
            try:
                self.token_pool.release_token(task.agent_id)
                logger.debug(f"Released token | agent_id={task.agent_id}")
            except Exception as e:
                logger.warning(
                    f"Token release failed | agent_id={task.agent_id} | error={e}"
                )

        return {"task": task}

    def _collect_results(self, state: OrchestrationState) -> OrchestrationState:
        """
        Collect results from completed agents in this iteration.
        """
        # Move completed tasks
        newly_completed = [
            t
            for t in state.agent_tasks
            if t.status in ["completed", "failed", "timeout"]
        ]
        state.completed_tasks.extend(newly_completed)

        # Remove from active tasks
        state.agent_tasks = [t for t in state.agent_tasks if t.status == "pending"]

        completed_count = len(state.completed_tasks)
        success_count = len(
            [t for t in state.completed_tasks if t.status == "completed"]
        )
        failed_count = len(
            [t for t in state.completed_tasks if t.status in ["failed", "timeout"]]
        )

        logger.info(
            f"📈 Collection complete | iteration={state.iteration}/{state.total_iterations} | completed={completed_count}/{state.num_agents} | success={success_count} | failed={failed_count}"
        )

        # Update results
        for task in newly_completed:
            state.results[task.agent_id] = {
                "type": task.agent_type,
                "status": task.status,
                "result": task.result,
                "error": task.error,
                "execution_time": (task.end_time - task.start_time).total_seconds()
                if task.end_time and task.start_time
                else None,
            }

            if task.error:
                state.errors.append(f"{task.agent_id}: {task.error}")

        return state

    def _check_completion(self, state: OrchestrationState) -> str:
        """
        Check if all agents are complete or more iterations needed.
        """
        remaining = len([t for t in state.agent_tasks if t.status == "pending"])
        completed = len(state.completed_tasks)

        logger.debug(
            f"Checking completion | completed={completed}/{state.num_agents} | remaining={remaining}"
        )

        if remaining > 0:
            logger.info(
                f"➡️ Continuing to next iteration | remaining={remaining} tasks"
            )
            return "continue"
        else:
            logger.info(f"🏁 All agents complete | total={completed}")
            state.phase = "completed"

            # Calculate final metrics
            if self.performance_monitor:
                state.performance_metrics = (
                    self.performance_monitor.calculate_statistics()
                )

            # Cleanup worktrees
            for task in state.completed_tasks:
                try:
                    self.worktree_manager.cleanup_agent(task.agent_id)
                    logger.debug(f"Cleaned up worktree | agent_id={task.agent_id}")
                except Exception as e:
                    logger.warning(
                        f"Worktree cleanup failed | agent_id={task.agent_id} | error={e}"
                    )

            return "end"

    def _determine_agent_types(self, task: str, num_agents: int) -> List[str]:
        """
        Determine agent types based on task and requested count.
        """
        # Agent type pool
        agent_types = [
            "code",
            "research",
            "test",
            "review",
            "docs",
            "security",
            "performance",
        ]

        # Task keyword mapping
        if "test" in task.lower():
            agent_types = ["test", "code", "review"] + agent_types
        elif "document" in task.lower() or "doc" in task.lower():
            agent_types = ["docs", "research"] + agent_types
        elif "review" in task.lower():
            agent_types = ["review", "test", "security"] + agent_types
        elif "build" in task.lower() or "implement" in task.lower():
            agent_types = ["code", "test", "review"] + agent_types

        # Return requested number of agents
        selected = agent_types[:num_agents]
        logger.debug(f"Selected agent types | types={selected}")
        return selected

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

        logger.info(
            f"🎯 Starting Send API execution | task='{task[:50]}...' | agents={max_agents} | max_parallel={self.max_parallel}"
        )

        # Initialize state
        initial_state = OrchestrationState(
            main_task=task, num_agents=max_agents, max_parallel=self.max_parallel
        )

        try:
            # Execute workflow - THIS is where Send API magic happens
            # No asyncio.gather() - LangGraph handles parallelism via Send objects
            logger.info("🔄 Invoking LangGraph workflow with Send API pattern")
            final_state = await self.workflow.ainvoke(initial_state)

            success_count = len(
                [r for r in final_state.results.values() if r["status"] == "completed"]
            )

            logger.info(
                f"✨ Execution complete | success={success_count}/{max_agents} | errors={len(final_state.errors)}"
            )

            return {
                "results": final_state.results,
                "metrics": {
                    **final_state.performance_metrics,
                    "total_agents": max_agents,
                    "successful": success_count,
                    "failed": max_agents - success_count,
                    "success_rate": success_count / max_agents if max_agents > 0 else 0,
                },
                "errors": final_state.errors,
                "phase": final_state.phase,
            }

        except Exception as e:
            logger.error(f"💥 Orchestration failed | error={e}", exc_info=True)
            return {
                "results": {},
                "metrics": {"error": str(e)},
                "errors": [str(e)],
                "phase": "failed",
            }
