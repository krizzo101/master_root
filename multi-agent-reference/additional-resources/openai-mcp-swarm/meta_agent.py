"""
MetaInterpreterAgent implementation for the SDLC Agents framework.

This agent operates as an intermediary between the user and specialized expert agents.
It interprets user requests, restructures them, and delegates to the appropriate expert agent.
"""
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from openai import OpenAI
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..logging import get_logger
from ..tools.brave_search import BraveSearchTool

logger = get_logger(__name__)


class ExpertProfile(BaseModel):
    """Model for an expert agent profile."""

    role: str = Field(..., description="The expert's role")
    system_message: str = Field(..., description="System message for the expert agent")
    model: str = Field(..., description="OpenAI model to use for this expert")
    temperature: float = Field(
        0.2, description="Temperature setting for the expert agent"
    )
    max_tokens: int = Field(
        4000, description="Maximum tokens for the expert agent's response"
    )


class InterpretedRequest(BaseModel):
    """Model for an interpreted user request."""

    original_request: str = Field(..., description="Original user request")
    interpreted_intent: str = Field(
        ..., description="Interpreted intent of the request"
    )
    expert_role: str = Field(
        ..., description="Selected expert role for handling the request"
    )
    optimized_prompt: str = Field(
        ..., description="Optimized prompt for the expert agent"
    )
    task_components: List[str] = Field(
        default_factory=list, description="Components of the task"
    )


