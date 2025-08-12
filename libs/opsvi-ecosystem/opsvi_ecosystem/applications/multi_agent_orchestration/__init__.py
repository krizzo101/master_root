"""
Multi-Agent Orchestration Template Application

A comprehensive, modular template demonstrating orchestration, automation,
and multi-agent workflows with robust error handling and extensibility.

Key Features:
- Interface-driven design for maximum extensibility
- Async-first approach for concurrent operations
- Comprehensive error handling and logging
- Support for sequential, parallel, and conditional workflows
- Inter-agent communication and collaboration
- Pluggable tool system
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent Systems Team"

from .agents.base_agent import BaseAgent
from .agents.research_agent import ResearchAgent
from .agents.task_agent import TaskAgent
from .communication.message_broker import MessageBroker
from .orchestrator.workflow_orchestrator import WorkflowOrchestrator
from .tools.base_tool import BaseTool

__all__ = [
    "WorkflowOrchestrator",
    "BaseAgent",
    "ResearchAgent",
    "TaskAgent",
    "BaseTool",
    "MessageBroker",
]
