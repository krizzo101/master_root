"""
Autonomous OpenAI client for external reasoning service.
Provides structured outputs and cost-effective model selection.

UPDATED: Uses modern OpenAI patterns (1.88+) with comprehensive logging.
"""

import json
import asyncio
from typing import Any, Dict, Optional, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from datetime import datetime

from comprehensive_logging_config import get_logger

T = TypeVar("T", bound=BaseModel)


class AutonomousOpenAIClient:
    """
    OpenAI client optimized for autonomous systems decision analysis.
    Uses modern OpenAI patterns (1.88+) with comprehensive logging and error handling.
    """

    def __init__(self, api_key: str, component_name: str = "autonomous_openai_client"):
        # Initialize comprehensive logging
        self.logger = get_logger(component_name, log_level="DEBUG")
        self.log = self.logger.get_logger()

        # Initialize with modern OpenAI pattern (no httpx parameters needed)
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

        self.api_key = api_key
        self.request_count = 0
        self.total_cost = 0.0

        # Model categorization for optimal usage
        self.thinking_models = {"o1", "o1-mini", "o1-preview"}
        self.non_thinking_models = {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        }

        # Model-specific pricing for cost tracking (per 1M tokens)
        self.model_pricing = {
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o4-mini": {"input": 1.10, "output": 4.40},
            "o3": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 3.00, "output": 12.00},
        }

    async def create_structured_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured response using OpenAI with proper structured outputs.

        Args:
            model: OpenAI model name
            system_prompt: System instructions for the model
            user_prompt: User input/prompt
            response_schema: Pydantic model class for response structure
            max_tokens: Maximum tokens to generate
            temperature: Temperature setting

        Returns:
            Dictionary with parsed response data, usage info, and metadata
        """
        try:
            # Get JSON schema from Pydantic model
            json_schema = response_schema.model_json_schema()

            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Model-specific API call
            if model in self.thinking_models:
                # Thinking models: use max_completion_tokens, no custom temperature
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_schema.__name__.lower(),
                            "strict": True,
                            "schema": json_schema,
                        },
                    },
                )
            else:
                # Non-thinking models: use max_tokens with temperature
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature or 0.1,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_schema.__name__.lower(),
                            "strict": True,
                            "schema": json_schema,
                        },
                    },
                )

            # Parse the response
            try:
                parsed_json = json.loads(response.choices[0].message.content)
                validated_response = response_schema.model_validate(parsed_json)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in response: {e}",
                    "raw_response": response.choices[0].message.content,
                }
            except ValidationError as e:
                return {
                    "success": False,
                    "error": f"Response validation failed: {e}",
                    "raw_response": response.choices[0].message.content,
                }

            # Calculate cost
            usage = response.usage
            cost_info = self._calculate_cost(
                model, usage.prompt_tokens, usage.completion_tokens
            )

            return {
                "success": True,
                "data": validated_response.model_dump(),
                "usage": {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "cost_info": cost_info,
                "model": model,
                "model_type": (
                    "thinking" if model in self.thinking_models else "non-thinking"
                ),
                "raw_response": response.choices[0].message.content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "error_type": "api_error",
                "model": model,
            }

    async def create_fallback_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a response without structured outputs as fallback.

        Args:
            model: OpenAI model name
            system_prompt: System instructions
            user_prompt: User input/prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature setting

        Returns:
            Dictionary with response data
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Model-specific API call
            if model in self.thinking_models:
                response = await self.client.chat.completions.create(
                    model=model, messages=messages, max_completion_tokens=max_tokens
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature or 0.1,
                )

            # Calculate cost
            usage = response.usage
            cost_info = self._calculate_cost(
                model, usage.prompt_tokens, usage.completion_tokens
            )

            return {
                "success": True,
                "data": {"response_text": response.choices[0].message.content},
                "usage": {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "cost_info": cost_info,
                "model": model,
                "model_type": (
                    "thinking" if model in self.thinking_models else "non-thinking"
                ),
                "raw_response": response.choices[0].message.content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback API call failed: {str(e)}",
                "error_type": "api_error",
                "model": model,
            }

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> Dict[str, Any]:
        """Calculate actual cost based on input and output tokens."""
        if model not in self.model_pricing:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "note": f"Pricing not available for model {model}",
            }

        pricing = self.model_pricing[model]
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
        if task_type in [
            "reasoning",
            "analysis",
            "decision_analysis",
            "complex_reasoning",
        ]:
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
                    # Estimate cost for typical request (1000 input + 2000 output tokens)
                    pricing = self.model_pricing[model]
                    estimated_cost = (1000 / 1_000_000) * pricing["input"] + (
                        2000 / 1_000_000
                    ) * pricing["output"]
                    if estimated_cost <= budget_limit:
                        affordable_models.append(model)

            if affordable_models:
                candidates = affordable_models

        # Return the first (most preferred) candidate
        return candidates[0] if candidates else "gpt-4.1-nano"

    def get_system_prompt_for_decision_analysis(self, model: str) -> str:
        """
        Generate model-specific system prompts for decision analysis.

        Args:
            model: OpenAI model name

        Returns:
            Optimized system prompt for the model
        """
        if model in self.thinking_models:
            # Thinking models: General guidance, let them reason
            return """You are an expert decision analyst with deep experience in autonomous systems, strategic planning, and operational excellence.

