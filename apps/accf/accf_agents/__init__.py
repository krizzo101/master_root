"""
ACCF Research Agent - Production-ready research agent system.

A comprehensive research agent system built with Neo4j GraphRAG,
vector search, and multi-agent orchestration for autonomous research workflows.
"""

__version__ = "0.5.0"
__author__ = "ACCF Team"
__description__ = (
    "Production-ready research agent system with Neo4j GraphRAG integration"
)

from .core.settings import Settings
from .core.orchestrator import AgentOrchestrator

__all__ = ["Settings", "AgentOrchestrator"]
