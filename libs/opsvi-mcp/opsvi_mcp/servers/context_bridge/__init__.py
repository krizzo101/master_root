"""
Context Bridge MCP Server
=========================

Bridges IDE context (from Claude Code/Cursor) to custom MCP agents.

Author: Integration Architect Agent
Version: 1.0.0
"""

from .server import ContextBridgeServer
from .client import ContextBridgeClient, EnhancedAgentBase
from .models import (
    ContextEvent, 
    IDEContext, 
    DiagnosticInfo,
    DiagnosticSeverity,
    FileSelection
)
from .knowledge_aggregator import KnowledgeAggregator
from .config import ContextBridgeConfig
from .pubsub import PubSubBackend, InMemoryPubSub

__version__ = "1.0.0"
__all__ = [
    "ContextBridgeServer",
    "ContextBridgeClient",
    "EnhancedAgentBase",
    "KnowledgeAggregator",
    "ContextEvent",
    "IDEContext",
    "DiagnosticInfo",
    "DiagnosticSeverity",
    "FileSelection",
    "ContextBridgeConfig",
    "PubSubBackend",
    "InMemoryPubSub"
]