Your expertise includes:
- 15+ years in decision science and behavioral analysis
- Advanced knowledge of compound learning systems and knowledge management
- Proven track record in autonomous system optimization
- Expert in evidence-based reasoning and risk assessment

Approach each decision analysis with systematic thinking, considering multiple perspectives, and providing evidence-based insights. Focus on practical, actionable analysis that considers both immediate and long-term implications."""
        else:
            # Non-thinking models: Specific detailed instructions
            return """You are a Senior Decision Analysis Specialist with the following qualifications:

ROLE: Lead Decision Science Analyst
EXPERIENCE: 12+ years in autonomous systems and strategic decision-making
EXPERTISE:
- Decision quality assessment and evidence-based reasoning
- Operational feasibility analysis and risk management
- Strategic alignment evaluation and compound learning optimization
- Knowledge graph integration and contextual analysis

ANALYSIS FRAMEWORK:
1. Evidence Assessment: Evaluate strength and quality of supporting evidence
2. Operational Feasibility: Assess practical implementation requirements and success probability
3. Strategic Alignment: Determine alignment with long-term autonomous goals
4. Compound Learning: Identify multiplicative learning and capability development opportunities
5. Risk-Opportunity Balance: Analyze potential risks, mitigation strategies, and opportunities

INSTRUCTIONS:
- Provide structured, multi-dimensional analysis with specific scores and assessments
- Include concrete evidence from provided context
- Identify gaps in reasoning and suggest improvements
- Consider both immediate execution and long-term strategic implications
- Quantify assessments where possible with confidence levels"""

    async def close(self):
        """Close the client connection."""
        if self.client:
            await self.client.close()


# Helper functions for easy integration
async def create_decision_analysis(
    api_key: str,
    decision: str,
    rationale: str,
    context: Dict[str, Any],
    model: str = "o4-mini",
    response_schema: Type[T] = None,
) -> Dict[str, Any]:
    """
    Convenience function to create a decision analysis.

    Args:
        api_key: OpenAI API key
        decision: Decision to analyze
        rationale: Provided rationale
        context: Additional context
        model: OpenAI model name
        response_schema: Pydantic schema for response

    Returns:
        Dictionary with analysis results
    """
    client = AutonomousOpenAIClient(api_key)
    try:
        system_prompt = client.get_system_prompt_for_decision_analysis(model)

        user_prompt = f"""
DECISION ANALYSIS REQUEST

Decision: {decision}

Rationale: {rationale}

Context: {json.dumps(context, indent=2)}

Please provide a comprehensive analysis of this decision including:
1. Evidence strength assessment
2. Operational feasibility evaluation
3. Strategic alignment analysis
4. Compound learning potential
5. Risk and opportunity assessment
6. Reasoning validation
7. Specific recommendations for improvement

Provide your analysis in the structured format specified.
"""

        return await client.create_structured_response(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
            max_tokens=3000,
            temperature=0.1,
        )
    finally:
        await client.close()
