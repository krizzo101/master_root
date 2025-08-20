"""Core Agent Set - Essential agents that cover general needs."""

# New core agents (6 fundamental agents)
from .analysis import AnalysisAgent
from .coder import CoderAgent
from .critic import CriticAgent
from .executor import ExecutorAgent
from .interface import InterfaceAgent
from .learner import LearnerAgent
from .monitor import MonitorAgent
from .optimizer import OptimizerAgent
from .orchestrator import OrchestratorAgent

# Existing agents
from .planner import PlannerAgent
from .reporter import ReporterAgent
from .research import ResearchAgent
from .test import TestAgent
from .transform import TransformAgent
from .validator import ValidatorAgent

__all__ = [
    # New core agents
    "CoderAgent",
    "TestAgent",
    "OrchestratorAgent",
    "MonitorAgent",
    "OptimizerAgent",
    "LearnerAgent",
    # Existing agents
    "PlannerAgent",
    "ExecutorAgent",
    "CriticAgent",
    "ResearchAgent",
    "InterfaceAgent",
    "TransformAgent",
    "AnalysisAgent",
    "ValidatorAgent",
    "ReporterAgent",
]