class MetaAgent:
    """
    MetaInterpreterAgent for interpreting user requests and delegating to expert agents.

    This agent:
    1. Interprets and restructures user prompts
    2. Infers task components and requirements
    3. Matches to the appropriate expert profile
    4. Confirms intent with the user
    5. Delegates to the expert agent for execution
    """

    def __init__(self):
        """Initialize the MetaAgent."""
        self.settings = get_settings()

        # Set up OpenAI client with API key and additional headers if project ID is available
        headers = {}
        if self.settings.api_config.openai_project_id:
            headers["OpenAI-Project"] = self.settings.api_config.openai_project_id

        self.client = OpenAI(
            api_key=self.settings.api_config.openai_api_key, default_headers=headers
        )

        # Initialize tools
        if self.settings.api_config.brave_api_key:
            self.brave_search = BraveSearchTool(self.settings.api_config.brave_api_key)
        else:
            self.brave_search = None
            logger.warning(
                "Brave Search API key not provided, search tool will be unavailable"
            )

        # Expert profiles
        self.expert_profiles = self._load_expert_profiles()

        logger.info("MetaAgent initialized")

    def _load_expert_profiles(self) -> Dict[str, ExpertProfile]:
        """
        Load expert agent profiles.

        Returns:
            Dictionary of expert profiles keyed by role
        """
        # In a real implementation, these might be loaded from a JSON file or database
        return {
            "design": ExpertProfile(
                role="Software Designer",
                system_message=(
                    "You are an expert software designer skilled in creating clean, "
                    "maintainable, and scalable software architectures. Your task is to "
                    "analyze requirements and create detailed design specifications, "
                    "including system diagrams, component relationships, data models, "
                    "and API contracts. Focus on modular design principles, separation "
                    "of concerns, and appropriate design patterns."
                ),
                model=self.settings.models_config.primary_model,
                temperature=0.3,
                max_tokens=4000,
            ),
            "development": ExpertProfile(
                role="Software Developer",
                system_message=(
                    "You are an expert software developer with deep knowledge of best practices, "
                    "design patterns, and efficient coding techniques. Your task is to implement "
                    "software components according to specifications, ensuring clean, readable, and "
                    "maintainable code. Focus on writing modular code with appropriate error handling, "
                    "optimizations, and documentation."
                ),
                model=self.settings.models_config.primary_model,
                temperature=0.2,
                max_tokens=4000,
            ),
            "testing": ExpertProfile(
                role="Software Tester",
                system_message=(
                    "You are an expert software tester specializing in comprehensive test strategies. "
                    "Your task is to design and implement tests that verify functionality, performance, "
                    "and reliability. Focus on test coverage, edge cases, integration testing, and "
                    "test automation approaches."
                ),
                model=self.settings.models_config.primary_model,
                temperature=0.2,
                max_tokens=3000,
            ),
            "research": ExpertProfile(
                role="Technology Researcher",
                system_message=(
                    "You are an expert technology researcher with expertise in evaluating tools, "
                    "frameworks, and approaches. Your task is to analyze technical options, compare "
                    "alternatives, and provide evidence-based recommendations. Focus on current "
                    "best practices, community adoption, and technology fit for specific requirements."
                ),
                model=self.settings.models_config.reasoning_model,
                temperature=0.4,
                max_tokens=4000,
            ),
        }

    def interpret_request(self, user_request: str) -> InterpretedRequest:
        """
        Interpret a user request and identify the appropriate expert agent.

        Args:
            user_request: The original user request

        Returns:
            An interpreted request
        """
        logger.info(f"Interpreting user request: {user_request[:100]}...")

        system_prompt = """
        You are a meta-interpreter agent whose job is to analyze user requests
        and identify the most appropriate expert for handling the task.

        You should:
        1. Interpret the user's request and clarify the intent
        2. Identify the expert role that is best suited for the task
        3. Structure the request for the expert in a clear, actionable format
        4. Break down the task into key components

        The available expert roles are:
        - design: For software architecture and design tasks
        - development: For implementation and coding tasks
        - testing: For quality assurance and testing tasks
        - research: For investigating technologies, tools, and approaches

        Respond with a JSON object containing:
        - interpreted_intent: A clear restatement of what the user is asking for
        - expert_role: The most appropriate expert role from the list above
        - optimized_prompt: A clean, structured version of the request for the expert
        - task_components: A list of the main components or subtasks involved
        """

        try:
            # Base parameters for the API call
            params = {
                "model": self.settings.models_config.reasoning_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_request},
                ],
                "response_format": {"type": "json_object"},
            }

            # Add temperature parameter only if model is not o3-mini
            if "o3-mini" not in self.settings.models_config.reasoning_model:
                params["temperature"] = 0.2

            response = self.client.chat.completions.create(**params)

            # Extract and parse the response
            content = response.choices[0].message.content
            parsed_response = json.loads(content)

            # Create the interpreted request
            interpreted_request = InterpretedRequest(
                original_request=user_request,
                interpreted_intent=parsed_response.get("interpreted_intent", ""),
                expert_role=parsed_response.get("expert_role", "development"),
                optimized_prompt=parsed_response.get("optimized_prompt", user_request),
                task_components=parsed_response.get("task_components", []),
            )

            logger.info(
                f"Request interpreted as '{interpreted_request.expert_role}' task"
            )
            return interpreted_request

        except Exception as e:
            logger.error(f"Error interpreting request: {str(e)}")
            # Fallback to a simple interpretation
            return InterpretedRequest(
                original_request=user_request,
                interpreted_intent=user_request,
                expert_role="development",
                optimized_prompt=user_request,
                task_components=[],
            )

    def confirm_intent(self, interpreted_request: InterpretedRequest) -> bool:
        """
        Confirm the interpreted intent with the user.

        In a real system, this would interact with the user to get confirmation.
        For this MVP, we'll assume the intent is correct.

        Args:
            interpreted_request: The interpreted request details

        Returns:
            True if the intent is confirmed, False otherwise
        """
        # In a real implementation, this would prompt the user for confirmation
        logger.info(f"Intent confirmation: {interpreted_request.interpreted_intent}")
        return True

    def execute_expert_task(
        self, interpreted_request: InterpretedRequest
    ) -> Dict[str, Any]:
        """
        Execute the task using the appropriate expert agent.

        Args:
            interpreted_request: The interpreted request details

        Returns:
            Expert agent's response
        """
        expert_role = interpreted_request.expert_role

        # Get the expert profile
        if expert_role not in self.expert_profiles:
            logger.warning(
                f"Unknown expert role: {expert_role}, defaulting to development"
            )
            expert_role = "development"

        expert = self.expert_profiles[expert_role]
        logger.info(f"Executing task with {expert_role} expert")

        # Prepare the prompt with intent confirmation
        prompt = (
            f'What I hear you asking is: "{interpreted_request.interpreted_intent}"\n\n'
            f"{interpreted_request.optimized_prompt}"
        )

        # Execute the expert agent
        try:
            # Base parameters for the API call
            params = {
                "model": expert.model,
                "messages": [
                    {"role": "system", "content": expert.system_message},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": expert.max_tokens,
            }

            # Add temperature parameter only if model is not o3-mini
            if "o3-mini" not in expert.model:
                params["temperature"] = expert.temperature

            response = self.client.chat.completions.create(**params)

            result = {
                "expert_role": expert_role,
                "interpreted_intent": interpreted_request.interpreted_intent,
                "response": response.choices[0].message.content,
                "model": expert.model,
            }

            logger.info(f"Expert task completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error executing expert task: {str(e)}")
            return {
                "expert_role": expert_role,
                "interpreted_intent": interpreted_request.interpreted_intent,
                "response": f"Error executing task: {str(e)}",
                "model": expert.model,
            }

    def process(self, user_request: str) -> Dict[str, Any]:
        """
        Process a user request through the complete workflow.

        Args:
            user_request: The original user request

        Returns:
            Expert agent's response
        """
        logger.info(f"Processing user request: {user_request[:100]}...")

        # Step 1: Interpret the request
        interpreted_request = self.interpret_request(user_request)

        # Step 2: Confirm intent (in a real system, this would interact with the user)
        intent_confirmed = self.confirm_intent(interpreted_request)
        if not intent_confirmed:
            logger.info("Intent not confirmed, returning")
            return {
                "expert_role": None,
                "interpreted_intent": interpreted_request.interpreted_intent,
                "response": "Intent not confirmed. Please provide more details or rephrase your request.",
                "model": None,
            }

        # Step 3: Execute the task with the appropriate expert
        result = self.execute_expert_task(interpreted_request)

        return result
