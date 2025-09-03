"""
Project Intelligence Integration for Chat Analytics

This module provides correlation between chat logs and project intelligence data,
enabling deep insights into code evolution during chat sessions.
"""

from .agent_analyzer import AgentAnalyzer
from .change_tracker import ChangeTracker
from .code_context import CodeContextExtractor
from .correlator import ProjectIntelligenceCorrelator
from .symbol_tracker import SymbolTracker

__all__ = [
    "ProjectIntelligenceCorrelator",
    "CodeContextExtractor",
    "ChangeTracker",
    "AgentAnalyzer",
    "SymbolTracker",
]

__version__ = "1.0.0"
