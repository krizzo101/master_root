"""
Swarm task decomposition for parallel execution.
"""

from .swarm_decomposer import ExecutionGroup, SwarmTaskDecomposer, TaskNode

__all__ = [
    "SwarmTaskDecomposer",
    "ExecutionGroup",
    "TaskNode",
]
