# Agent Interface Stubs for SDLC Automation Factory
# Implementation-ready Python class stubs for all core agents

from typing import Any, Dict, List
from pydantic import BaseModel


class AgentBase:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, *args, **kwargs):
        raise NotImplementedError


class ResearchAgent(AgentBase):
    def run(self, query: str) -> Dict[str, Any]:
        """Perform multi-source research and return findings."""
        ...


class RequirementsAgent(AgentBase):
    def run(self, user_input: str) -> Dict[str, Any]:
        """Gather and structure requirements from user input."""
        ...


class ArchitectureAgent(AgentBase):
    def run(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture based on requirements."""
        ...


class DesignReviewAgent(AgentBase):
    def run(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Review design and provide summary/approval."""
        ...


class ManagementAgent(AgentBase):
    def run(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Orchestrate all agent workflows and manage execution."""
        ...


class EnvironmentAgent(AgentBase):
    def run(self) -> bool:
        """Set up and validate environment and dependencies."""
        ...


class FrontendAgent(AgentBase):
    def run(self, design: Dict[str, Any]) -> Dict[str, Any]:
        ...


class BackendAgent(AgentBase):
    def run(self, design: Dict[str, Any]) -> Dict[str, Any]:
        ...


class DatabaseAgent(AgentBase):
    def run(self, design: Dict[str, Any]) -> Dict[str, Any]:
        ...


class IntegrationAgent(AgentBase):
    def run(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...


class CriticAgent(AgentBase):
    def run(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        ...


class TestingAgent(AgentBase):
    def run(self, code: Dict[str, Any]) -> Dict[str, Any]:
        ...


class DocumentationAgent(AgentBase):
    def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        ...


# Example Pydantic schema for requirements
class RequirementsSchema(BaseModel):
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    constraints: List[str]
    user_stories: List[str]
    acceptance_criteria: List[str]
