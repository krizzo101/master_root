"""
OPSVI Orchestration Library (opsvi_orch)
-----------------------------------------
Comprehensive orchestration library with multiple levels:

1. Workflow Orchestration (Higher Level):
   - DAG-based workflow management
   - Pipeline coordination with Celery
   - Task models and registry
   
2. Execution Orchestration (Lower Level):
   - LangGraph patterns for parallel execution
   - Send API for true parallelism (NO asyncio.gather)
   - Recursive execution patterns
   
3. Integration:
   - Claude Code server enhancement
   - Configuration-based feature enablement
"""

__version__ = "0.1.0"

# Workflow orchestration (from original opsvi_orchestration)
from .workflow import (
    MetaOrchestrator,
    dag_loader,
    Project,
    Run,
    TaskRecord,
    WorkflowRegistry,
)

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

# Integration
from .integration import (
    ClaudeOrchestrationConfig,
    ClaudeOrchestrationIntegration,
    enhance_claude_code_server,
)

__all__ = [
    # Version
    "__version__",
    # Workflow (from original)
    "MetaOrchestrator",
    "dag_loader",
    "Project",
    "Run",
    "TaskRecord",
    "WorkflowRegistry",
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
    # Integration
    "ClaudeOrchestrationConfig",
    "ClaudeOrchestrationIntegration",
    "enhance_claude_code_server",
]
