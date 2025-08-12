"""
Agent Interface Contracts

ABC interfaces for all agent components emphasizing dynamic generation
and truly agentic behavior (no templates or rules).
"""

from abc import ABC, abstractmethod
from typing import Any

from src.applications.oamat_sd.src.models.data_models import (
    ComplexityAnalysis,
    GapAnalysisResult,
    InformationCompletionResult,
    RequestInput,
    ValidationResult,
)


class IRequestValidationAgent(ABC):
    """Interface for dynamic request validation and information extraction"""

    @abstractmethod
    async def validate_request(self, request: RequestInput) -> ValidationResult:
        """
        Dynamically validate request using AI-driven analysis

        Must use intelligent analysis, not rule-based validation.
        Should adapt validation approach based on request content.
        """
        pass

    @abstractmethod
    async def extract_information_dynamically(
        self, request: RequestInput
    ) -> dict[str, Any]:
        """
        Use AI to extract information from natural language

        Must generate extraction strategy based on content analysis,
        not predefined extraction patterns.
        """
        pass

    @abstractmethod
    async def generate_validation_strategy(self, content: str) -> dict[str, Any]:
        """
        Dynamically generate validation approach for this specific content

        Must create novel validation strategies, not template matching.
        """
        pass


class IGapAnalysisAgent(ABC):
    """Interface for intelligent gap analysis and dynamic prioritization"""

    @abstractmethod
    async def analyze_gaps_intelligently(
        self, request: RequestInput, extracted_info: dict[str, Any]
    ) -> GapAnalysisResult:
        """
        Use AI reasoning to identify and prioritize information gaps

        Must analyze context to determine what's truly needed,
        not check against predefined schemas.
        """
        pass

    @abstractmethod
    async def generate_completion_strategy(self, gaps: list[Any]) -> dict[str, Any]:
        """
        Dynamically generate strategy for filling information gaps

        Must create intelligent completion approaches based on gap analysis.
        """
        pass

    @abstractmethod
    async def prioritize_gaps_contextually(
        self, gaps: list[Any], context: dict[str, Any]
    ) -> list[Any]:
        """
        Use contextual reasoning to prioritize gaps

        Must adapt prioritization to specific request context.
        """
        pass


class IInformationCompletionAgent(ABC):
    """Interface for intelligent information completion using dynamic research"""

    @abstractmethod
    async def complete_information_intelligently(
        self, gaps: GapAnalysisResult, context: dict[str, Any]
    ) -> InformationCompletionResult:
        """
        Intelligently complete missing information using dynamic research

        Must generate novel research and completion strategies,
        not apply predefined defaults.
        """
        pass

    @abstractmethod
    async def research_gap_dynamically(
        self, gap: Any, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Dynamically research information to fill a specific gap

        Must adapt research approach based on gap characteristics.
        """
        pass

    @abstractmethod
    async def generate_intelligent_defaults(
        self, gap: Any, research_results: dict[str, Any]
    ) -> Any:
        """
        Generate contextually appropriate defaults using AI reasoning

        Must create intelligent defaults, not static fallbacks.
        """
        pass


class IComplexityAnalysisModel(ABC):
    """Interface for intelligent complexity analysis using dynamic factor generation"""

    @abstractmethod
    async def analyze_complexity_dynamically(
        self, request: RequestInput, context: dict[str, Any]
    ) -> ComplexityAnalysis:
        """
        Dynamically analyze complexity using AI reasoning

        Must generate novel complexity factors and analysis approaches,
        not use predetermined scoring rules.
        """
        pass

    @abstractmethod
    async def generate_complexity_factors(
        self, request_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Dynamically generate complexity factors specific to this request

        Must create factors that matter for this specific context,
        not use fixed factor lists.
        """
        pass

    @abstractmethod
    async def reason_about_complexity(self, factors: dict[str, Any]) -> dict[str, Any]:
        """
        Use AI reasoning to understand complexity implications

        Must provide intelligent analysis, not rule-based scoring.
        """
        pass


class IO3MasterAgent(ABC):
    """Interface for O3 master agent with dynamic strategy generation"""

    @abstractmethod
    async def generate_execution_strategy(
        self, complexity_analysis: ComplexityAnalysis
    ) -> dict[str, Any]:
        """
        Use O3 reasoning to generate novel execution strategies

        Must create strategies specific to this request context,
        not select from predefined strategy templates.
        """
        pass

    @abstractmethod
    async def design_agent_roles_dynamically(
        self, strategy: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Dynamically design agent roles using O3 reasoning

        Must invent novel agent roles and capabilities,
        not use predefined role lists.
        """
        pass

    @abstractmethod
    async def create_coordination_plan(
        self, agent_roles: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate intelligent coordination plans using O3 reasoning

        Must design novel coordination approaches,
        not use static coordination patterns.
        """
        pass

    @abstractmethod
    async def generate_workflow_structure(
        self, strategy: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Dynamically generate workflow structures using O3 reasoning

        Must create workflows specific to this execution context,
        not use predefined workflow templates.
        """
        pass


class IDynamicAgentFactory(ABC):
    """Interface for truly dynamic agent creation without templates"""

    @abstractmethod
    async def create_agent_from_specification(self, agent_spec: dict[str, Any]) -> Any:
        """
        Create agents from dynamically generated specifications

        Must build agents from novel specifications,
        not instantiate from templates.
        """
        pass

    @abstractmethod
    async def generate_agent_capabilities(
        self, role_spec: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Dynamically generate agent capabilities based on role requirements

        Must create unique capability sets for each agent,
        not use predefined capability templates.
        """
        pass

    @abstractmethod
    async def design_agent_reasoning(
        self, agent_spec: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Design agent-specific reasoning patterns

        Must create reasoning approaches tailored to agent's role,
        not use generic reasoning templates.
        """
        pass

    @abstractmethod
    async def bind_tools_intelligently(
        self, agent_spec: dict[str, Any], available_tools: list[Any]
    ) -> list[Any]:
        """
        Intelligently select and bind tools based on agent requirements

        Must analyze tool needs contextually,
        not use predefined tool assignments.
        """
        pass
