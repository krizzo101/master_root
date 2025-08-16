"""
Recursive Orchestration Patterns
---------------------------------
Patterns for recursive agent spawning with depth control and parallelism.
Combines V1 recursion management with LangGraph Send API.

Key features:
- Depth tracking and limits
- Parent-child relationships
- Fork bomb prevention
- Parallel child spawning at each level
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import hashlib

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


@dataclass
class RecursionConfig:
    """Configuration for recursive orchestration."""
    max_depth: int = 5
    max_concurrent_at_depth: Dict[int, int] = field(default_factory=lambda: {
        0: 1,    # Root level
        1: 10,   # First level children
        2: 50,   # Second level
        3: 100,  # Third level
        4: 200,  # Fourth level
        5: 400   # Fifth level
    })
    max_total_jobs: int = 1000
    max_children_per_parent: int = 20
    enable_checkpointing: bool = True
    timeout_multiplier: float = 0.8  # Reduce timeout at each depth


@dataclass
class RecursionContext:
    """Context for a recursive execution."""
    job_id: str
    parent_job_id: Optional[str]
    root_job_id: str
    depth: int
    call_stack: List[str]
    recursion_path: List[str]
    start_time: datetime
    children_spawned: int = 0
    
    def can_spawn_children(self, config: RecursionConfig, num_children: int) -> bool:
        """Check if this job can spawn children."""
        # Check depth limit
        if self.depth >= config.max_depth:
            logger.warning(f"Depth limit reached: {self.depth}/{config.max_depth}")
            return False
        
        # Check children per parent limit
        if self.children_spawned + num_children > config.max_children_per_parent:
            logger.warning(f"Children limit reached: {self.children_spawned + num_children}/{config.max_children_per_parent}")
            return False
        
        return True
    
    def create_child_context(self, child_id: str, task_signature: str) -> 'RecursionContext':
        """Create context for a child job."""
        return RecursionContext(
            job_id=child_id,
            parent_job_id=self.job_id,
            root_job_id=self.root_job_id,
            depth=self.depth + 1,
            call_stack=self.call_stack + [self.job_id],
            recursion_path=self.recursion_path + [task_signature],
            start_time=datetime.now(),
            children_spawned=0
        )


class RecursionLimiter:
    """
    Manages recursion limits and prevents fork bombs.
    Based on V1 RecursionManager patterns.
    """
    
    def __init__(self, config: Optional[RecursionConfig] = None):
        """Initialize with configuration."""
        self.config = config or RecursionConfig()
        self.active_contexts: Dict[str, RecursionContext] = {}
        self.depth_counts: Dict[int, int] = {}
        self.root_job_counts: Dict[str, int] = {}
        
    def validate_spawn(
        self,
        parent_context: Optional[RecursionContext],
        num_children: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if spawning is allowed.
        
        Args:
            parent_context: Parent's recursion context (None for root)
            num_children: Number of children to spawn
            
        Returns:
            Tuple of (allowed, error_message)
        """
        # Determine depth
        depth = parent_context.depth + 1 if parent_context else 0
        
        # Check depth limit
        if depth >= self.config.max_depth:
            return False, f"Depth limit exceeded: {depth}/{self.config.max_depth}"
        
        # Check concurrent at depth
        current_at_depth = self.depth_counts.get(depth, 0)
        max_at_depth = self.config.max_concurrent_at_depth.get(depth, 10)
        
        if current_at_depth + num_children > max_at_depth:
            return False, f"Concurrent limit at depth {depth}: {current_at_depth + num_children}/{max_at_depth}"
        
        # Check total jobs
        if parent_context:
            root_count = self.root_job_counts.get(parent_context.root_job_id, 0)
            if root_count + num_children > self.config.max_total_jobs:
                return False, f"Total job limit: {root_count + num_children}/{self.config.max_total_jobs}"
        
        # Check parent's children limit
        if parent_context and not parent_context.can_spawn_children(self.config, num_children):
            return False, f"Parent children limit exceeded"
        
        return True, None
    
    def register_spawn(
        self,
        parent_context: Optional[RecursionContext],
        child_contexts: List[RecursionContext]
    ):
        """Register spawned children."""
        for context in child_contexts:
            # Update counts
            self.active_contexts[context.job_id] = context
            self.depth_counts[context.depth] = self.depth_counts.get(context.depth, 0) + 1
            self.root_job_counts[context.root_job_id] = self.root_job_counts.get(context.root_job_id, 0) + 1
        
        # Update parent's children count
        if parent_context:
            parent_context.children_spawned += len(child_contexts)
        
        logger.info(f"Registered {len(child_contexts)} children at depth {child_contexts[0].depth if child_contexts else 0}")
    
    def unregister_job(self, job_id: str):
        """Unregister completed job."""
        context = self.active_contexts.get(job_id)
        if not context:
            return
        
        # Update counts
        self.depth_counts[context.depth] -= 1
        self.root_job_counts[context.root_job_id] -= 1
        
        # Remove context
        del self.active_contexts[job_id]
        
        logger.debug(f"Unregistered job {job_id} at depth {context.depth}")


