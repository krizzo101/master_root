#!/usr/bin/env python3
"""
Fixed Autonomous OpenAI Client with Modern Patterns and Comprehensive Logging

This client follows the latest OpenAI Python library patterns (1.88+) and eliminates
httpx dependency issues. It includes comprehensive logging for debugging and monitoring.

Key improvements:
- Modern AsyncOpenAI initialization (no httpx parameters)
- Proper error handling and logging
- Cost tracking and budget management  
- Structured outputs with fallback approaches
- Performance monitoring and debug logging
- Following established codebase patterns
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import BaseModel

from comprehensive_logging_config import get_logger


@dataclass
class TokenUsage:
    """Token usage information."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class CostInfo:
    """Cost calculation information."""

    input_cost: float
    output_cost: float
    total_cost: float
    model: str


class AutonomousOpenAIClient:
    """
    Modern OpenAI client with comprehensive logging and error handling.

    Features:
    - Latest OpenAI library patterns (1.88+)
    - Comprehensive debug logging
    - Cost tracking and budget management
    - Structured outputs with fallback
    - Performance monitoring
    - Error context and recovery
    """

    def __init__(self, api_key: str, component_name: str = "autonomous_openai_client"):
        """
        Initialize the OpenAI client with modern patterns.

        Args:
            api_key: OpenAI API key
            component_name: Component name for logging
        """
        self.api_key = api_key
        self.component_name = component_name

        # Initialize comprehensive logging
        self.logger = get_logger(component_name, log_level="DEBUG")
        self.log = self.logger.get_logger()

        # Initialize OpenAI client with modern pattern (no httpx parameters)
        try:
            self.client = AsyncOpenAI(api_key=api_key)
            self.log.info("OpenAI client initialized successfully with modern pattern")
        except Exception as e:
            self.logger.log_error_with_context(
                e,
                {
                    "initialization_method": "modern_pattern",
                    "api_key_length": len(api_key),
                },
            )
            raise

        # Model categorization for optimal usage
        self.thinking_models = {"o1", "o1-mini", "o1-preview", "o3", "o3-mini"}
        self.non_thinking_models = {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
        }

        # Model-specific pricing for cost tracking (per 1M tokens)
        self.model_pricing = {
            # Current models
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            # Future models (estimated)
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o1": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            "o1-preview": {"input": 15.00, "output": 60.00},
            "o3": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 3.00, "output": 12.00},
        }

        # Budget tracking
        self.budget_limit = None
        self.total_cost = 0.0
        self.request_count = 0

        self.log.info(
            f"Autonomous OpenAI Client initialized with {len(self.model_pricing)} models"
        )

    async def create_completion(
        self,
        model: str,
        messages: List[Dict[str, str]] = None,
        instructions: str = None,
        user_input: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.1,
        response_format: Optional[Dict] = None,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Create completion using modern OpenAI patterns with comprehensive logging.

        Args:
            model: Model name
            messages: Chat messages (for chat completions)
            instructions: System instructions (for Responses API)
            user_input: User input (for Responses API)
            max_tokens: Maximum tokens to generate
            temperature: Temperature setting
            response_format: Response format specification
            timeout: Request timeout

        Returns:
            Dictionary with completion data, usage, and cost info
        """
        correlation_id = self.logger.start_operation(
            "create_completion",
            {
                "model": model,
                "has_messages": bool(messages),
                "has_instructions": bool(instructions),
                "has_user_input": bool(user_input),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "has_response_format": bool(response_format),
            },
        )

        try:
            # Determine API approach based on parameters
            if messages:
                result = await self._create_chat_completion(
                    model,
                    messages,
                    max_tokens,
                    temperature,
                    response_format,
                    timeout,
                    correlation_id,
                )
            elif instructions and user_input:
                result = await self._create_responses_completion(
                    model,
                    instructions,
                    user_input,
                    max_tokens,
                    temperature,
                    response_format,
                    timeout,
                    correlation_id,
                )
            else:
                raise ValueError(
                    "Must provide either 'messages' or both 'instructions' and 'user_input'"
                )

            # Track costs and usage
            self._track_usage(result)

            self.logger.end_operation(
                correlation_id,
                success=True,
                result_context={
                    "model_used": result.get("model"),
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "cost": result.get("cost_info", {}).get("total_cost", 0.0),
                },
            )

            return result

        except Exception as e:
            self.logger.log_error_with_context(
                e,
                {
                    "model": model,
                    "api_approach": "chat" if messages else "responses",
                    "request_count": self.request_count,
                },
                correlation_id,
            )
            self.logger.end_operation(correlation_id, success=False)
            raise

    async def _create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        response_format: Optional[Dict],
        timeout: float,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Create completion using Chat Completions API."""
        start_time = datetime.now()

        try:
            # Prepare parameters based on model type
            params = {"model": model, "messages": messages, "timeout": timeout}

            # Add model-specific parameters
            if model in self.thinking_models:
                # Thinking models: use max_completion_tokens, no custom temperature
                if max_tokens != 2000:  # Only add if not default
                    params["max_completion_tokens"] = max_tokens
            else:
                # Non-thinking models: use max_tokens and temperature
                params["max_tokens"] = max_tokens
                params["temperature"] = temperature

            # Add response format if specified
            if response_format:
                params["response_format"] = response_format

            self.log.debug(
                f"Chat completion parameters: {self._mask_sensitive_params(params)}"
            )

            # Make API call
            response = await self.client.chat.completions.create(**params)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Extract response data
            content = response.choices[0].message.content
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

            cost_info = self._calculate_cost(model, usage)

            # Log API call
            self.logger.log_api_call(
                "OpenAI_Chat",
                f"/chat/completions",
                "POST",
                request_data={"model": model, "message_count": len(messages)},
                response_data={"content_length": len(content) if content else 0},
                success=True,
                duration_ms=duration_ms,
            )

            return {
                "success": True,
                "content": content,
                "model": model,
                "usage": usage.__dict__,
                "cost_info": cost_info.__dict__,
                "api_type": "chat_completions",
                "duration_ms": duration_ms,
                "raw_response": response,
            }

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.log_api_call(
                "OpenAI_Chat",
                "/chat/completions",
                "POST",
                request_data={"model": model, "message_count": len(messages)},
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
            raise

    async def _create_responses_completion(
        self,
        model: str,
        instructions: str,
        user_input: str,
        max_tokens: int,
        temperature: float,
        response_format: Optional[Dict],
        timeout: float,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Create completion using Responses API (modern approach)."""
        start_time = datetime.now()

        try:
            # Prepare parameters
            params = {"model": model, "instructions": instructions, "input": user_input}

            # Add response format if specified
            if response_format:
                params["response_format"] = response_format

            self.log.debug(
                f"Responses API parameters: {self._mask_sensitive_params(params)}"
            )

            # Make API call using modern Responses API
            response = await self.client.responses.create(**params)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Extract response data
            content = response.output_text
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens
                if hasattr(response.usage, "input_tokens")
                else response.usage.prompt_tokens,
                output_tokens=response.usage.output_tokens
                if hasattr(response.usage, "output_tokens")
                else response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

            cost_info = self._calculate_cost(model, usage)

            # Log API call
            self.logger.log_api_call(
                "OpenAI_Responses",
                "/responses",
                "POST",
                request_data={
                    "model": model,
                    "instructions_length": len(instructions),
                    "input_length": len(user_input),
                },
                response_data={"content_length": len(content) if content else 0},
                success=True,
                duration_ms=duration_ms,
            )

            return {
                "success": True,
                "content": content,
                "model": model,
                "usage": usage.__dict__,
                "cost_info": cost_info.__dict__,
                "api_type": "responses",
                "duration_ms": duration_ms,
                "raw_response": response,
            }

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.log_api_call(
                "OpenAI_Responses",
                "/responses",
                "POST",
                request_data={
                    "model": model,
                    "instructions_length": len(instructions),
                    "input_length": len(user_input),
                },
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
            raise

    async def create_structured_completion(
        self,
        model: str,
        instructions: str,
        user_input: str,
        response_schema: Type[BaseModel],
        max_tokens: int = 2000,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Create structured completion with Pydantic schema validation.

        Args:
            model: Model name
            instructions: System instructions
            user_input: User input
            response_schema: Pydantic model for response structure
            max_tokens: Maximum tokens
            temperature: Temperature setting

        Returns:
            Dictionary with validated structured response
        """
        correlation_id = self.logger.start_operation(
            "create_structured_completion",
            {
                "model": model,
                "schema_name": response_schema.__name__,
                "max_tokens": max_tokens,
            },
        )

        try:
            # Create JSON schema from Pydantic model
            json_schema = response_schema.model_json_schema()

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

IMPORTANT: You must respond with valid JSON that exactly matches the required schema. 
Do not include any text outside the JSON structure."""

            # Create completion with structured output
            result = await self.create_completion(
                model=model,
                instructions=enhanced_instructions,
                user_input=user_input,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
            )

            if result["success"]:
                # Parse and validate JSON response
                try:
                    parsed_json = json.loads(result["content"])
                    validated_response = response_schema.model_validate(parsed_json)

                    result["structured_data"] = validated_response.model_dump()
                    result["validation_success"] = True

                    self.log.info(
                        f"Structured response validated successfully for schema {response_schema.__name__}"
                    )

                except json.JSONDecodeError as e:
                    self.log.error(f"JSON parsing failed: {e}")
                    result["validation_success"] = False
                    result["validation_error"] = f"JSON parsing failed: {e}"

                except Exception as e:
                    self.log.error(f"Schema validation failed: {e}")
                    result["validation_success"] = False
                    result["validation_error"] = f"Schema validation failed: {e}"

            self.logger.end_operation(
                correlation_id,
                success=result["success"] and result.get("validation_success", False),
                result_context={
                    "validation_success": result.get("validation_success", False),
                    "schema_name": response_schema.__name__,
                },
            )

            return result

        except Exception as e:
            self.logger.log_error_with_context(
                e,
                {"model": model, "schema_name": response_schema.__name__},
                correlation_id,
            )
            self.logger.end_operation(correlation_id, success=False)
            raise

    def _calculate_cost(self, model: str, usage: TokenUsage) -> CostInfo:
        """Calculate cost based on model pricing and token usage."""
        if model not in self.model_pricing:
            self.log.warning(f"Pricing not available for model {model}")
            return CostInfo(0.0, 0.0, 0.0, model)

        pricing = self.model_pricing[model]
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return CostInfo(
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(total_cost, 6),
            model=model,
        )

    def _track_usage(self, result: Dict[str, Any]):
        """Track usage statistics and costs."""
        self.request_count += 1

        if "cost_info" in result:
            cost = result["cost_info"]["total_cost"]
            self.total_cost += cost

            self.log.info(
                f"Request #{self.request_count}: ${cost:.6f} | Total: ${self.total_cost:.6f}"
            )

            # Check budget limits
            if self.budget_limit and self.total_cost > self.budget_limit:
                self.log.warning(
                    f"Budget limit exceeded: ${self.total_cost:.6f} > ${self.budget_limit:.6f}"
                )

    def _mask_sensitive_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive parameters for logging."""
        masked = params.copy()

        # Mask API key if present
        if "api_key" in masked:
            key = masked["api_key"]
            if len(key) > 8:
                masked["api_key"] = key[:4] + "****" + key[-4:]
            else:
                masked["api_key"] = "****"

        # Truncate long content for logging
        for key in ["instructions", "input", "messages"]:
            if (
                key in masked
                and isinstance(masked[key], str)
                and len(masked[key]) > 200
            ):
                masked[key] = masked[key][:200] + "..."

        return masked

    def set_budget_limit(self, limit: float):
        """Set budget limit for cost tracking."""
        self.budget_limit = limit
        self.log.info(f"Budget limit set to ${limit:.2f}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "request_count": self.request_count,
            "total_cost": self.total_cost,
            "budget_limit": self.budget_limit,
            "budget_remaining": self.budget_limit - self.total_cost
            if self.budget_limit
            else None,
            "average_cost_per_request": self.total_cost / self.request_count
            if self.request_count > 0
            else 0,
        }

    def get_optimal_model(
        self,
        task_type: str,
        complexity: str = "medium",
        budget_per_request: Optional[float] = None,
    ) -> str:
        """
        Select optimal model based on task requirements.

        Args:
            task_type: Type of task (reasoning, analysis, simple, creative)
            complexity: Complexity level (low, medium, high)
            budget_per_request: Maximum cost per request

        Returns:
            Recommended model name
        """
        # Define model tiers by capability and cost
        if task_type in ["reasoning", "analysis", "optimization", "complex_decision"]:
            if complexity == "high":
                candidates = ["o1", "gpt-4o", "gpt-4-turbo"]
            elif complexity == "medium":
                candidates = ["gpt-4o", "gpt-4o-mini"]
            else:
                candidates = ["gpt-4o-mini", "gpt-3.5-turbo"]
        elif task_type in ["simple_classification", "formatting", "extraction"]:
            candidates = ["gpt-4o-mini", "gpt-3.5-turbo"]
        elif task_type in ["creative", "planning", "strategy"]:
            if complexity == "high":
                candidates = ["gpt-4o", "gpt-4-turbo"]
            else:
                candidates = ["gpt-4o", "gpt-4o-mini"]
        else:
            candidates = ["gpt-4o-mini", "gpt-4o"]

        # Filter by budget if specified
        if budget_per_request:
            affordable_models = []
            for model in candidates:
                if model in self.model_pricing:
                    # Estimate cost for typical request (500 input + 1000 output tokens)
                    pricing = self.model_pricing[model]
                    estimated_cost = (500 / 1_000_000) * pricing["input"] + (
                        1000 / 1_000_000
                    ) * pricing["output"]
                    if estimated_cost <= budget_per_request:
                        affordable_models.append(model)

            if affordable_models:
                candidates = affordable_models

        # Return the first (most preferred) candidate
        selected = candidates[0] if candidates else "gpt-4o-mini"

        self.log.info(
            f"Selected model {selected} for task_type={task_type}, complexity={complexity}"
        )
        return selected

    async def close(self):
        """Close the client and clean up resources."""
        if self.client:
            await self.client.close()
            self.log.info("OpenAI client closed successfully")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory function for easy instantiation
def create_openai_client(
    api_key: str, component_name: str = "autonomous_openai_client"
) -> AutonomousOpenAIClient:
    """
    Factory function to create OpenAI client with proper configuration.

    Args:
        api_key: OpenAI API key
        component_name: Component name for logging

    Returns:
        Configured OpenAI client instance
    """
    return AutonomousOpenAIClient(api_key, component_name)


# Example usage and testing
async def test_client():
    """Test the OpenAI client with comprehensive logging."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return

    async with create_openai_client(api_key, "test_client") as client:
        # Set budget limit
        client.set_budget_limit(1.0)

        # Test chat completion
        try:
            result = await client.create_completion(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
            )
            print(f"✅ Chat completion: {result['content'][:100]}...")

        except Exception as e:
            print(f"❌ Chat completion failed: {e}")

        # Test Responses API
        try:
            result = await client.create_completion(
                model="gpt-4o-mini",
                instructions="You are a math tutor.",
                user_input="Explain what 5*5 equals.",
            )
            print(f"✅ Responses API: {result['content'][:100]}...")

        except Exception as e:
            print(f"❌ Responses API failed: {e}")

        # Test structured output
        from pydantic import BaseModel

        class MathAnswer(BaseModel):
            question: str
            answer: int
            explanation: str

        try:
            result = await client.create_structured_completion(
                model="gpt-4o-mini",
                instructions="Solve math problems and provide structured answers.",
                user_input="What is 7 * 8?",
                response_schema=MathAnswer,
            )

            if result.get("validation_success"):
                print(f"✅ Structured output: {result['structured_data']}")
            else:
                print(
                    f"❌ Structured output validation failed: {result.get('validation_error')}"
                )

        except Exception as e:
            print(f"❌ Structured output failed: {e}")

        # Print usage stats
        stats = client.get_usage_stats()
        print(f"📊 Usage stats: {stats}")


if __name__ == "__main__":
    asyncio.run(test_client())
