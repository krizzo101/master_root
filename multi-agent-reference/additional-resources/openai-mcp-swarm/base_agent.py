"""
Base agent class for the SDLC Agents framework.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel

from ..config.settings import get_settings
from ..logging import get_logger

logger = get_logger(__name__)


class AgentResult(BaseModel):
    """Model for an agent result."""

    success: bool
    message: str
    data: Dict[str, Any] = {}


class BaseAgent(ABC):
    """
    Base agent class for specialized SDLC agents.

    This abstract class defines the interface for all specialized agents
    and provides common functionality.
    """

    def __init__(self, role: str, model: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            role: Agent role/name
            model: OpenAI model to use (if None, uses the default for the agent type)
        """
        self.role = role
        self.settings = get_settings()

        # Set up OpenAI client with API key and additional headers if project ID is available
        headers = {}
        if self.settings.api_config.openai_project_id:
            headers["OpenAI-Project"] = self.settings.api_config.openai_project_id

        self.client = OpenAI(
            api_key=self.settings.api_config.openai_api_key, default_headers=headers
        )

        self.model = model or self.settings.models_config.primary_model
        logger.info(f"Initialized {role} agent using model {self.model}")

    @property
    @abstractmethod
    def system_message(self) -> str:
        """
        Get the system message for the agent.

        Returns:
            System message string
        """
        pass

    def execute(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000
    ) -> AgentResult:
        """
        Execute the agent with the given prompt.

        Args:
            prompt: User prompt for the agent
            temperature: Temperature parameter for the model
            max_tokens: Maximum tokens for the response

        Returns:
            Agent result
        """
        logger.info(f"Executing {self.role} agent with prompt: {prompt[:100]}...")

        try:
            # Base parameters for the API call
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
            }

            # Add temperature parameter only if model is not o3-mini
            if "o3-mini" not in self.model:
                params["temperature"] = temperature

            response = self.client.chat.completions.create(**params)

            content = response.choices[0].message.content

            return AgentResult(
                success=True,
                message=f"{self.role} agent executed successfully",
                data={
                    "content": content,
                    "model": self.model,
                    "role": self.role,
                },
            )

        except Exception as e:
            logger.error(f"Error executing {self.role} agent: {str(e)}")
            return AgentResult(
                success=False,
                message=f"Error executing {self.role} agent: {str(e)}",
                data={
                    "error": str(e),
                    "model": self.model,
                    "role": self.role,
                },
            )
