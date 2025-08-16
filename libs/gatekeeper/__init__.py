"""
Gatekeeper Module

A reusable module for intelligent file dependency analysis and context management.
Can be integrated into any agent that needs to analyze file relationships and
optimize context for LLM processing.
"""

from auto_attach import AutoAttach
from context_analyzer import ContextAnalyzer
from gatekeeper_agent import GatekeeperAgent

__version__ = "1.0.0"
__all__ = ["AutoAttach", "GatekeeperAgent", "ContextAnalyzer"]
