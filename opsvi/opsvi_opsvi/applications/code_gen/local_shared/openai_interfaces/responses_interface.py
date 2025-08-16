"""
Modern OpenAI Structured Outputs Interface

This module provides a clean interface for OpenAI's native structured outputs functionality
using client.chat.completions.parse() instead of manual schema injection.

Updated for July 2025 best practices.
"""

import logging
from typing import TypeVar, Type, Optional, Any, Dict
from pydantic import BaseModel
from openai import OpenAI
from openai.types.chat import ChatCompletion

from .model_selector import validate_model_constraints

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIResponsesInterface:
    """
    Modern interface for OpenAI structured outputs using native SDK methods.

    This replaces the legacy manual schema injection approach with the
    recommended client.chat.completions.parse() method.
    """

    def __init__(self):
        self.client = OpenAI()
        logger.info("Initialized OpenAI Structured Outputs Interface")

    def create_structured_response(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        model: str = "gpt-4.1",
        system_prompt: str = "",
        **kwargs,
    ) -> BaseModel:
        """
        Create a structured response using OpenAI's native structured outputs.

        Args:
            prompt: The user prompt
            response_model: Pydantic model defining the expected response structure
            model: OpenAI model to use (must support structured outputs)
            system_prompt: Optional system message
            **kwargs: Additional parameters for the chat completion

        Returns:
            Instance of response_model with parsed response

        Raises:
            ValueError: If model is not approved or response cannot be parsed
            Exception: For other API errors
        """
        # Validate model
        if not validate_model_constraints(model):
            raise ValueError(
                f"Model {model} is not approved. Use one of the approved models."
            )

        logger.info(
            f"Creating structured response with model {model} and schema {response_model.__name__}"
        )

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use native structured outputs with parse method
            completion = self.client.chat.completions.parse(
                model=model, messages=messages, response_format=response_model, **kwargs
            )

            message = completion.choices[0].message

            # Handle refusals
            if message.refusal:
                raise ValueError(f"Model refused to respond: {message.refusal}")

            # Return parsed response
            if message.parsed:
                logger.info(f"Successfully parsed structured response")
                return message.parsed
            else:
                raise ValueError("Response was not properly parsed despite no refusal")

        except Exception as e:
            logger.error(f"Structured response creation failed: {str(e)}")
            raise

    def create_simple_response(
        self,
        prompt: str,
        model: str = "gpt-4.1-mini",
        system_prompt: str = "",
        **kwargs,
    ) -> str:
        """
        Create a simple text response without structured output.

        Args:
            prompt: The user prompt
            model: OpenAI model to use
            system_prompt: Optional system message
            **kwargs: Additional parameters for the chat completion

        Returns:
            The response content as a string

        Raises:
            ValueError: If model is not approved
            Exception: For other API errors
        """
        # Validate model
        if not validate_model_constraints(model):
            raise ValueError(
                f"Model {model} is not approved. Use one of the approved models."
            )

        logger.info(f"Creating simple response with model {model}")

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use regular chat completion
            completion = self.client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )

            message = completion.choices[0].message

            # Handle refusals
            if hasattr(message, "refusal") and message.refusal:
                raise ValueError(f"Model refused to respond: {message.refusal}")

            if message.content:
                logger.info("Successfully created simple response")
                return message.content
            else:
                raise ValueError("No content in response")

        except Exception as e:
            logger.error(f"Simple response creation failed: {str(e)}")
            raise


# Global instance for lazy initialization
_openai_interface: Optional[OpenAIResponsesInterface] = None


def get_openai_interface(*args, **kwargs) -> OpenAIResponsesInterface:
    """
    Get the global OpenAI interface instance.

    Accepts an optional api_key (ignored) for backward compatibility with older tests.
    """
    global _openai_interface
    if _openai_interface is None:
        _openai_interface = OpenAIResponsesInterface()
    return _openai_interface