class DepthTracker:
    """
    Tracks execution depth and provides depth-aware configuration.
    """
    
    @staticmethod
    def get_timeout_for_depth(base_timeout: int, depth: int, multiplier: float = 0.8) -> int:
        """Calculate timeout based on depth."""
        timeout = int(base_timeout * (multiplier ** depth))
        return max(timeout, 5000)  # Minimum 5 seconds
    
    @staticmethod
    def get_batch_size_for_depth(base_batch: int, depth: int) -> int:
        """Calculate batch size based on depth."""
        # Reduce batch size at deeper levels
        batch_sizes = {
            0: base_batch,
            1: base_batch,
            2: max(base_batch // 2, 5),
            3: max(base_batch // 4, 3),
            4: max(base_batch // 8, 2),
            5: 1
        }
        return batch_sizes.get(depth, 1)
    
    @staticmethod
    def create_task_signature(task: str) -> str:
        """Create unique signature for task (for cycle detection)."""
        normalized = task.lower().strip()[:100]
        return hashlib.md5(normalized.encode()).hexdigest()[:8]


class RecursiveOrchestrationPattern:
    """
    Implements recursive orchestration with LangGraph and Send API.
    Combines V1 recursion patterns with parallel execution.
    """
    
    def __init__(
        self,
        config: Optional[RecursionConfig] = None,
        limiter: Optional[RecursionLimiter] = None
    ):
        """Initialize with configuration and limiter."""
        self.config = config or RecursionConfig()
        self.limiter = limiter or RecursionLimiter(self.config)
        
    def create_recursive_sends(
        self,
        node: str,
        tasks: List[Dict[str, Any]],
        parent_context: Optional[RecursionContext]
    ) -> Tuple[List[Send], List[RecursionContext]]:
        """
        Create Send objects for recursive parallel execution.
        
        Args:
            node: Target node for children
            tasks: Tasks to spawn as children
            parent_context: Parent's recursion context
            
        Returns:
            Tuple of (Send objects, child contexts)
        """
        # Validate spawn
        allowed, error = self.limiter.validate_spawn(parent_context, len(tasks))
        if not allowed:
            logger.error(f"Spawn validation failed: {error}")
            return [], []
        
        sends = []
        contexts = []
        
        for i, task in enumerate(tasks):
            # Create child context
            child_id = f"{parent_context.job_id if parent_context else 'root'}_{i}_{datetime.now().timestamp()}"
            task_sig = DepthTracker.create_task_signature(str(task))
            
            if parent_context:
                child_context = parent_context.create_child_context(child_id, task_sig)
            else:
                # Root context
                child_context = RecursionContext(
                    job_id=child_id,
                    parent_job_id=None,
                    root_job_id=child_id,
                    depth=0,
                    call_stack=[],
                    recursion_path=[task_sig],
                    start_time=datetime.now()
                )
            
            # Create Send with recursion context
            send_state = {
                "task": task,
                "recursion_context": {
                    "job_id": child_context.job_id,
                    "parent_id": child_context.parent_job_id,
                    "root_id": child_context.root_job_id,
                    "depth": child_context.depth,
                    "call_stack": child_context.call_stack
                },
                "timeout_ms": DepthTracker.get_timeout_for_depth(
                    30000,  # Base timeout
                    child_context.depth,
                    self.config.timeout_multiplier
                )
            }
            
            sends.append(Send(node, send_state))
            contexts.append(child_context)
        
        # Register spawn
        self.limiter.register_spawn(parent_context, contexts)
        
        logger.info(f"Created {len(sends)} recursive sends at depth {contexts[0].depth if contexts else 0}")
        return sends, contexts


class RecursiveGraphBuilder:
    """
    Builds LangGraph StateGraphs with recursive execution support.
    """
    
    def __init__(
        self,
        state_type: type,
        config: Optional[RecursionConfig] = None
    ):
        """Initialize builder."""
        self.state_type = state_type
        self.config = config or RecursionConfig()
        self.pattern = RecursiveOrchestrationPattern(config)
        
    def build_recursive_graph(
        self,
        root_node: Callable,
        child_node: Callable,
        aggregator_node: Callable,
        decomposer: Optional[Callable] = None
    ) -> StateGraph:
        """
        Build a StateGraph with recursive parallel execution.
        
        Pattern:
        1. Root decomposes task
        2. Spawns parallel children via Send
        3. Children can spawn grandchildren
        4. Results aggregate up the tree
        
        Args:
            root_node: Root execution function
            child_node: Child execution function (can spawn more children)
            aggregator_node: Result aggregation function
            decomposer: Optional task decomposition function
            
        Returns:
            Configured recursive StateGraph
        """
        workflow = StateGraph(self.state_type)
        
        # Add nodes
        workflow.add_node("root", root_node)
        workflow.add_node("child", child_node)
        workflow.add_node("aggregator", aggregator_node)
        
        # Entry point
        workflow.add_edge(START, "root")
        
        # Root spawns children
        def root_spawn_routing(state):
            # Decompose task
            if decomposer:
                subtasks = decomposer(state.get("task"))
            else:
                subtasks = state.get("subtasks", [])
            
            if not subtasks:
                # No decomposition, go directly to aggregator
                return []
            
            # Create recursive sends
            parent_context = state.get("recursion_context")
            sends, _ = self.pattern.create_recursive_sends(
                "child",
                subtasks,
                parent_context
            )
            
            return sends
        
        workflow.add_conditional_edges("root", root_spawn_routing)
        
        # Children can spawn grandchildren
        def child_spawn_routing(state):
            # Check if further decomposition needed
            context = state.get("recursion_context", {})
            depth = context.get("depth", 0)
            
            if depth >= self.config.max_depth - 1:
                # At max depth, don't spawn more
                return []
            
            # Optional: decompose and spawn grandchildren
            if decomposer:
                subtasks = decomposer(state.get("task"))
                if subtasks and len(subtasks) > 1:
                    # Create recursive sends for grandchildren
                    parent_context = RecursionContext(
                        job_id=context.get("job_id"),
                        parent_job_id=context.get("parent_id"),
                        root_job_id=context.get("root_id"),
                        depth=depth,
                        call_stack=context.get("call_stack", []),
                        recursion_path=[],
                        start_time=datetime.now()
                    )
                    
                    sends, _ = self.pattern.create_recursive_sends(
                        "child",  # Grandchildren are also "child" nodes
                        subtasks,
                        parent_context
                    )
                    
                    return sends
            
            return []
        
        workflow.add_conditional_edges("child", child_spawn_routing)
        
        # All paths lead to aggregator
        workflow.add_edge("root", "aggregator")
        workflow.add_edge("child", "aggregator")
        
        # Aggregator to END
        workflow.add_edge("aggregator", END)
        
        logger.info(f"Built recursive graph with max depth {self.config.max_depth}")
        return workflow