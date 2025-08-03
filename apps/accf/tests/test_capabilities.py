import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)

from capabilities.collaboration_agent import CollaborationAgent
from capabilities.critique_agent import CritiqueAgent
from capabilities.documentation_agent import DocumentationAgent
from capabilities.execution_agent import ExecutionAgent
from capabilities.feedback_agent import FeedbackAgent
from capabilities.knowledge_agent import KnowledgeAgent
from capabilities.memory_agent import MemoryAgent
from capabilities.research_agent import ResearchAgent
from capabilities.security_agent import SecurityAgent
from capabilities.self_reflection_agent import SelfReflectionAgent
from capabilities.testing_agent import TestingAgent


def test_memory_agent_init():
    agent = MemoryAgent()
    assert hasattr(agent, "memory")


def test_research_agent_init():
    agent = ResearchAgent()
    assert hasattr(agent, "research_db")


def test_execution_agent_init():
    agent = ExecutionAgent()
    assert hasattr(agent, "logger")
    result = agent.execute({"action": "test"})
    assert result["status"] in ["completed", "error"]


def test_collaboration_agent_init():
    agent = CollaborationAgent()
    assert hasattr(agent, "collaborators")


def test_self_reflection_agent_init():
    agent = SelfReflectionAgent()
    assert hasattr(agent, "reflection_log")


def test_knowledge_agent_init():
    agent = KnowledgeAgent()
    assert hasattr(agent, "knowledge_base")


def test_security_agent_init():
    agent = SecurityAgent()
    assert hasattr(agent, "security_layer")


def test_feedback_agent_init():
    agent = FeedbackAgent()
    assert hasattr(agent, "logs")


def test_documentation_agent_init():
    agent = DocumentationAgent()
    assert hasattr(agent, "docs")


def test_critique_agent_init():
    agent = CritiqueAgent()
    assert hasattr(agent, "criteria")


def test_testing_agent_init():
    agent = TestingAgent()
    assert hasattr(agent, "llm")
