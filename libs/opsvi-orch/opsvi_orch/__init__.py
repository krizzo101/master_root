"""
OPSVI Orchestration Library
----------------------------
Reusable orchestration patterns and executors for parallel and recursive execution.
Based on LangGraph Send API for true parallelism.

Key Features:
- NO asyncio.gather (forbidden pattern from OAMAT_SD)
- Send API for parallel execution
- Recursive orchestration with depth control
- Integration with Claude Code servers
"""

__version__ = "0.1.0"

# Core patterns
from .patterns import (
    ParallelOrchestrationPattern,
    StateGraphBuilder,
    SendAPIPattern,
    SendBuilder,
    ParallelSendExecutor,
    BatchSendCoordinator,
    RecursiveOrchestrationPattern,
    RecursionLimiter,
    DepthTracker,
    RecursiveGraphBuilder,
)

# Executors
from .executors import (
    ParallelExecutor,
    ParallelExecutionConfig,
    ExecutionResult,
    RecursiveExecutor,
    RecursiveClaudeExecutor,
    RecursiveExecutionResult,
    ClaudeJobExecutor,
    ClaudeBatchExecutor,
    ClaudeExecutionMetrics,
)

# Managers
from .managers import (
    JobManager,
    JobConfig,
    BatchJobResult,
)

__all__ = [
    # Version
    "__version__",
    # Patterns
    "ParallelOrchestrationPattern",
    "StateGraphBuilder",
    "SendAPIPattern",
    "SendBuilder",
    "ParallelSendExecutor",
    "BatchSendCoordinator",
    "RecursiveOrchestrationPattern",
    "RecursionLimiter",
    "DepthTracker",
    "RecursiveGraphBuilder",
    # Executors
    "ParallelExecutor",
    "ParallelExecutionConfig",
    "ExecutionResult",
    "RecursiveExecutor",
    "RecursiveClaudeExecutor",
    "RecursiveExecutionResult",
    "ClaudeJobExecutor",
    "ClaudeBatchExecutor",
    "ClaudeExecutionMetrics",
    # Managers
    "JobManager",
    "JobConfig",
    "BatchJobResult",
]
