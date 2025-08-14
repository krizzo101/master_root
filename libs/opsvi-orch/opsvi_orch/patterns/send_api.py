"""
Send API Patterns
-----------------
Advanced Send API patterns for complex parallel orchestration.
Extracted from OAMAT_SD subdivision_executor.py.

Provides:
- Parallel task distribution
- Result aggregation
- Error handling in parallel execution
- Resource-aware batching
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio

from langgraph.constants import Send

logger = logging.getLogger(__name__)


@dataclass
class SendMetrics:
    """Metrics for Send execution."""
    total_sends: int = 0
    successful_sends: int = 0
    failed_sends: int = 0
    total_duration_ms: float = 0
    average_duration_ms: float = 0
    
    def update(self, success: bool, duration_ms: float):
        """Update metrics with execution result."""
        self.total_sends += 1
        if success:
            self.successful_sends += 1
        else:
            self.failed_sends += 1
        self.total_duration_ms += duration_ms
        self.average_duration_ms = self.total_duration_ms / self.total_sends


class SendBuilder:
    """
    Builder for complex Send objects with metadata and tracking.
    """
    
    def __init__(self, target_node: str):
        """Initialize with target node."""
        self.target_node = target_node
        self.state = {}
        self.metadata = {}
        
    def with_task(self, task: Any) -> 'SendBuilder':
        """Add task to state."""
        self.state["task"] = task
        return self
    
    def with_parent(self, parent_id: str, depth: int) -> 'SendBuilder':
        """Add parent tracking for recursive execution."""
        self.state["parent_id"] = parent_id
        self.state["depth"] = depth
        self.metadata["recursive"] = True
        return self
    
    def with_batch_info(self, batch_id: str, index: int, total: int) -> 'SendBuilder':
        """Add batch information."""
        self.state["batch_id"] = batch_id
        self.state["batch_index"] = index
        self.state["batch_total"] = total
        return self
    
    def with_timeout(self, timeout_ms: int) -> 'SendBuilder':
        """Add timeout constraint."""
        self.state["timeout_ms"] = timeout_ms
        self.metadata["has_timeout"] = True
        return self
    
    def with_retry_policy(self, max_retries: int, backoff_ms: int) -> 'SendBuilder':
        """Add retry policy."""
        self.state["max_retries"] = max_retries
        self.state["backoff_ms"] = backoff_ms
        self.metadata["retriable"] = True
        return self
    
    def with_custom(self, key: str, value: Any) -> 'SendBuilder':
        """Add custom state."""
        self.state[key] = value
        return self
    
    def build(self) -> Send:
        """Build the Send object."""
        # Add metadata to state
        self.state["_metadata"] = self.metadata
        self.state["_created_at"] = datetime.now().isoformat()
        
        return Send(self.target_node, self.state)


class ParallelSendExecutor:
    """
    Executes Send objects with resource management and monitoring.
    Based on OAMAT_SD subdivision_executor patterns.
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        timeout_ms: int = 30000,
        enable_metrics: bool = True
    ):
        """
        Initialize executor.
        
        Args:
            max_concurrent: Maximum concurrent Send executions
            timeout_ms: Default timeout for each Send
            enable_metrics: Track execution metrics
        """
        self.max_concurrent = max_concurrent
        self.timeout_ms = timeout_ms
        self.enable_metrics = enable_metrics
        self.metrics = SendMetrics() if enable_metrics else None
        
    def create_parallel_sends(
        self,
        node: str,
        tasks: List[Dict[str, Any]],
        batch_id: Optional[str] = None
    ) -> List[Send]:
        """
        Create Send objects for parallel execution with metadata.
        
        Args:
            node: Target node
            tasks: List of task dictionaries
            batch_id: Optional batch identifier
            
        Returns:
            List of Send objects ready for execution
        """
        sends = []
        batch_id = batch_id or f"batch_{datetime.now().timestamp()}"
        
        for i, task in enumerate(tasks):
            send = (SendBuilder(node)
                    .with_task(task)
                    .with_batch_info(batch_id, i, len(tasks))
                    .with_timeout(self.timeout_ms)
                    .build())
            sends.append(send)
        
        logger.info(f"Created {len(sends)} Send objects for batch {batch_id}")
        return sends
    
    def create_recursive_sends(
        self,
        node: str,
        tasks: List[Dict[str, Any]],
        parent_id: str,
        current_depth: int
    ) -> List[Send]:
        """
        Create Send objects for recursive parallel execution.
        
        Args:
            node: Target node
            tasks: List of task dictionaries
            parent_id: Parent job ID
            current_depth: Current recursion depth
            
        Returns:
            List of Send objects with parent tracking
        """
        sends = []
        
        for i, task in enumerate(tasks):
            send = (SendBuilder(node)
                    .with_task(task)
                    .with_parent(parent_id, current_depth + 1)
                    .with_batch_info(f"recursive_{parent_id}", i, len(tasks))
                    .with_timeout(self.timeout_ms)
                    .build())
            sends.append(send)
        
        logger.info(f"Created {len(sends)} recursive Send objects at depth {current_depth + 1}")
        return sends
    
    def batch_sends(
        self,
        sends: List[Send],
        batch_size: Optional[int] = None
    ) -> List[List[Send]]:
        """
        Batch Send objects for controlled parallelism.
        
        Args:
            sends: List of Send objects
            batch_size: Override default max_concurrent
            
        Returns:
            List of Send batches
        """
        batch_size = batch_size or self.max_concurrent
        batches = []
        
        for i in range(0, len(sends), batch_size):
            batch = sends[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Batched {len(sends)} sends into {len(batches)} batches of max {batch_size}")
        return batches


class BatchSendCoordinator:
    """
    Coordinates batch Send execution with result aggregation.
    Implements patterns from OAMAT_SD for production reliability.
    """
    
    def __init__(self, executor: Optional[ParallelSendExecutor] = None):
        """Initialize with optional custom executor."""
        self.executor = executor or ParallelSendExecutor()
        self.results = {}
        self.errors = {}
        
    def prepare_subdivision_sends(
        self,
        coordinator_node: str,
        executor_node: str,
        tasks: List[Dict[str, Any]],
        subdivision_strategy: str = "balanced"
    ) -> Tuple[Send, List[Send]]:
        """
        Prepare coordinator and executor sends for subdivision pattern.
        
        Pattern from OAMAT_SD:
        1. Coordinator Send to prepare work
        2. Multiple executor Sends for parallel work
        
        Args:
            coordinator_node: Coordinator node name
            executor_node: Executor node name
            tasks: Tasks to subdivide
            subdivision_strategy: How to divide work
            
        Returns:
            Tuple of (coordinator_send, executor_sends)
        """
        # Coordinator send
        coordinator_send = Send(coordinator_node, {
            "tasks": tasks,
            "strategy": subdivision_strategy,
            "total_executors": len(tasks),
            "timestamp": datetime.now().isoformat()
        })
        
        # Executor sends
        executor_sends = self.executor.create_parallel_sends(
            executor_node,
            tasks,
            batch_id=f"subdivision_{datetime.now().timestamp()}"
        )
        
        logger.info(f"Prepared subdivision: 1 coordinator, {len(executor_sends)} executors")
        return coordinator_send, executor_sends
    
    def create_aggregation_send(
        self,
        aggregator_node: str,
        results: List[Dict[str, Any]],
        batch_id: str
    ) -> Send:
        """
        Create Send for result aggregation.
        
        Args:
            aggregator_node: Aggregator node name
            results: Results to aggregate
            batch_id: Batch identifier
            
        Returns:
            Send object for aggregation
        """
        return Send(aggregator_node, {
            "results": results,
            "batch_id": batch_id,
            "total_results": len(results),
            "aggregation_time": datetime.now().isoformat()
        })
    
    def handle_send_failure(
        self,
        send: Send,
        error: Exception,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> Optional[Send]:
        """
        Handle Send execution failure with optional retry.
        
        Args:
            send: Failed Send object
            error: Exception that occurred
            retry_policy: Optional retry configuration
            
        Returns:
            New Send for retry or None
        """
        logger.error(f"Send failed: {error}")
        
        if not retry_policy:
            return None
        
        max_retries = retry_policy.get("max_retries", 3)
        current_retry = send.state.get("retry_count", 0)
        
        if current_retry >= max_retries:
            logger.error(f"Max retries ({max_retries}) exceeded")
            return None
        
        # Create retry Send with backoff
        backoff_ms = retry_policy.get("backoff_ms", 1000) * (2 ** current_retry)
        
        retry_send = (SendBuilder(send.node)
                      .with_custom("original_state", send.state)
                      .with_custom("retry_count", current_retry + 1)
                      .with_custom("retry_after_ms", backoff_ms)
                      .with_custom("previous_error", str(error))
                      .build())
        
        logger.info(f"Created retry Send (attempt {current_retry + 1}/{max_retries})")
        return retry_send