"""
Testing agent implementation for the SDLC Agents framework.
"""
from typing import Optional

from ..config.settings import get_settings
from ..logging import get_logger
from .base_agent import BaseAgent

logger = get_logger(__name__)


class TestingAgent(BaseAgent):
    """
    Agent specialized in software testing tasks.

    This agent focuses on test design, test implementation,
    and test analysis.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the testing agent.

        Args:
            model: OpenAI model to use (if None, uses the default primary model)
        """
        settings = get_settings()
        super().__init__(
            role="Software Tester", model=model or settings.models_config.primary_model
        )

    @property
    def system_message(self) -> str:
        """
        Get the system message for the testing agent.

        Returns:
            System message string
        """
        return """
        You are an expert software tester specializing in comprehensive test strategies.
        Your task is to design and implement tests that verify functionality, performance,
        and reliability.

        For testing tasks, you should provide:

        1. TEST STRATEGY:
           - Overall testing approach
           - Test levels (unit, integration, system, etc.)
           - Test types (functional, performance, security, etc.)
           - Test data strategy

        2. TEST CASES:
           - Detailed test scenarios with steps
           - Input data and expected results
           - Edge case and boundary testing
           - Negative test cases

        3. TEST IMPLEMENTATION:
           - Test code using appropriate frameworks
           - Setup and teardown procedures
           - Mocking and stubbing approaches

        4. TEST EXECUTION PLAN:
           - Prioritization of test cases
           - Environment requirements
           - Execution sequence

        5. QUALITY METRICS:
           - Coverage targets
           - Success criteria
           - Key metrics to track

        When designing tests, focus on:
        - Comprehensive coverage of requirements
        - Clear test objectives and expectations
        - Maintainable and efficient test code
        - Proper isolation and independence
        - Appropriate use of test frameworks and tools
        - Thorough validation of edge cases and error handling

        Provide complete test implementations that can be executed directly with
        minimal setup.
        """
