"""Core Agent Set - Essential agents that cover general needs."""

# New core agents (6 fundamental agents)
from .coder import CoderAgent
from .test import TestAgent
from .orchestrator import OrchestratorAgent
from .monitor import MonitorAgent
from .optimizer import OptimizerAgent
from .learner import LearnerAgent

# Existing agents
from .planner import PlannerAgent
from .executor import ExecutorAgent
from .critic import CriticAgent
from .research import ResearchAgent
from .interface import InterfaceAgent
from .transform import TransformAgent
from .analysis import AnalysisAgent
from .validator import ValidatorAgent
from .reporter import ReporterAgent

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
    "ReporterAgent"
]