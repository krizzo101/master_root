"""
Recursive Executor
------------------
Executes tasks recursively with parallel child spawning.
Designed for Claude Code V1 integration.

Implements true recursive parallelism:
- Each level can spawn multiple children
- Children can spawn grandchildren
- Depth and resource limits enforced
"""

from typing import Any, Callable, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
import os

from pydantic import ConfigDict
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from ..patterns.recursive_orch import (
    RecursiveOrchestrationPattern,
    RecursionConfig,
    RecursionContext,
    RecursionLimiter,
    RecursiveGraphBuilder,
    DepthTracker
)
from ..patterns.send_api import ParallelSendExecutor
from .parallel_executor import ExecutionResult

logger = logging.getLogger(__name__)


class RecursiveJobState(TypedDict):
    """State for recursive job execution."""
    __pydantic_config__ = ConfigDict(strict=True)
    
    task: str
    job_id: str
    parent_job_id: Optional[str]
    recursion_context: Dict[str, Any]
    depth: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    children_spawned: List[str]
    status: str


@dataclass
class RecursiveExecutionResult:
    """Result of recursive execution."""
    job_id: str
    success: bool
    depth: int
    children_spawned: int
    total_descendants: int
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    execution_time_ms: float
    tree_structure: Dict[str, Any] = field(default_factory=dict)


