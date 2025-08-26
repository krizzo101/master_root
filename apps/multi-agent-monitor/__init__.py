"""
Multi-Agent Monitor System
===========================
A comprehensive monitoring and orchestration system for managing teams of Claude agents
working in parallel on complex projects.

Key Features:
- 6-token parallel execution management
- Real-time agent monitoring and session capture
- Team orchestration with specialized roles
- Workflow templates for common project types
- Validation gates and quality assurance
"""

__version__ = "1.0.0"

from .src.monitoring.agent_monitor import (
    MonitoringDashboard,
    PhaseValidator,
    SessionCaptureAgent,
)
from .src.orchestration.team_orchestrator import (
    AgentTeamOrchestrator,
    ProjectType,
    WorkflowTemplate,
)
from .src.orchestration.token_pool import TokenPoolManager

__all__ = [
    "SessionCaptureAgent",
    "PhaseValidator",
    "MonitoringDashboard",
    "AgentTeamOrchestrator",
    "ProjectType",
    "WorkflowTemplate",
    "TokenPoolManager",
]
