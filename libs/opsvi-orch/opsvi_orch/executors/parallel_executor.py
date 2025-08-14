"""
Parallel Executor
-----------------
Generic parallel task execution using LangGraph Send API.
Extracted and generalized from OAMAT_SD subdivision_executor.py.

NO asyncio.gather - only Send API for parallelism.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from ..patterns.langgraph_patterns import ParallelOrchestrationPattern, StateGraphBuilder
from ..patterns.send_api import ParallelSendExecutor, BatchSendCoordinator

logger = logging.getLogger(__name__)


@dataclass
class ParallelExecutionConfig:
    """Configuration for parallel execution."""
    max_concurrent: int = 10
    timeout_ms: int = 30000
    enable_checkpointing: bool = True
    enable_metrics: bool = True
    batch_strategy: str = "balanced"  # balanced, aggressive, conservative
    aggregation_strategy: str = "collect_all"  # collect_all, first_complete, majority


@dataclass
class ExecutionResult:
    """Result of parallel execution."""
    success: bool
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    execution_time_ms: float
    tasks_completed: int
    tasks_failed: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class ParallelExecutor:
    """
    Generic parallel task executor using LangGraph Send API.
    
    Based on OAMAT_SD patterns for production reliability:
    - Send API for true parallelism (no asyncio.gather)
    - State dict handling
    - Checkpointing support
    - Metrics and monitoring
    """
    
    def __init__(
        self,
        config: Optional[ParallelExecutionConfig] = None,
        checkpointer: Optional[Any] = None
    ):
        """
        Initialize executor.
        
        Args:
            config: Execution configuration
            checkpointer: Optional LangGraph checkpointer
        """
        self.config = config or ParallelExecutionConfig()
        self.checkpointer = checkpointer or (
            InMemorySaver() if self.config.enable_checkpointing else None
        )
        self.send_executor = ParallelSendExecutor(
            max_concurrent=self.config.max_concurrent,
            timeout_ms=self.config.timeout_ms,
            enable_metrics=self.config.enable_metrics
        )
        self.coordinator = BatchSendCoordinator(self.send_executor)
        
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        task_executor: Callable,
        result_aggregator: Optional[Callable] = None,
        state_type: Optional[type] = None,
        debug: bool = False
    ) -> ExecutionResult:
        """
        Execute tasks in parallel using LangGraph Send API.
        
        Args:
            tasks: List of task dictionaries
            task_executor: Function to execute each task
            result_aggregator: Optional custom aggregator
            state_type: Optional state TypedDict
            debug: Enable debug logging
            
        Returns:
            ExecutionResult with aggregated results
        """
        start_time = datetime.now()
        
        if debug:
            logger.info(f"Starting parallel execution of {len(tasks)} tasks")
        
        try:
            # Build execution graph
            graph = self._build_execution_graph(
                task_executor,
                result_aggregator,
                state_type or dict
            )
            
            # Prepare initial state
            initial_state = {
                "tasks": tasks,
                "batch_strategy": self.config.batch_strategy,
                "max_concurrent": self.config.max_concurrent,
                "results": [],
                "errors": [],
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "total_tasks": len(tasks)
                }
            }
            
            # Execute through LangGraph
            final_state = await graph.ainvoke(initial_state)
            
            # Calculate metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Build result
            result = ExecutionResult(
                success=len(final_state.get("errors", [])) == 0,
                results=final_state.get("results", []),
                errors=final_state.get("errors", []),
                execution_time_ms=execution_time,
                tasks_completed=len(final_state.get("results", [])),
                tasks_failed=len(final_state.get("errors", [])),
                metadata=final_state.get("metadata", {})
            )
            
            if debug:
                logger.info(f"Parallel execution completed in {execution_time:.0f}ms")
                logger.info(f"Tasks completed: {result.tasks_completed}, failed: {result.tasks_failed}")
            
            return result
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                success=False,
                results=[],
                errors=[{"error": str(e), "type": "execution_failure"}],
                execution_time_ms=execution_time,
                tasks_completed=0,
                tasks_failed=len(tasks)
            )
    
    def _build_execution_graph(
        self,
        task_executor: Callable,
        result_aggregator: Optional[Callable],
        state_type: type
    ) -> StateGraph:
        """
        Build LangGraph for parallel execution.
        
        Pattern:
        1. Coordinator prepares tasks
        2. Send API distributes to parallel executors
        3. Aggregator collects results
        """
        builder = StateGraphBuilder(state_type)
        
        # Coordinator node
        def coordinator_node(state):
            """Prepare tasks for parallel execution."""
            tasks = state.get("tasks", [])
            
            # Apply batching strategy
            if self.config.batch_strategy == "aggressive":
                # All at once
                state["prepared_tasks"] = tasks
            elif self.config.batch_strategy == "conservative":
                # Small batches
                batch_size = min(5, self.config.max_concurrent)
                state["prepared_tasks"] = tasks[:batch_size]
                state["remaining_tasks"] = tasks[batch_size:]
            else:  # balanced
                state["prepared_tasks"] = tasks
            
            state["coordinator_complete"] = True
            return state
        
        # Executor node
        def executor_node(state):
            """Execute single task."""
            task = state.get("task_data")
            
            try:
                # Execute task
                result = task_executor(task)
                
                return {
                    "task_result": result,
                    "task_success": True,
                    "task_index": state.get("task_index"),
                    "execution_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                return {
                    "task_error": str(e),
                    "task_success": False,
                    "task_index": state.get("task_index")
                }
        
        # Aggregator node
        def aggregator_node(state):
            """Aggregate results from parallel execution."""
            if result_aggregator:
                # Custom aggregation
                aggregated = result_aggregator(state)
            else:
                # Default aggregation
                results = []
                errors = []
                
                # Collect from state updates
                if "task_result" in state:
                    results.append(state["task_result"])
                if "task_error" in state:
                    errors.append({
                        "index": state.get("task_index"),
                        "error": state["task_error"]
                    })
                
                # Merge with existing
                results.extend(state.get("results", []))
                errors.extend(state.get("errors", []))
                
                aggregated = {
                    "results": results,
                    "errors": errors,
                    "aggregation_complete": True
                }
            
            return aggregated
        
        # Build graph
        builder.add_node("coordinator", coordinator_node)
        builder.add_node("executor", executor_node)
        builder.add_node("aggregator", aggregator_node)
        
        # Add parallel coordinator pattern
        builder.add_parallel_coordinator(
            "coordinator",
            lambda state: [{"task_data": t} for t in state.get("prepared_tasks", [])],
            "executor"
        )
        
        # Set flow
        builder.set_entry("coordinator")
        builder.add_edge("executor", "aggregator")
        builder.set_exit("aggregator")
        
        # Compile with checkpointing
        graph = builder.build()
        if self.checkpointer:
            return graph.compile(checkpointer=self.checkpointer)
        else:
            return graph.compile()
    
    async def execute_with_retry(
        self,
        tasks: List[Dict[str, Any]],
        task_executor: Callable,
        max_retries: int = 3,
        backoff_ms: int = 1000
    ) -> ExecutionResult:
        """
        Execute with automatic retry on failure.
        
        Args:
            tasks: Tasks to execute
            task_executor: Execution function
            max_retries: Maximum retry attempts
            backoff_ms: Backoff between retries
            
        Returns:
            ExecutionResult
        """
        for attempt in range(max_retries):
            result = await self.execute_parallel_tasks(
                tasks,
                task_executor,
                debug=attempt > 0  # Debug on retries
            )
            
            if result.success or attempt == max_retries - 1:
                return result
            
            # Wait before retry
            import asyncio
            await asyncio.sleep(backoff_ms / 1000 * (2 ** attempt))
            
            logger.info(f"Retrying parallel execution (attempt {attempt + 2}/{max_retries})")
        
        return result