class RecursiveExecutor:
    """
    Generic recursive executor with parallel child spawning.
    """
    
    def __init__(
        self,
        config: Optional[RecursionConfig] = None,
        checkpointer: Optional[Any] = None
    ):
        """
        Initialize recursive executor.
        
        Args:
            config: Recursion configuration
            checkpointer: Optional LangGraph checkpointer
        """
        self.config = config or RecursionConfig()
        self.limiter = RecursionLimiter(self.config)
        self.pattern = RecursiveOrchestrationPattern(self.config, self.limiter)
        self.checkpointer = checkpointer or InMemorySaver()
        self.graph_builder = RecursiveGraphBuilder(RecursiveJobState, self.config)
        
        # Track execution tree
        self.execution_tree: Dict[str, List[str]] = {}
        
    async def execute_recursive(
        self,
        task: str,
        parent_id: Optional[str] = None,
        decomposer: Optional[Callable] = None,
        executor: Optional[Callable] = None,
        aggregator: Optional[Callable] = None,
        debug: bool = False
    ) -> RecursiveExecutionResult:
        """
        Execute task recursively with parallel child spawning.
        
        Args:
            task: Root task to execute
            parent_id: Optional parent job ID
            decomposer: Function to decompose tasks
            executor: Function to execute tasks
            aggregator: Function to aggregate results
            debug: Enable debug logging
            
        Returns:
            RecursiveExecutionResult
        """
        start_time = datetime.now()
        job_id = f"job_{uuid.uuid4().hex[:8]}_{start_time.timestamp()}"
        
        if debug:
            logger.info(f"Starting recursive execution: {job_id}")
        
        # Get parent context if exists
        parent_context = None
        if parent_id:
            parent_context = self._get_context(parent_id)
        
        # Validate spawn
        allowed, error = self.limiter.validate_spawn(parent_context, 1)
        if not allowed:
            logger.error(f"Spawn validation failed: {error}")
            return RecursiveExecutionResult(
                job_id=job_id,
                success=False,
                depth=parent_context.depth + 1 if parent_context else 0,
                children_spawned=0,
                total_descendants=0,
                results={},
                errors=[{"error": error}],
                execution_time_ms=0
            )
        
        # Build execution graph
        graph = self._build_recursive_graph(
            decomposer or self._default_decomposer,
            executor or self._default_executor,
            aggregator or self._default_aggregator
        )
        
        # Prepare initial state
        initial_state: RecursiveJobState = {
            "task": task,
            "job_id": job_id,
            "parent_job_id": parent_id,
            "recursion_context": {
                "job_id": job_id,
                "parent_id": parent_id,
                "depth": parent_context.depth + 1 if parent_context else 0,
                "root_id": parent_context.root_job_id if parent_context else job_id
            },
            "depth": parent_context.depth + 1 if parent_context else 0,
            "results": [],
            "errors": [],
            "children_spawned": [],
            "status": "starting"
        }
        
        try:
            # Execute through LangGraph
            final_state = await graph.ainvoke(initial_state)
            
            # Calculate metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Build result
            result = RecursiveExecutionResult(
                job_id=job_id,
                success=len(final_state.get("errors", [])) == 0,
                depth=final_state.get("depth", 0),
                children_spawned=len(final_state.get("children_spawned", [])),
                total_descendants=self._count_descendants(job_id),
                results=final_state.get("results", {}),
                errors=final_state.get("errors", []),
                execution_time_ms=execution_time,
                tree_structure=self._build_tree_structure(job_id)
            )
            
            if debug:
                logger.info(f"Recursive execution completed: {job_id}")
                logger.info(f"Children spawned: {result.children_spawned}, Total descendants: {result.total_descendants}")
            
            return result
            
        except Exception as e:
            logger.error(f"Recursive execution failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return RecursiveExecutionResult(
                job_id=job_id,
                success=False,
                depth=initial_state["depth"],
                children_spawned=0,
                total_descendants=0,
                results={},
                errors=[{"error": str(e), "type": "execution_failure"}],
                execution_time_ms=execution_time
            )
    
    def _build_recursive_graph(
        self,
        decomposer: Callable,
        executor: Callable,
        aggregator: Callable
    ) -> StateGraph:
        """Build recursive execution graph."""
        
        def root_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Root node execution."""
            state["status"] = "executing_root"
            
            # Execute root task
            try:
                result = executor(state.get("task"))
                state["root_result"] = result
            except Exception as e:
                state["errors"].append({"node": "root", "error": str(e)})
            
            return state
        
        def child_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Child node execution."""
            context = state.get("recursion_context", {})
            depth = context.get("depth", 0)
            
            state["status"] = f"executing_child_depth_{depth}"
            
            # Execute child task
            try:
                result = executor(state.get("task"))
                state["child_result"] = result
            except Exception as e:
                state["errors"].append({
                    "node": "child",
                    "depth": depth,
                    "error": str(e)
                })
            
            return state
        
        def aggregator_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Aggregate results from all levels."""
            state["status"] = "aggregating"
            
            # Aggregate results
            aggregated = aggregator(state)
            state["results"] = aggregated
            state["status"] = "completed"
            
            return state
        
        # Build graph with recursive pattern
        graph = self.graph_builder.build_recursive_graph(
            root_node=root_node,
            child_node=child_node,
            aggregator_node=aggregator_node,
            decomposer=decomposer
        )
        
        return graph.compile(checkpointer=self.checkpointer)
    
    def _default_decomposer(self, task: Any) -> List[Dict[str, Any]]:
        """
        Default task decomposition with intelligent analysis.
        Returns subtasks if the task appears complex enough to benefit from decomposition.
        """
        if not task:
            return []
            
        task_str = str(task) if not isinstance(task, str) else task
        task_lower = task_str.lower()
        
        # Keywords that suggest decomposition
        complexity_indicators = ['complex', 'multiple', 'comprehensive', 'complete', 'full', 'entire', 'all']
        action_words = ['create', 'build', 'implement', 'develop', 'design', 'analyze']
        
        # Check if decomposition is beneficial
        should_decompose = (
            any(indicator in task_lower for indicator in complexity_indicators) or
            len(task_str) > 150 or
            task_lower.count(' and ') >= 2
        )
        
        if not should_decompose:
            return []
        
        # Intelligent decomposition based on task type
        subtasks = []
        if any(word in task_lower for word in ['api', 'service', 'server']):
            subtasks = [
                {"subtask": f"Design API structure for: {task_str[:50]}...", "phase": "design"},
                {"subtask": f"Implement core endpoints for: {task_str[:50]}...", "phase": "implement"},
                {"subtask": f"Add validation and error handling for: {task_str[:50]}...", "phase": "enhance"},
                {"subtask": f"Create tests for: {task_str[:50]}...", "phase": "test"}
            ]
        elif any(word in task_lower for word in ['analyze', 'review', 'audit']):
            subtasks = [
                {"subtask": f"Gather data for: {task_str[:50]}...", "phase": "gather"},
                {"subtask": f"Analyze patterns in: {task_str[:50]}...", "phase": "analyze"},
                {"subtask": f"Generate insights for: {task_str[:50]}...", "phase": "synthesize"}
            ]
        else:
            # Generic decomposition
            subtasks = [
                {"subtask": f"Plan approach for: {task_str[:50]}...", "phase": "plan"},
                {"subtask": f"Execute main task: {task_str[:50]}...", "phase": "execute"},
                {"subtask": f"Validate results of: {task_str[:50]}...", "phase": "validate"}
            ]
        
        return subtasks
    
    def _default_executor(self, task: Any) -> Dict[str, Any]:
        """
        Default executor that provides meaningful execution simulation.
        Can be used for testing orchestration patterns without external dependencies.
        """
        import hashlib
        import random
        
        task_str = str(task)
        task_id = hashlib.md5(task_str.encode()).hexdigest()[:8]
        
        # Simulate varying execution times
        base_time = len(task_str) * 5  # 5ms per character
        variance = random.uniform(0.8, 1.2)
        execution_time_ms = min(base_time * variance, 5000)  # Cap at 5 seconds
        
        # Simulate occasional failures (5% chance)
        success = random.random() > 0.05
        
        result = {
            "task_id": task_id,
            "executed": task,
            "status": "completed" if success else "failed",
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            result["output"] = {
                "message": f"Task {task_id} completed successfully",
                "metrics": {
                    "complexity": len(task_str),
                    "processing_time": execution_time_ms
                }
            }
        else:
            result["error"] = f"Simulated failure for task {task_id}"
        
        return result
    
    def _default_aggregator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default aggregator that intelligently combines results from parallel/recursive execution.
        Provides useful summary statistics and maintains result hierarchy.
        """
        root_result = state.get("root_result", {})
        child_results = state.get("child_results", [])
        
        # Calculate aggregate metrics
        total_time = root_result.get("execution_time_ms", 0)
        successful_tasks = 1 if root_result.get("status") == "completed" else 0
        failed_tasks = 1 if root_result.get("status") == "failed" else 0
        
        for child in child_results:
            if isinstance(child, dict):
                total_time += child.get("execution_time_ms", 0)
                if child.get("status") == "completed":
                    successful_tasks += 1
                elif child.get("status") == "failed":
                    failed_tasks += 1
        
        total_tasks = successful_tasks + failed_tasks
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "root_result": root_result,
            "child_results": child_results,
            "aggregation": {
                "total_tasks": total_tasks,
                "successful": successful_tasks,
                "failed": failed_tasks,
                "success_rate": f"{success_rate:.1f}%",
                "total_execution_time_ms": total_time,
                "average_time_ms": total_time / total_tasks if total_tasks > 0 else 0
            },
            "status": "completed" if failed_tasks == 0 else "partial",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_context(self, job_id: str) -> Optional[RecursionContext]:
        """Get recursion context for a job."""
        return self.limiter.active_contexts.get(job_id)
    
    def _count_descendants(self, job_id: str) -> int:
        """Count all descendants of a job."""
        count = 0
        children = self.execution_tree.get(job_id, [])
        count += len(children)
        
        for child in children:
            count += self._count_descendants(child)
        
        return count
    
    def _build_tree_structure(self, job_id: str) -> Dict[str, Any]:
        """Build tree structure for visualization."""
        children = self.execution_tree.get(job_id, [])
        
        return {
            "job_id": job_id,
            "children": [
                self._build_tree_structure(child) for child in children
            ]
        }


