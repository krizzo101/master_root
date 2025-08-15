"""
Auto-Forge Factory - Production-Ready Autonomous Software Development Platform

A complete autonomous software development factory that can accept requirements
and deliver complete, tested, optimized software solutions without human intervention.

Features:
- Multi-agent orchestration (Planner, Specifier, Architect, Coder, Tester, etc.)
- End-to-end software development pipeline
- Real-time progress tracking via WebSocket
- Comprehensive testing and validation
- Security and quality assurance
- Performance optimization
- Multi-language support
- Cloud deployment automation
"""

__version__ = "1.0.0"
__author__ = "Auto-Forge Factory Team"

from .api.main import app
from .core.orchestrator import AutoForgeOrchestrator
from .core.agent_registry import AgentRegistry
from .models.schemas import DevelopmentRequest, DevelopmentResponse, JobStatus

__all__ = [
    "app",
    "AutoForgeOrchestrator",
    "AgentRegistry",
    "DevelopmentRequest",
    "DevelopmentResponse",
    "JobStatus",
]
