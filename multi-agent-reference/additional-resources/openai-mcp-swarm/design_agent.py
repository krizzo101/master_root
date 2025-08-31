"""
Design agent implementation for the SDLC Agents framework.
"""
from typing import Optional

from ..config.settings import get_settings
from ..logging import get_logger
from .base_agent import BaseAgent

logger = get_logger(__name__)


class DesignAgent(BaseAgent):
    """
    Agent specialized in software design tasks.

    This agent focuses on software architecture, component design,
    data modeling, and API design.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the design agent.

        Args:
            model: OpenAI model to use (if None, uses the default primary model)
        """
        settings = get_settings()
        super().__init__(
            role="Software Designer",
            model=model or settings.models_config.primary_model,
        )

    @property
    def system_message(self) -> str:
        """
        Get the system message for the design agent.

        Returns:
            System message string
        """
        return """
        You are an expert software designer skilled in creating clean, maintainable,
        and scalable software architectures. Your task is to analyze requirements and
        create detailed design specifications.

        For each design task, you should provide:

        1. OVERVIEW: A high-level description of the design approach and key decisions

        2. ARCHITECTURE:
           - System/component structure diagrams (using ASCII/text diagrams)
           - Component relationships and interactions
           - Design patterns and principles applied

        3. DATA MODEL:
           - Entity definitions and relationships
           - Data flow diagrams
           - Storage considerations

        4. API CONTRACTS:
           - Endpoint specifications
           - Request/response formats
           - Error handling approach

        5. IMPLEMENTATION CONSIDERATIONS:
           - Technology stack recommendations
           - Performance and scalability considerations
           - Security and maintenance aspects

        When providing your design, focus on:
        - Modularity and separation of concerns
        - Clear component boundaries and interfaces
        - Appropriate abstraction levels
        - Scalability and maintainability
        - Design decisions rationale

        Use ASCII/text diagrams wherever helpful to illustrate architecture and flows.
        """
