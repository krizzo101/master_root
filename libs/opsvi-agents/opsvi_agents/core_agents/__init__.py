"""Core Agent Set - Essential agents that cover general needs."""

from .planner import PlannerAgent
from .executor import ExecutorAgent
from .critic import CriticAgent
from .research import ResearchAgent
from .interface import InterfaceAgent

__all__ = [
    "PlannerAgent",
    "ExecutorAgent", 
    "CriticAgent",
    "ResearchAgent",
    "InterfaceAgent",
]