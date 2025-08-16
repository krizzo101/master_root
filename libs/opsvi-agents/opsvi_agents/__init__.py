"""OPSVI-Agents Core V2 - Production-ready agent framework."""

__version__ = "2.0.0"

# Core components
from .core import (
    BaseAgent,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentResult,
    AgentState,
    AgentCapability,
)

# Registry
from .registry import (
    AgentRegistry,
    AgentDefinition,
    registry as agent_registry,
)

# Tools
from .tools import (
    ToolRegistry,
    ToolDefinition,
    registry as tool_registry,
)

# Adapters
from .adapters import (
    UniversalAgentAdapter,
    migrate_legacy_agent,
)

# Parallel execution
from .parallel import (
    ParallelAgentExecutor,
    ParallelTask,
    ParallelResult,
    create_parallel_executor,
)

# Learning
from .learning import (
    ErrorPatternLearner,
    ErrorPattern,
    Solution,
    learner as error_learner,
)

# Monitoring
from .monitoring import (
    TelemetryTracker,
    PerformanceMetric,
    Timer,
    tracker as telemetry_tracker,
    CheckpointManager,
    Checkpoint,
    manager as checkpoint_manager,
)

# Migration
from .migration import (
    AgentMigrator,
    migrator,
)

# Templates
from .templates import (
    ReActAgent,
    ToolAgent,
    SupervisorAgent,
    SubTask,
)

__all__ = [
    # Version
    "__version__",
    
    # Core
    "BaseAgent",
    "AgentConfig",
    "AgentContext",
    "AgentMessage",
    "AgentResult",
    "AgentState",
    "AgentCapability",
    
    # Registry
    "AgentRegistry",
    "AgentDefinition",
    "agent_registry",
    
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    "tool_registry",
    
    # Adapters
    "UniversalAgentAdapter",
    "migrate_legacy_agent",
    
    # Parallel
    "ParallelAgentExecutor",
    "ParallelTask",
    "ParallelResult",
    "create_parallel_executor",
    
    # Learning
    "ErrorPatternLearner",
    "ErrorPattern",
    "Solution",
    "error_learner",
    
    # Monitoring
    "TelemetryTracker",
    "PerformanceMetric",
    "Timer",
    "telemetry_tracker",
    "CheckpointManager",
    "Checkpoint",
    "checkpoint_manager",
    
    # Migration
    "AgentMigrator",
    "migrator",
    
    # Templates
    "ReActAgent",
    "ToolAgent",
    "SupervisorAgent",
    "SubTask",
]
