# Coordination system package
#
# Provides agent coordination, registry, and messaging capabilities
# for the multi-agent system.

from .agent_registry import AgentRegistry, get_registry, initialize_registry
from .enhanced_agent_registry import (
    EnhancedAgentRegistry,
    get_enhanced_registry,
    initialize_enhanced_registry,
    AgentMetrics,
    RegistrationStatus,
    HealthLevel,
    FileStorageBackend,
    MemoryStorageBackend,
)

__all__ = [
    # Legacy registry
    "AgentRegistry",
    "get_registry",
    "initialize_registry",
    # Enhanced registry
    "EnhancedAgentRegistry",
    "get_enhanced_registry",
    "initialize_enhanced_registry",
    "AgentMetrics",
    "RegistrationStatus",
    "HealthLevel",
    "FileStorageBackend",
    "MemoryStorageBackend",
]
