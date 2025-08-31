"""
Send API Orchestrator - Primary HECATON orchestration using LangGraph
Enables true parallel multi-agent execution with 3-5x performance improvement
"""

import asyncio
import logging
import operator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import Annotated

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Individual agent task with validation"""

    agent_id: str
    agent_type: str
    task_prompt: str
    token_index: int
    worktree_path: str
    sequence: int = 0  # For patch ordering
    mcp_profile: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    permission_mode: str = "plan"
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OrchestrationState(TypedDict, total=False):
    """
    Dict-shaped state for LangGraph. Use reducers for parallel-safe merges:
      - results: dict merged with OR (|)  -> last-write-wins per key
      - errors:  list concatenated        -> accumulate all
    """

    main_task: str
    num_agents: int
    agent_tasks: List[AgentTask]
    # substate injected to each parallel 'run_agent' call
    current_task: AgentTask
    # merged artifacts
    results: Annotated[Dict[str, Any], operator.or_]
    errors: Annotated[List[str], operator.add]
    patch_manifests: Annotated[List[Dict[str, Any]], operator.add]
    phase: str
    performance_metrics: Dict[str, float]
    max_parallel: int
    run_id: str


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
        merge_config=None,
    ):
        """
        Initialize Send API orchestrator with required components.

        Args:
            executor: RealClaudeSubprocessExecutor instance
            token_pool: SecureTokenPool for CLAUDE_CODE_TOKEN management
            worktree_manager: WorktreeManager for git isolation
            performance_monitor: Optional PerformanceMonitor for metrics
            max_parallel: Max agents to run in parallel (default 5)
            merge_config: Optional MergeBackConfig for patch integration
        """
        self.executor = executor
        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.performance_monitor = performance_monitor
        self.max_parallel = max_parallel
        self.merge_config = merge_config
        self.merger = None

        # Initialize merger if config provided
        if merge_config and merge_config.enabled:
            from .merger import Merger

            self.merger = Merger(merge_config, worktree_manager)

        self.workflow = self._build_workflow()

        logger.info(f"Send API Orchestrator initialized (max_parallel={max_parallel})")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with Send API pattern.

        Graph structure:
        START -> plan_agents -> run_agent (parallel via Send) -> aggregate -> END
        """
        workflow = StateGraph(OrchestrationState)

        # Add nodes
        workflow.add_node("plan_agents", self._plan_agents)
        workflow.add_node("run_agent", self._run_agent)
        workflow.add_node("aggregate", self._aggregate_results)

        # Define flow
        workflow.add_edge(START, "plan_agents")
        # Use conditional edge for Send API pattern
        workflow.add_conditional_edges("plan_agents", self._route_agents, ["run_agent"])
        workflow.add_edge("run_agent", "aggregate")
        workflow.add_edge("aggregate", END)

        return workflow.compile()

    def _plan_agents(self, state: OrchestrationState) -> Dict[str, Any]:
        """
        Plan agent tasks based on main task and available resources.
        """
        logger.info(f"Planning {state['num_agents']} agents for: {state['main_task']}")

        # Agent role definitions with tool requirements
        agent_configs = {
            "code": {
                "mcp_profile": None,  # No MCP for code agents
                "allowed_tools": ["Read", "Write", "Edit"],
                "system_prompt": (
                    "You write code directly with no preamble. " "Keep diffs minimal and idiomatic."
                ),
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
        selected_types = available_types[: state["num_agents"]]

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
                task_prompt=(
                    f"{state['main_task']}\n\n"
                    f"[{agent_type.upper()} AGENT]: {config['system_prompt']}"
                ),
                token_index=token_idx,
                worktree_path=str(worktree),
                sequence=i,  # Add sequence for patch ordering
                mcp_profile=config["mcp_profile"],
                allowed_tools=config["allowed_tools"],
                permission_mode="plan",  # Always use plan mode for safety
            )
            agent_tasks.append(task)

            # Start performance tracking
            if self.performance_monitor:
                self.performance_monitor.start_tracking(agent_id)

        # Return partial state update
        return {"agent_tasks": agent_tasks, "phase": "planned"}

    def _route_agents(self, state: OrchestrationState):
        """
        Route function that returns Send objects for parallel execution.
        This is used by conditional edges to trigger parallel processing.
        """
        # Throttle by token count or configured max_parallel
        limit = min(state.get("max_parallel", 5), self.token_pool.get_token_count())
        tasks = state["agent_tasks"][:limit]

        # Each Send carries a *substate* with only the fields that the target node needs
        sends = [Send("run_agent", {"current_task": t}) for t in tasks]

        logger.info(f"Routing {len(sends)} agents for parallel execution")
        return sends

    async def _run_agent(self, state: OrchestrationState) -> Dict[str, Any]:
        """
        Execute individual agent task (runs in parallel).
        This node is invoked once per Send object in parallel.
        """
        task = state["current_task"]

        logger.info(f"Running {task.agent_id} ({task.agent_type})")

        try:
            # Execute the task with the provided worktree and run_id
            result = await self.executor.execute_task(
                {
                    "id": task.agent_id,
                    "prompt": task.task_prompt,
                    "agent_type": task.agent_type,
                    "worktree": task.worktree_path,
                    "token_index": task.token_index,
                    "mcp_profile": task.mcp_profile,
                    "allowed_tools": task.allowed_tools,
                    "permission_mode": task.permission_mode,
                    "run_id": state.get("run_id"),  # Pass run_id for patch export
                    "sequence": getattr(task, "sequence", 0),
                }
            )

            # Extract patch manifest if present
            patch_manifest = result.get("patch_manifest")

            # Return mergeable partial update with patch manifest
            update = {
                "results": {
                    task.agent_id: {
                        "type": task.agent_type,
                        "status": "completed",
                        "result": result,
                    }
                }
            }

            if patch_manifest:
                update["patch_manifests"] = [patch_manifest]

            return update

        except asyncio.TimeoutError:
            logger.error(f"{task.agent_id} timed out")
            return {"errors": [f"{task.agent_id}: Agent execution timed out"]}

        except Exception as e:
            logger.exception(f"Agent {task.agent_id} failed: {e}")
            return {"errors": [f"{task.agent_id}: {e}"]}

    def _aggregate_results(self, state: OrchestrationState) -> Dict[str, Any]:
        """
        Aggregate results from all parallel agents and merge patches if enabled.
        """
        logger.info("Aggregating results from parallel agents")

        # Get merged results and errors from state
        merged = state.get("results", {}) or {}
        errors = state.get("errors", []) or []
        agent_tasks = state.get("agent_tasks", []) or []
        patch_manifests = state.get("patch_manifests", []) or []
        run_id = state.get("run_id")

        metrics = {"total": len(agent_tasks), "completed": 0, "failed": 0}

        for task in agent_tasks:
            agent_result = merged.get(task.agent_id, {})
            if agent_result.get("status") == "completed":
                metrics["completed"] += 1
            else:
                metrics["failed"] += 1

            # End performance tracking
            if self.performance_monitor:
                self.performance_monitor.end_tracking(
                    task.agent_id, success=(agent_result.get("status") == "completed")
                )

        # Calculate performance stats
        if self.performance_monitor:
            perf_stats = self.performance_monitor.calculate_statistics()
            metrics.update(perf_stats)

        # Execute merge-back if enabled and patches exist
        merge_report = None
        if (
            self.merger
            and self.merge_config
            and self.merge_config.enabled
            and patch_manifests
            and run_id
        ):
            logger.info(f"Executing merge-back for {len(patch_manifests)} patches")

            try:
                # Prepare staging worktree
                staging_path = self.merger.prepare_staging(run_id, self.merge_config.target_branch)

                # Order patches deterministically
                ordered_patches = self.merger.order_patches(patch_manifests)

                # Apply patches to staging
                applied, conflicts = self.merger.apply_patches(staging_path, ordered_patches)

                merge_report = {
                    "patches_applied": len(applied),
                    "conflicts": len(conflicts),
                    "conflict_details": conflicts,
                }

                if conflicts:
                    # Generate Fix-It tasks if conflicts exist
                    from ..orchestration.tasks import create_fixit_tasks

                    fixit_tasks = create_fixit_tasks(conflicts, run_id=run_id)
                    merge_report["fixit_tasks"] = fixit_tasks
                    logger.warning(f"Generated {len(fixit_tasks)} Fix-It tasks for conflicts")

                    # Emit conflict reports
                    self.merger.emit_reports(run_id, applied, conflicts, None, agent_tasks)
                else:
                    # Run quality gates
                    gates_report = self.merger.run_gates(staging_path)

                    if gates_report.success:
                        # Create PR or land directly
                        if not self.merge_config.dry_run:
                            pr_info = self.merger.create_pr_or_land(
                                staging_path, run_id, applied, agent_tasks
                            )
                            merge_report["pr_info"] = pr_info
                            logger.info(f"Merge-back successful: {pr_info}")
                    else:
                        merge_report["gate_failures"] = gates_report.failed_gates
                        logger.warning(f"Quality gates failed: {gates_report.failed_gates}")

                        # Generate Fix-It tasks for gate failures
                        from ..orchestration.tasks import create_fixit_tasks

                        fixit_tasks = create_fixit_tasks([], gates_report, run_id)
                        merge_report["fixit_tasks"] = fixit_tasks

                    # Emit reports
                    self.merger.emit_reports(run_id, applied, conflicts, gates_report, agent_tasks)

            except Exception as e:
                logger.error(f"Merge-back failed: {e}")
                merge_report = {"error": str(e)}
                errors.append(f"Merge-back failed: {e}")

        # Cleanup worktrees (unless keeping for debugging)
        if not (self.merge_config and self.merge_config.keep_worktrees):
            for task in agent_tasks:
                try:
                    self.worktree_manager.cleanup(task.agent_id, force=True)
                except Exception as e:
                    logger.warning(f"Worktree cleanup failed for {task.agent_id}: {e}")

        logger.info(f"Completed: {metrics['completed']}/{metrics['total']} agents succeeded")

        return_data = {
            "results": merged,
            "performance_metrics": metrics,
            "errors": errors,
            "phase": "completed",
        }

        if merge_report:
            return_data["merge_report"] = merge_report

        return return_data

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

        # Generate run_id for this execution
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        logger.info(f"Starting orchestration with run_id: {run_id}")

        # Initialize state as dict
        initial_state = {
            "main_task": task,
            "num_agents": max_agents,
            "max_parallel": self.max_parallel,
            "agent_tasks": [],
            "results": {},
            "errors": [],
            "patch_manifests": [],
            "phase": "initialized",
            "run_id": run_id,
        }

        try:
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "results": final_state.get("results", {}),
                "metrics": final_state.get("performance_metrics", {}),
                "errors": final_state.get("errors", []),
                "phase": final_state.get("phase", "unknown"),
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                "results": {},
                "metrics": {"error": str(e)},
                "errors": [str(e)],
                "phase": "failed",
            }