class RecursiveClaudeExecutor(RecursiveExecutor):
    """
    Recursive executor specialized for Claude Code integration.
    """
    
    def __init__(
        self,
        claude_command: str = "claude",
        config: Optional[RecursionConfig] = None
    ):
        """
        Initialize Claude-specific recursive executor.
        
        Args:
            claude_command: Claude CLI command
            config: Recursion configuration
        """
        super().__init__(config)
        self.claude_command = claude_command
        
    async def execute_claude_recursive(
        self,
        task: str,
        parent_job_id: Optional[str] = None,
        cwd: Optional[str] = None,
        output_format: str = "json"
    ) -> RecursiveExecutionResult:
        """
        Execute Claude task recursively.
        
        Args:
            task: Task description
            parent_job_id: Parent job ID
            cwd: Working directory
            output_format: Output format
            
        Returns:
            RecursiveExecutionResult
        """
        
        def claude_decomposer(task_str: str) -> List[Dict[str, Any]]:
            """Decompose task for Claude execution based on task complexity."""
            task_lower = task_str.lower()
            subtasks = []
            
            # Intelligent task decomposition based on keywords and complexity
            if any(word in task_lower for word in ["build", "create", "implement", "develop"]):
                subtasks.extend([
                    {"task": f"Design architecture for: {task_str[:100]}", "priority": 1},
                    {"task": f"Implement core functionality: {task_str[:100]}", "priority": 2},
                    {"task": f"Add error handling and validation: {task_str[:100]}", "priority": 3},
                    {"task": f"Write tests for: {task_str[:100]}", "priority": 4},
                    {"task": f"Document implementation: {task_str[:100]}", "priority": 5}
                ])
            elif any(word in task_lower for word in ["analyze", "review", "audit", "examine"]):
                subtasks.extend([
                    {"task": f"Gather and validate data for: {task_str[:100]}", "priority": 1},
                    {"task": f"Perform detailed analysis: {task_str[:100]}", "priority": 2},
                    {"task": f"Identify patterns and insights: {task_str[:100]}", "priority": 3},
                    {"task": f"Generate recommendations: {task_str[:100]}", "priority": 4}
                ])
            elif any(word in task_lower for word in ["fix", "debug", "repair", "resolve"]):
                subtasks.extend([
                    {"task": f"Reproduce and isolate issue: {task_str[:100]}", "priority": 1},
                    {"task": f"Identify root cause: {task_str[:100]}", "priority": 2},
                    {"task": f"Implement fix: {task_str[:100]}", "priority": 3},
                    {"task": f"Verify solution: {task_str[:100]}", "priority": 4}
                ])
            elif len(task_str) > 200 or task_lower.count(" and ") >= 2:
                # Complex task based on length or multiple conjunctions
                subtasks.extend([
                    {"task": f"Break down requirements: {task_str[:100]}", "priority": 1},
                    {"task": f"Execute primary objective: {task_str[:100]}", "priority": 2},
                    {"task": f"Handle secondary objectives: {task_str[:100]}", "priority": 3},
                    {"task": f"Integrate and validate results: {task_str[:100]}", "priority": 4}
                ])
            
            return subtasks
        
        async def claude_executor(task_data: Any) -> Dict[str, Any]:
            """Execute task via Claude CLI with actual subprocess spawning."""
            import subprocess
            import json as json_module
            
            task_str = str(task_data) if not isinstance(task_data, str) else task_data
            
            # Prepare Claude command
            cmd = [
                self.claude_command,
                "--output-format", output_format,
                "--dangerously-skip-permissions",
                "-p", task_str
            ]
            
            # Add MCP config if available
            if cwd:
                mcp_config_path = os.path.join(cwd, ".mcp.json")
                if os.path.exists(mcp_config_path):
                    cmd.extend(["--mcp-config", mcp_config_path])
            
            # Prepare environment
            env = os.environ.copy()
            if "CLAUDE_CODE_TOKEN" in env:
                # Ensure we use token auth
                env.pop("ANTHROPIC_API_KEY", None)
            
            try:
                # Execute Claude process
                process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=60)
                
                result = {
                    "command": " ".join(cmd),
                    "task": task_str,
                    "cwd": cwd,
                    "output_format": output_format,
                    "success": process.returncode == 0,
                    "return_code": process.returncode,
                    "executed_at": datetime.now().isoformat()
                }
                
                if output_format == "json" and stdout:
                    try:
                        result["output"] = json_module.loads(stdout)
                    except json_module.JSONDecodeError:
                        result["output"] = stdout
                else:
                    result["output"] = stdout
                    
                if stderr:
                    result["stderr"] = stderr
                    
                return result
                
            except subprocess.TimeoutExpired:
                return {
                    "command": " ".join(cmd),
                    "task": task_str,
                    "success": False,
                    "error": "Process timed out after 60 seconds",
                    "executed_at": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "command": " ".join(cmd),
                    "task": task_str,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "executed_at": datetime.now().isoformat()
                }
        
        def claude_aggregator(state: Dict[str, Any]) -> Dict[str, Any]:
            """Aggregate Claude results with intelligent merging."""
            main_result = state.get("root_result", {})
            subtask_results = state.get("child_results", [])
            
            # Extract successful outputs
            successful_outputs = []
            failed_tasks = []
            
            if main_result.get("success"):
                successful_outputs.append(main_result.get("output", ""))
            else:
                failed_tasks.append(main_result)
            
            for result in subtask_results:
                if isinstance(result, dict) and result.get("success"):
                    successful_outputs.append(result.get("output", ""))
                else:
                    failed_tasks.append(result)
            
            # Combine outputs intelligently
            combined_output = "\n\n---\n\n".join(filter(None, successful_outputs))
            
            return {
                "main_result": main_result,
                "subtask_results": subtask_results,
                "combined_output": combined_output,
                "summary": {
                    "total_tasks": 1 + len(subtask_results),
                    "successful": len(successful_outputs),
                    "failed": len(failed_tasks),
                    "success_rate": len(successful_outputs) / (1 + len(subtask_results)) * 100
                },
                "failed_tasks": failed_tasks
            }
        
        return await self.execute_recursive(
            task=task,
            parent_id=parent_job_id,
            decomposer=claude_decomposer,
            executor=claude_executor,
            aggregator=claude_aggregator,
            debug=True
        )