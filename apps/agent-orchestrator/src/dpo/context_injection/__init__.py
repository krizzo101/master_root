"""
Context Injection System
Provides agents with relevant ecosystem knowledge without overwhelming them
"""

from .context_system import (
    AgentContext,
    ContextFilter,
    ContextInjectionSystem,
    DynamicContextGenerator,
    EcosystemDiscovery,
    ToolCapability,
    get_context_system,
)
from .orchestrator_integration import (
    ContextAwareOrchestrator,
    OrchestratorContextInjector,
    create_context_aware_orchestrator,
    inject_context_into_orchestrator,
)

__all__ = [
    # Core system
    "ContextInjectionSystem",
    "EcosystemDiscovery",
    "ContextFilter",
    "DynamicContextGenerator",
    "AgentContext",
    "ToolCapability",
    "get_context_system",
    # Orchestrator integration
    "OrchestratorContextInjector",
    "inject_context_into_orchestrator",
    "ContextAwareOrchestrator",
    "create_context_aware_orchestrator",
]

__version__ = "1.0.0"
