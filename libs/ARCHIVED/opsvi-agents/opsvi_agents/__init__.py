"""OPSVI-Agents Core V2 - Production-ready agent framework."""

__version__ = "2.0.0"

# Adapters
from .adapters import UniversalAgentAdapter, migrate_legacy_agent

# Core components
from .core import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentResult,
    AgentState,
    BaseAgent,
)

# Learning
from .learning import ErrorPattern, ErrorPatternLearner, Solution
from .learning import learner as error_learner

# Migration
from .migration import AgentMigrator, migrator

# Monitoring
from .monitoring import (
    Checkpoint,
    CheckpointManager,
    PerformanceMetric,
    TelemetryTracker,
    Timer,
)
from .monitoring import manager as checkpoint_manager
from .monitoring import tracker as telemetry_tracker

# Parallel execution
from .parallel import (
    ParallelAgentExecutor,
    ParallelResult,
    ParallelTask,
    create_parallel_executor,
)

# Registry
from .registry import AgentDefinition, AgentRegistry
from .registry import registry as agent_registry

# Templates
from .templates import ReActAgent, SubTask, SupervisorAgent, ToolAgent

# Tools
from .tools import ToolDefinition, ToolRegistry
from .tools import registry as tool_registry

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
