"""
Research-based OpenAI Responses API client with proper structured outputs.
Based on comprehensive research of OpenAI documentation and testing.
"""

import json
from typing import Any, Dict, Optional, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from .simplified_schemas import (
    get_simplified_schema_for_operation,
)

T = TypeVar("T", bound=BaseModel)


class ResponsesAPIClientFixed:
    """
    Research-based client for OpenAI Responses API with structured outputs.
    Uses correct API paths and parameters based on comprehensive documentation research.
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

        # Model categorization based on research
        self.thinking_models = {"o3", "o4-mini", "o3-mini"}

        # Model pricing (per 1M tokens) - research-based current pricing
        self.model_pricing = {
            "gpt-4.1": {"input": 30.0, "output": 60.0},
            "gpt-4.1-mini": {"input": 0.15, "output": 0.60},
            "o3": {"input": 60.0, "output": 240.0},
            "o4-mini": {"input": 0.15, "output": 0.60},
            "o3-mini": {"input": 0.15, "output": 0.60},
        }

    async def create_structured_response(
        self,
        model: str,
        instructions: str,
        user_input: str,
        response_schema: Type[BaseModel],
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured response using the correct Responses API with JSON schema.

        Research findings:
        - Uses client.chat.responses.create() (not client.responses.create())
        - Uses 'input' parameter instead of 'messages'
        - Supports response_format with JSON schema
        - Requires simplified schemas for complex structures
        """
        try:
            # Convert Pydantic schema to JSON schema
            json_schema = response_schema.model_json_schema()

            # Create proper response format for structured outputs
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__.lower(),
                    "strict": True,
                    "schema": json_schema,
                },
            }

            # Enhanced instructions for JSON requirement
            enhanced_instructions = f"""{instructions}

IMPORTANT: Respond with valid JSON that exactly matches the required schema. Provide specific, actionable content for each field."""

            # Use correct API path: client.chat.responses.create()
            response = await self.client.chat.responses.create(
                model=model,
                instructions=enhanced_instructions,
                input=user_input,  # Use 'input' not 'messages'
                response_format=response_format,
            )

            # Parse and validate the response
            try:
                parsed_data = json.loads(response.output_text)
                validated_response = response_schema.model_validate(parsed_data)

                # Calculate usage and cost
                usage_info = self._get_usage_info(response)
                cost_info = (
                    self._calculate_cost(model, response.usage)
                    if hasattr(response, "usage")
                    else {}
                )

                return {
                    "success": True,
                    "data": validated_response.model_dump(),
                    "usage": usage_info,
                    "cost_info": cost_info,
                    "model": model,
                    "model_type": (
                        "thinking" if model in self.thinking_models else "non-thinking"
                    ),
                    "raw_response": response.output_text,
                    "api_method": "chat.responses.create (structured)",
                }

            except (json.JSONDecodeError, ValidationError):
                # Fallback to non-structured response
                return await self.create_fallback_response(
                    model, instructions, user_input
                )

        except Exception as e:
            # If structured approach fails, try fallback
            if "response_format" in str(e).lower():
                return await self.create_fallback_response(
                    model, instructions, user_input
                )
            else:
                return {
                    "success": False,
                    "error": f"Responses API error: {str(e)}",
                    "model": model,
                    "api_method": "chat.responses.create (failed)",
                }

    async def create_fallback_response(
        self, model: str, instructions: str, user_input: str
    ) -> Dict[str, Any]:
        """
        Create a response without structured outputs using correct API path.
        """
        try:
            # Use correct API path without structured outputs
            response = await self.client.chat.responses.create(
                model=model, instructions=instructions, input=user_input
            )

            # Get usage and cost information
            usage_info = self._get_usage_info(response)
            cost_info = (
                self._calculate_cost(model, response.usage)
                if hasattr(response, "usage")
                else {}
            )

            return {
                "success": True,
                "data": {"response_text": response.output_text},
                "usage": usage_info,
                "cost_info": cost_info,
                "model": model,
                "model_type": (
                    "thinking" if model in self.thinking_models else "non-thinking"
                ),
                "raw_response": response.output_text,
                "api_method": "chat.responses.create (fallback)",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback Responses API error: {str(e)}",
                "model": model,
                "api_method": "chat.responses.create (fallback failed)",
            }

    async def create_response_for_plugin(
        self,
        plugin_type: str,
        operation: str,
        model: str,
        instructions: str,
        user_input: str,
        use_structured: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a response with appropriate schema for a specific plugin operation.
        """
        if use_structured:
            # Get simplified schema for the operation
            schema = get_simplified_schema_for_operation(operation)
            return await self.create_structured_response(
                model, instructions, user_input, schema
            )
        else:
            return await self.create_fallback_response(model, instructions, user_input)

    def _get_usage_info(self, response) -> Dict[str, int]:
        """Extract usage information from response object."""
        if hasattr(response, "usage"):
            usage = response.usage
            return {
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "total_tokens": getattr(usage, "input_tokens", 0)
                + getattr(usage, "output_tokens", 0),
            }
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def _calculate_cost(self, model: str, usage) -> Dict[str, float]:
        """Calculate cost based on model pricing and usage."""
        if model not in self.model_pricing or not usage:
            return {}

        pricing = self.model_pricing[model]
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "cost_per_1k_input": round(pricing["input"] / 1000, 6),
            "cost_per_1k_output": round(pricing["output"] / 1000, 6),
        }
