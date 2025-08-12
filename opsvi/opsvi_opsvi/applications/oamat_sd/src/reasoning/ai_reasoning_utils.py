"""
AI Reasoning Utilities Module

Handles AI reasoning infrastructure, prompt creation, response parsing, and logging.
Extracted from o3_master_agent.py for better modularity.
"""

import json
import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class AIReasoningUtils:
    """Handles AI reasoning infrastructure and utilities"""

    def __init__(self, model_config: dict[str, Any] | None = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.model_config = model_config or self._default_model_config()

        # Initialize O3 model (NO FALLBACKS - fail if unavailable)
        try:
            # O3 models don't support temperature parameter - use minimal config
            model_kwargs = {"model": self.model_config["model"]}

            # Only add temperature for non-O3 models
            if not self.model_config["model"].startswith("o3"):
                model_kwargs["temperature"] = self.model_config["temperature"]

            self.master_model = ChatOpenAI(**model_kwargs)
            self.logger.info(f"✅ O3 model initialized: {self.model_config['model']}")
        except Exception as e:
            self.logger.error(f"❌ O3 model initialization failed: {e}")
            raise RuntimeError(
                f"O3 model initialization failed: {e}. System cannot operate without O3."
            )

    def _default_model_config(self) -> dict[str, Any]:
        """Default configuration for O3 model integration."""
        return {
            "model": "o3-mini",  # Standardized reasoning model
            "temperature": 0.1,
            "enable_chain_of_thought": True,
            "enable_self_reflection": True,
        }

    def _get_approved_ai_model(self, model_type: str) -> ChatOpenAI:
        """Get approved AI model for specific use case using centralized configuration"""
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        config_manager = ConfigManager()
        model_spec = config_manager.get_model_config(model_type)

        # Create model with centralized configuration
        model_kwargs = {
            "model": model_spec.model_name,
            "max_tokens": model_spec.max_tokens,
        }

        # Only add temperature if the model supports it
        if model_spec.supports_temperature and model_spec.temperature is not None:
            model_kwargs["temperature"] = model_spec.temperature

        return ChatOpenAI(**model_kwargs)

    async def call_ai_reasoning(
        self, prompt: str, context: str, model_type: str = "reasoning"
    ) -> str:
        """Call AI reasoning with proper logging and error handling"""
        self.logger.info(f"🤖 {context}: Starting AI reasoning")

        try:
            # Get appropriate model
            ai_model = self._get_approved_ai_model(model_type)

            # API Logging: Prepare request data
            api_start_time = time.time()
            request_messages = [
                SystemMessage(
                    content="You are an expert system architect specializing in dynamic multi-agent workflow design."
                ),
                HumanMessage(content=prompt),
            ]

            # Log API call start
            try:
                from src.applications.oamat_sd.src.sd_logging.logger_factory import (
                    get_logger_factory,
                )

                logger_factory = get_logger_factory()
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": getattr(ai_model, "model_name", model_type),
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                        "temperature": getattr(ai_model, "temperature", 0.1),
                    },
                    status_code=None,  # Will update after response
                    duration_ms=None,  # Will update after response
                )
            except Exception as log_error:
                self.logger.warning(f"API logging failed: {log_error}")

            response = await ai_model.ainvoke(request_messages)

            # API Logging: Log successful response
            api_duration = (time.time() - api_start_time) * 1000
            try:
                logger_factory.log_api_call(
                    method="POST",
                    url="https://api.openai.com/v1/chat/completions",
                    request_data={
                        "model": getattr(ai_model, "model_name", model_type),
                        "messages": [
                            {"role": msg.type, "content": str(msg.content)[:500]}
                            for msg in request_messages
                        ],
                    },
                    response_data={
                        "content": str(response.content)[:1000],
                        "finish_reason": "stop",
                        "usage": {
                            "completion_tokens": len(str(response.content).split())
                        },
                    },
                    status_code=200,
                    duration_ms=api_duration,
                )
            except Exception as log_error:
                self.logger.warning(f"API response logging failed: {log_error}")

            self.logger.info(f"✅ {context} AI reasoning completed successfully")
            return response.content

        except Exception as e:
            self.logger.error(f"❌ {context} AI reasoning failed: {e}")
            # Rule compliance: NO FALLBACKS - fail cleanly
            raise RuntimeError(
                f"{context} failed: {e}. System cannot proceed without AI analysis."
            )

    def parse_json_from_ai_response(
        self, response_content: str, expected_schema: str
    ) -> dict[str, Any]:
        """Parse JSON from AI response with validation (shared utility)"""
        try:
            # Look for JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                self.logger.info(
                    f"✅ Successfully parsed {expected_schema} from AI response"
                )
                return parsed_data
            else:
                raise ValueError(f"No JSON found in AI response for {expected_schema}")

        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse {expected_schema} JSON: {e}")
            # Rule compliance: NO FALLBACKS - fail cleanly
            raise RuntimeError(
                f"AI response parsing failed for {expected_schema}: {e}. Cannot proceed without valid AI output."
            )

    def validate_ai_output_schema(
        self, data: dict[str, Any], required_fields: list[str], schema_name: str
    ) -> bool:
        """Validate AI output conforms to expected schema"""
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            self.logger.error(
                f"❌ {schema_name} missing required fields: {missing_fields}"
            )
            raise ValueError(
                f"{schema_name} AI output missing fields: {missing_fields}"
            )

        self.logger.info(f"✅ {schema_name} schema validation passed")
        return True

    def create_structured_prompt(
        self,
        system_role: str,
        task_description: str,
        context_data: dict[str, Any],
        output_format: str,
        examples: list[str] | None = None,
    ) -> str:
        """Create a structured prompt for AI reasoning"""

        # Build context section
        context_section = ""
        if context_data:
            context_section = "\n## CONTEXT\n"
            for key, value in context_data.items():
                context_section += f"**{key.title()}**: {value}\n"

        # Build examples section
        examples_section = ""
        if examples:
            examples_section = "\n## EXAMPLES\n"
            for i, example in enumerate(examples, 1):
                examples_section += f"**Example {i}**: {example}\n"

        prompt = f"""You are {system_role}.

## TASK
{task_description}
{context_section}
{examples_section}
## OUTPUT FORMAT
{output_format}

Please analyze the above and provide your response in the specified format."""

        return prompt

    def create_analysis_prompt(
        self,
        analysis_type: str,
        data_to_analyze: dict[str, Any],
        specific_requirements: list[str],
        output_schema: str,
    ) -> str:
        """Create a prompt specifically for analysis tasks"""

        requirements_text = "\n".join(f"- {req}" for req in specific_requirements)

        prompt = f"""You are an expert analyst specializing in {analysis_type}.

## ANALYSIS REQUEST
Perform a comprehensive {analysis_type} analysis of the provided data.

## DATA TO ANALYZE
{json.dumps(data_to_analyze, indent=2)}

## SPECIFIC REQUIREMENTS
{requirements_text}

## OUTPUT SCHEMA
{output_schema}

Provide a thorough analysis following the specified schema."""

        return prompt

    def create_generation_prompt(
        self,
        generation_type: str,
        input_data: dict[str, Any],
        constraints: list[str],
        quality_criteria: list[str],
        output_format: str,
    ) -> str:
        """Create a prompt for generation tasks"""

        constraints_text = "\n".join(f"- {constraint}" for constraint in constraints)
        criteria_text = "\n".join(f"- {criterion}" for criterion in quality_criteria)

        prompt = f"""You are an expert {generation_type} generator.

## GENERATION REQUEST
Generate high-quality {generation_type} based on the provided input data.

## INPUT DATA
{json.dumps(input_data, indent=2)}

## CONSTRAINTS
{constraints_text}

## QUALITY CRITERIA
{criteria_text}

## OUTPUT FORMAT
{output_format}

Generate the requested output following all constraints and quality criteria."""

        return prompt

    def extract_json_from_response(
        self, response: str, fallback: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Extract JSON from AI response with optional fallback"""
        try:
            return self.parse_json_from_ai_response(response, "structured_response")
        except Exception as e:
            if fallback is not None:
                self.logger.warning(f"JSON extraction failed, using fallback: {e}")
                return fallback
            else:
                raise

    def log_reasoning_step(
        self,
        step_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        confidence: float,
        duration_ms: float,
    ):
        """Log a reasoning step for debugging and analysis"""
        self.logger.info(f"🧠 Reasoning Step: {step_name}")
        self.logger.debug(f"Input size: {len(str(input_data))} chars")
        self.logger.debug(f"Output size: {len(str(output_data))} chars")
        self.logger.debug(f"Confidence: {confidence:.2f}")
        self.logger.debug(f"Duration: {duration_ms:.1f}ms")

    def create_error_recovery_prompt(
        self,
        failed_task: str,
        error_details: str,
        context: dict[str, Any],
        alternative_approach: str,
    ) -> str:
        """Create a prompt for error recovery scenarios"""

        prompt = f"""You are an expert problem solver specializing in error recovery.

## FAILED TASK
{failed_task}

## ERROR DETAILS
{error_details}

## CONTEXT
{json.dumps(context, indent=2)}

## ALTERNATIVE APPROACH
{alternative_approach}

## RECOVERY REQUEST
Analyze the failure and provide a corrected approach that addresses the error while maintaining the original objective.

Provide your solution in a clear, structured format with:
1. Root cause analysis
2. Corrected approach
3. Validation steps
4. Risk mitigation measures"""

        return prompt
