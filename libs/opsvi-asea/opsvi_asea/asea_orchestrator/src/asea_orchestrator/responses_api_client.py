"""
OpenAI Responses API client with structured outputs for ASEA orchestrator.
Provides type-safe, schema-validated AI responses using Pydantic models.
"""

import json
from typing import Any, Dict, Optional, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from .schemas import get_schema_for_plugin

T = TypeVar("T", bound=BaseModel)


class ResponsesAPIClient:
    """
    Client for OpenAI Responses API with structured outputs.
    Handles model-specific parameters and provides robust error handling.
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

        # Model categorization for optimal API usage
        self.thinking_models = {"o3", "o4-mini", "o3-mini"}
        self.non_thinking_models = {"gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"}

        # Model-specific pricing for cost tracking
        self.model_pricing = {
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o4-mini": {"input": 1.10, "output": 4.40},
            "o3": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 3.00, "output": 12.00},
            # Legacy models (deprecated)
            # "gpt-4o": {"input": 2.50, "output": 10.00},
            # "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        }

    async def create_structured_response(
        self,
        model: str,
        instructions: str,
        user_input: str,
        response_schema: Type[T],
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured response using the Responses API with proper structured outputs.

        Args:
            model: OpenAI model name
            instructions: System instructions for the model
            user_input: User input/prompt
            response_schema: Pydantic model class for response structure
            max_tokens: Maximum tokens to generate (ignored - Responses API manages this)
            temperature: Temperature setting (ignored - Responses API manages this)

        Returns:
            Dictionary with parsed response data, usage info, and metadata
        """
        try:
            # Method 1: Try using responses.parse() with Pydantic model (preferred)
            try:
                response = await self.client.responses.parse(
                    model=model,
                    instructions=instructions,
                    input=user_input,
                    text_format=response_schema,
                )

                # Get the parsed response
                validated_response = response.output_parsed

                # Get usage information
                usage = response.usage if hasattr(response, "usage") else None
                cost_info = self._calculate_cost(model, usage) if usage else {}

                return {
                    "success": True,
                    "data": validated_response.model_dump(),
                    "usage": {
                        "input_tokens": usage.input_tokens if usage else 0,
                        "output_tokens": usage.output_tokens if usage else 0,
                        "total_tokens": (usage.input_tokens + usage.output_tokens)
                        if usage
                        else 0,
                    },
                    "cost_info": cost_info,
                    "model": model,
                    "model_type": "thinking"
                    if model in self.thinking_models
                    else "non-thinking",
                    "raw_response": response.output_text
                    if hasattr(response, "output_text")
                    else str(validated_response),
                }

            except Exception:
                # Method 2: Fallback to responses.create() with text_format
                json_schema = response_schema.model_json_schema()

                text_format = {
                    "format": {
                        "type": "json_schema",
                        "name": response_schema.__name__.lower(),
                        "strict": True,
                        "schema": json_schema,
                    }
                }

                # Enhance instructions to mention JSON requirement
                enhanced_instructions = f"""{instructions}

IMPORTANT: You must respond with valid JSON that matches the required schema. Do not include any text outside the JSON structure."""

                response = await self.client.responses.create(
                    model=model,
                    instructions=enhanced_instructions,
                    input=user_input,
                    text_format=text_format,
                )

                # Parse the JSON response
                try:
                    parsed_json = json.loads(response.output_text)
                    validated_response = response_schema.model_validate(parsed_json)
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Invalid JSON in response: {e}",
                        "raw_response": response.output_text,
                    }
                except ValidationError as e:
                    return {
                        "success": False,
                        "error": f"Response validation failed: {e}",
                        "raw_response": response.output_text,
                    }

                # Get usage information
                usage = response.usage if hasattr(response, "usage") else None
                cost_info = self._calculate_cost(model, usage) if usage else {}

                return {
                    "success": True,
                    "data": validated_response.model_dump(),
                    "usage": {
                        "input_tokens": usage.input_tokens if usage else 0,
                        "output_tokens": usage.output_tokens if usage else 0,
                        "total_tokens": (usage.input_tokens + usage.output_tokens)
                        if usage
                        else 0,
                    },
                    "cost_info": cost_info,
                    "model": model,
                    "model_type": "thinking"
                    if model in self.thinking_models
                    else "non-thinking",
                    "raw_response": response.output_text,
                }

        except Exception:
            # Final fallback - instruction-driven approach
            return await self.create_fallback_response(
                model=model,
                instructions=instructions,
                user_input=user_input,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    async def create_plugin_response(
        self,
        plugin_name: str,
        operation: str,
        model: str,
        instructions: str,
        user_input: str,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured response for a specific plugin operation.

        Args:
            plugin_name: Name of the plugin
            operation: Specific operation being performed
            model: OpenAI model name
            instructions: System instructions
            user_input: User input/prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature setting

        Returns:
            Dictionary with parsed response data and metadata
        """
        # Get appropriate schema for plugin operation
        response_schema = get_schema_for_plugin(plugin_name, operation)

        return await self.create_structured_response(
            model=model,
            instructions=instructions,
            user_input=user_input,
            response_schema=response_schema,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def create_fallback_response(
        self,
        model: str,
        instructions: str,
        user_input: str,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a response without structured outputs as fallback.

        Args:
            model: OpenAI model name
            instructions: System instructions
            user_input: User input/prompt
            max_tokens: Maximum tokens to generate (ignored - Responses API manages this)
            temperature: Temperature setting (ignored - Responses API manages this)

        Returns:
            Dictionary with response data
        """
        try:
            # Call Responses API without structured outputs using basic parameters
            response = await self.client.responses.create(
                model=model, instructions=instructions, input=user_input
            )

            # Get usage information
            usage = response.usage if hasattr(response, "usage") else None
            cost_info = self._calculate_cost(model, usage) if usage else {}

            return {
                "success": True,
                "data": {"response_text": response.output_text},
                "usage": {
                    "input_tokens": usage.input_tokens if usage else 0,
                    "output_tokens": usage.output_tokens if usage else 0,
                    "total_tokens": (usage.input_tokens + usage.output_tokens)
                    if usage
                    else 0,
                },
                "cost_info": cost_info,
                "model": model,
                "model_type": "thinking"
                if model in self.thinking_models
                else "non-thinking",
                "raw_response": response.output_text,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback API call failed: {str(e)}",
                "error_type": "api_error",
                "model": model,
            }

    def _calculate_cost(self, model: str, usage: Any) -> Dict[str, Any]:
        """Calculate cost based on token usage."""
        if not usage or model not in self.model_pricing:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "note": f"Pricing not available for model {model}",
            }

        pricing = self.model_pricing[model]
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "cost_per_1k_input": round(pricing["input"] / 1000, 6),
            "cost_per_1k_output": round(pricing["output"] / 1000, 6),
        }

    def get_optimal_model_for_task(
        self,
        task_type: str,
        complexity: str = "medium",
        budget_limit: Optional[float] = None,
    ) -> str:
        """
        Select optimal model based on task type, complexity, and budget.

        Args:
            task_type: Type of task (reasoning, analysis, simple, creative, etc.)
            complexity: Complexity level (low, medium, high)
            budget_limit: Maximum cost per request in USD

        Returns:
            Recommended model name
        """
        # Define model tiers by capability and cost
        if task_type in ["reasoning", "analysis", "optimization", "complex_decision"]:
            if complexity == "high":
                candidates = ["o4-mini", "gpt-4.1", "o3-mini"]
            elif complexity == "medium":
                candidates = ["gpt-4.1-mini", "o4-mini", "gpt-4.1"]
            else:
                candidates = ["gpt-4.1-nano", "gpt-4.1-mini"]
        elif task_type in [
            "simple_classification",
            "formatting",
            "extraction",
            "basic_analysis",
        ]:
            candidates = ["gpt-4.1-nano", "gpt-4.1-mini"]
        elif task_type in ["creative", "planning", "strategy", "complex_generation"]:
            if complexity == "high":
                candidates = ["gpt-4.1", "o4-mini", "o3-mini"]
            else:
                candidates = ["gpt-4.1-mini", "gpt-4.1"]
        else:
            candidates = ["gpt-4.1-mini", "gpt-4.1-nano"]

        # Filter by budget if specified
        if budget_limit:
            affordable_models = []
            for model in candidates:
                if model in self.model_pricing:
                    # Estimate cost for typical request (500 input + 1000 output tokens)
                    pricing = self.model_pricing[model]
                    estimated_cost = (500 / 1_000_000) * pricing["input"] + (
                        1000 / 1_000_000
                    ) * pricing["output"]
                    if estimated_cost <= budget_limit:
                        affordable_models.append(model)

            if affordable_models:
                candidates = affordable_models

        # Return the first (most preferred) candidate
        return candidates[0] if candidates else "gpt-4.1-nano"

    async def close(self):
        """Close the client connection."""
        if self.client:
            await self.client.close()


# Helper function for easy integration
async def create_structured_ai_response(
    api_key: str,
    plugin_name: str,
    operation: str,
    model: str,
    instructions: str,
    user_input: str,
    max_tokens: int = 2000,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convenience function to create a structured AI response.

    Args:
        api_key: OpenAI API key
        plugin_name: Name of the plugin
        operation: Specific operation
        model: OpenAI model name
        instructions: System instructions
        user_input: User input/prompt
        max_tokens: Maximum tokens to generate
        temperature: Temperature setting

    Returns:
        Dictionary with parsed response data and metadata
    """
    client = ResponsesAPIClient(api_key)
    try:
        return await client.create_plugin_response(
            plugin_name=plugin_name,
            operation=operation,
            model=model,
            instructions=instructions,
            user_input=user_input,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    finally:
        await client.close()
