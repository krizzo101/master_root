"""
OpsVi Meta - Self-Improving Meta-System

A meta-orchestration system that uses the project's own capabilities
to complete, test, and improve itself autonomously.
"""

__version__ = "0.1.0"

from .implementation_pipeline import ImplementationPipeline
from .monitoring import MetaSystemMonitor
from .self_healing import SelfHealingSystem
from .test_automation import TestCoverageAutomation
from .todo_discovery import TodoDiscoveryEngine

__all__ = [
    "TodoDiscoveryEngine",
    "ImplementationPipeline",
    "TestCoverageAutomation",
    "SelfHealingSystem",
    "MetaSystemMonitor",
]
