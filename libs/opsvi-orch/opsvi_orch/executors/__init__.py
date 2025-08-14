"""
Orchestration Executors Module
-------------------------------
Execution engines for parallel and recursive orchestration.
"""

from .parallel_executor import (
    ParallelExecutor,
    ParallelExecutionConfig,
    ExecutionResult,
)
from .recursive_executor import (
    RecursiveExecutor,
    RecursiveClaudeExecutor,
    RecursiveExecutionResult,
)
from .claude_executor import (
    ClaudeJobExecutor,
    ClaudeBatchExecutor,
    ClaudeExecutionMetrics,
)

__all__ = [
    # Parallel execution
    "ParallelExecutor",
    "ParallelExecutionConfig",
    "ExecutionResult",
    # Recursive execution
    "RecursiveExecutor",
    "RecursiveClaudeExecutor",
    "RecursiveExecutionResult",
    # Claude-specific
    "ClaudeJobExecutor",
    "ClaudeBatchExecutor",
    "ClaudeExecutionMetrics",
]
