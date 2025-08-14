"""
Orchestration Patterns Module
-----------------------------
Reusable orchestration patterns extracted from production systems.
Based on LangGraph Send API for true parallel execution.
"""

from .langgraph_patterns import (
    ParallelOrchestrationPattern,
    StateGraphBuilder,
    SendAPIPattern
)
from .send_api import (
    SendBuilder,
    ParallelSendExecutor,
    BatchSendCoordinator
)
from .recursive_orch import (
    RecursiveOrchestrationPattern,
    RecursionLimiter,
    DepthTracker,
    RecursiveGraphBuilder
)

__all__ = [
    # LangGraph patterns
    'ParallelOrchestrationPattern',
    'StateGraphBuilder',
    'SendAPIPattern',
    
    # Send API patterns
    'SendBuilder',
    'ParallelSendExecutor',
    'BatchSendCoordinator',
    
    # Recursive patterns
    'RecursiveOrchestrationPattern',
    'RecursionLimiter',
    'DepthTracker',
    'RecursiveGraphBuilder',
]