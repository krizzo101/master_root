"""Orchestrator package for pipeline management and task coordination."""

# Use lazy imports to avoid circular dependencies
from .budgets import BudgetManager, BudgetPeriod, BudgetType
from .dag_loader import DAGLoader, ExecutionDAG, PipelineConfig
from .policies import BasePolicy, PolicyManager
from .registry import TaskRegistryManager
from .router import ModelRouter, RoutingDecision
from .task_models import TaskDefinition, TaskExecution, TaskResult


# Lazy imports to avoid circular dependencies
def _get_task_execution_imports():
    """Lazy import for task execution components."""
    from .execution_coordinator import ExecutionCoordinator
    from .task_execution_bridge import TaskExecutionBridge
    from .task_execution_engine import CeleryTaskExecutionEngine, TaskExecutionEngine

    return (
        TaskExecutionEngine,
        CeleryTaskExecutionEngine,
        TaskExecutionBridge,
        ExecutionCoordinator,
    )


def _get_dependency_container_imports():
    """Lazy import for dependency container components."""
    from .dependency_container import (
        DependencyContainer,
        clear_container,
        get_container,
        get_service,
        has_service,
        inject,
        register_factory,
        register_service,
        register_singleton,
    )

    return (
        DependencyContainer,
        get_container,
        register_service,
        register_factory,
        register_singleton,
        get_service,
        inject,
        has_service,
        clear_container,
    )


from .exceptions import (
    OrchestrationError,
    PipelineError,
    ResourceError,
    TaskExecutionError,
    TimeoutError,
    ValidationError,
)


# Lazy import for meta_orchestrator to avoid circular imports
def _get_meta_orchestrator_imports():
    """Lazy import for meta_orchestrator components."""
    from .meta_orchestrator import (
        MetaOrchestrator,
        OrchestrationContext,
        OrchestrationStatus,
    )

    return MetaOrchestrator, OrchestrationContext, OrchestrationStatus


__all__ = [
    "MetaOrchestrator",
    "OrchestrationContext",
    "OrchestrationStatus",
    "TaskRegistryManager",
    "DAGLoader",
    "ExecutionDAG",
    "PipelineConfig",
    "PolicyManager",
    "BasePolicy",
    "BudgetManager",
    "BudgetType",
    "BudgetPeriod",
    "ModelRouter",
    "RoutingDecision",
    "TaskDefinition",
    "TaskExecution",
    "TaskResult",
    "TaskExecutionEngine",
    "CeleryTaskExecutionEngine",
    "TaskExecutionBridge",
    "ExecutionCoordinator",
    "DependencyContainer",
    "get_container",
    "register_service",
    "register_factory",
    "register_singleton",
    "get_service",
    "inject",
    "has_service",
    "clear_container",
    "OrchestrationError",
    "PipelineError",
    "TaskExecutionError",
    "ValidationError",
    "ResourceError",
    "TimeoutError",
]


# Lazy import implementation
def __getattr__(name):
    """Lazy import for components."""
    if name in ["MetaOrchestrator", "OrchestrationContext", "OrchestrationStatus"]:
        (
            MetaOrchestrator,
            OrchestrationContext,
            OrchestrationStatus,
        ) = _get_meta_orchestrator_imports()
        if name == "MetaOrchestrator":
            return MetaOrchestrator
        elif name == "OrchestrationContext":
            return OrchestrationContext
        elif name == "OrchestrationStatus":
            return OrchestrationStatus
    elif name in [
        "TaskExecutionEngine",
        "CeleryTaskExecutionEngine",
        "TaskExecutionBridge",
        "ExecutionCoordinator",
    ]:
        (
            TaskExecutionEngine,
            CeleryTaskExecutionEngine,
            TaskExecutionBridge,
            ExecutionCoordinator,
        ) = _get_task_execution_imports()
        if name == "TaskExecutionEngine":
            return TaskExecutionEngine
        elif name == "CeleryTaskExecutionEngine":
            return CeleryTaskExecutionEngine
        elif name == "TaskExecutionBridge":
            return TaskExecutionBridge
        elif name == "ExecutionCoordinator":
            return ExecutionCoordinator
    elif name in [
        "DependencyContainer",
        "get_container",
        "register_service",
        "register_factory",
        "register_singleton",
        "get_service",
        "inject",
        "has_service",
        "clear_container",
    ]:
        (
            DependencyContainer,
            get_container,
            register_service,
            register_factory,
            register_singleton,
            get_service,
            inject,
            has_service,
            clear_container,
        ) = _get_dependency_container_imports()
        if name == "DependencyContainer":
            return DependencyContainer
        elif name == "get_container":
            return get_container
        elif name == "register_service":
            return register_service
        elif name == "register_factory":
            return register_factory
        elif name == "register_singleton":
            return register_singleton
        elif name == "get_service":
            return get_service
        elif name == "inject":
            return inject
        elif name == "has_service":
            return has_service
        elif name == "clear_container":
            return clear_container
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
