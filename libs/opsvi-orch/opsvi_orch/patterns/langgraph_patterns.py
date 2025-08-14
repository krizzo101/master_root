"""
LangGraph Patterns
------------------
Core patterns extracted from OAMAT_SD execution_engine.py
Implements proven Send API patterns for parallel execution.

CRITICAL RULES (from OAMAT_SD):
- NEVER use asyncio.gather - use Send API
- State is DICT not TypedDict in nodes
- Separate node and routing functions
- 3-5x performance improvement documented
"""

from typing import Any, Callable, Dict, List, Optional, TypedDict
from dataclasses import dataclass
import logging

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


class ParallelOrchestrationPattern:
    """
    Implements parallel orchestration using LangGraph Send API.
    Extracted from OAMAT_SD execution_engine.py lines 150-250.
    
    Key features:
    - True parallel execution via Send objects
    - No asyncio.gather (forbidden pattern)
    - State dict handling (not TypedDict access)
    - Conditional edges with Send routing
    """
    
    @staticmethod
    def create_parallel_sends(
        target_node: str,
        tasks: List[Dict[str, Any]],
        state_key: str = "task_data"
    ) -> List[Send]:
        """
        Create Send objects for parallel execution.
        
        Args:
            target_node: Name of the node to send tasks to
            tasks: List of task dictionaries to execute in parallel
            state_key: Key to store task data in state
            
        Returns:
            List of Send objects that execute in parallel
        """
        sends = []
        for i, task in enumerate(tasks):
            send_state = {
                state_key: task,
                "task_index": i,
                "total_tasks": len(tasks),
                "parallel_batch": True
            }
            sends.append(Send(target_node, send_state))
        
        logger.debug(f"Created {len(sends)} Send objects for parallel execution")
        return sends
    
    @staticmethod
    def build_parallel_graph(
        state_type: type,
        coordinator_node: Callable,
        executor_node: Callable,
        aggregator_node: Callable,
        routing_function: Optional[Callable] = None
    ) -> StateGraph:
        """
        Build a StateGraph with parallel execution pattern.
        
        Pattern from OAMAT_SD:
        1. Coordinator prepares work
        2. Send API distributes to parallel executors
        3. Aggregator collects results
        
        Args:
            state_type: State TypedDict class
            coordinator_node: Function that prepares tasks
            executor_node: Function that executes single task
            aggregator_node: Function that aggregates results
            routing_function: Optional custom routing logic
            
        Returns:
            Configured StateGraph ready for compilation
        """
        workflow = StateGraph(state_type)
        
        # Add nodes
        workflow.add_node("coordinator", coordinator_node)
        workflow.add_node("executor", executor_node)
        workflow.add_node("aggregator", aggregator_node)
        
        # Entry point
        workflow.add_edge(START, "coordinator")
        
        # Parallel distribution via Send API
        if routing_function:
            workflow.add_conditional_edges(
                "coordinator",
                routing_function,  # Must return Send objects
            )
        else:
            # Default routing: coordinator -> parallel executors
            def default_routing(state):
                tasks = state.get("tasks", [])
                return ParallelOrchestrationPattern.create_parallel_sends(
                    "executor", 
                    tasks
                )
            
            workflow.add_conditional_edges(
                "coordinator",
                default_routing
            )
        
        # Executors -> Aggregator
        workflow.add_edge("executor", "aggregator")
        
        # Aggregator -> END
        workflow.add_edge("aggregator", END)
        
        logger.info("Built parallel orchestration graph")
        return workflow


class StateGraphBuilder:
    """
    Builder pattern for complex StateGraphs.
    Ensures compliance with OAMAT_SD patterns.
    """
    
    def __init__(self, state_type: type):
        """Initialize with state type."""
        self.state_type = state_type
        self.workflow = StateGraph(state_type)
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []
        
    def add_node(self, name: str, func: Callable) -> 'StateGraphBuilder':
        """Add a node to the graph."""
        self.workflow.add_node(name, func)
        self.nodes[name] = func
        return self
    
    def add_parallel_coordinator(
        self, 
        name: str,
        task_extractor: Callable,
        target_node: str
    ) -> 'StateGraphBuilder':
        """
        Add a coordinator node that spawns parallel tasks.
        
        Args:
            name: Coordinator node name
            task_extractor: Function to extract tasks from state
            target_node: Node to send tasks to
        """
        def coordinator_node(state):
            # CRITICAL: State is dict, not TypedDict
            tasks = task_extractor(state)
            state["prepared_tasks"] = tasks
            state["parallel_execution"] = True
            return state
        
        def send_routing(state):
            # Create Send objects for parallel execution
            tasks = state.get("prepared_tasks", [])
            return ParallelOrchestrationPattern.create_parallel_sends(
                target_node,
                tasks
            )
        
        self.workflow.add_node(name, coordinator_node)
        self.workflow.add_conditional_edges(name, send_routing)
        
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> 'StateGraphBuilder':
        """Add an edge between nodes."""
        self.workflow.add_edge(from_node, to_node)
        self.edges.append((from_node, to_node))
        return self
    
    def set_entry(self, node: str) -> 'StateGraphBuilder':
        """Set the entry point."""
        self.workflow.add_edge(START, node)
        return self
    
    def set_exit(self, node: str) -> 'StateGraphBuilder':
        """Set the exit point."""
        self.workflow.add_edge(node, END)
        return self
    
    def build(self) -> StateGraph:
        """Build and return the StateGraph."""
        logger.info(f"Built StateGraph with {len(self.nodes)} nodes, {len(self.edges)} edges")
        return self.workflow


class SendAPIPattern:
    """
    Encapsulates Send API best practices from OAMAT_SD.
    
    CRITICAL: This replaces asyncio.gather patterns.
    Rule 997: asyncio.gather is FORBIDDEN.
    """
    
    @staticmethod
    def validate_send_objects(sends: List[Send]) -> bool:
        """Validate Send objects before execution."""
        if not sends:
            logger.warning("No Send objects to validate")
            return False
        
        for send in sends:
            if not isinstance(send, Send):
                logger.error(f"Invalid Send object: {type(send)}")
                return False
        
        return True
    
    @staticmethod
    def create_batch_sends(
        node: str,
        items: List[Any],
        batch_size: int = 10,
        state_transformer: Optional[Callable] = None
    ) -> List[List[Send]]:
        """
        Create batches of Send objects for controlled parallelism.
        
        Args:
            node: Target node name
            items: Items to process
            batch_size: Max parallel executions
            state_transformer: Optional function to transform item to state
            
        Returns:
            List of Send batches
        """
        batches = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            sends = []
            
            for j, item in enumerate(batch):
                if state_transformer:
                    state = state_transformer(item)
                else:
                    state = {"item": item, "batch": i // batch_size, "index": j}
                
                sends.append(Send(node, state))
            
            batches.append(sends)
        
        logger.info(f"Created {len(batches)} batches with max {batch_size} parallel sends")
        return batches